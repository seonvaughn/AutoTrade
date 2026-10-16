"""Typed configuration loaded from config.yaml (secrets come from env vars)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

VALID_TRIGGERS = {"vwap_cross", "ema50_cross", "orb"}
VALID_MODES = {"backtest", "replay", "paper", "live"}
LIVE_CONFIRM_ENV = "SCALPCITY_LIVE_CONFIRM"
LIVE_CONFIRM_VALUE = "I_UNDERSTAND_THIS_TRADES_REAL_MONEY"


@dataclass
class ExitRules:
    take_profit_pct: float = 12.0     # close at +12% on the option premium
    stop_loss_pct: float = 10.0       # close at -10%
    trail_activate_pct: float = 4.0   # once up 4%, start locking profit ...
    trail_lock_ratio: float = 0.6     # ... keep at least 60% of the best gain seen
    max_hold_minutes: float = 20.0
    exit_on_reversal: bool = True     # opposite signal closes the trade


@dataclass
class Sizing:
    mode: str = "budget"              # fixed | budget | risk
    contracts: int = 5                # mode=fixed
    budget: float = 2000.0            # mode=budget: max premium $ per trade
    risk: float = 200.0               # mode=risk: $ lost if the stop is hit
    max_contracts: int = 50


@dataclass
class WorkerConfig:
    name: str
    symbol: str
    triggers: list[str] = field(default_factory=lambda: ["vwap_cross", "ema50_cross", "orb"])
    dte: int = 0                      # 0 = same-day expiry, 1 = next trading day
    strike: str = "atm"               # atm | otm1 | itm1 | delta:0.40
    sizing: Sizing = field(default_factory=Sizing)
    exits: ExitRules = field(default_factory=ExitRules)
    daily_goal: float = 1000.0        # clock out once realized P&L reaches this
    max_daily_loss: float = 500.0     # clock out once realized P&L falls to -this
    start_time: str = "09:35"
    end_time: str = "15:30"
    cooldown_minutes: float = 2.0
    max_trades_per_day: int = 10
    min_close_beyond_atr: float = 0.05  # candle must close at least this far past the level
    trend_filter: bool = False        # calls only above EMA50 & VWAP, puts only below
    enabled: bool = True


@dataclass
class RiskConfig:
    max_daily_loss: float = 1500.0    # all workers combined -> kill switch
    max_open_positions: int = 3
    max_premium_exposure: float = 8000.0
    max_spread_pct: float = 12.0
    min_premium: float = 0.30
    max_premium: float = 15.0
    pdt_guard: bool = True


@dataclass
class SimConfig:
    starting_cash: float = 30000.0
    iv: dict[str, float] = field(default_factory=lambda: {"SPY": 0.15, "QQQ": 0.18, "IWM": 0.22})
    half_spread_pct: float = 0.5      # half the bid/ask spread as % of mid
    min_half_spread: float = 0.01
    fee_per_contract: float = 0.03    # regulatory fees (Alpaca options are commission-free)
    strike_step: dict[str, float] = field(default_factory=lambda: {"SPY": 1.0, "QQQ": 1.0, "IWM": 1.0})
    use_historical_option_bars: bool = False  # backtest with real option prices (data.source: polygon | alpaca)
    # weekdays (0=Mon .. 4=Fri) with a listed expiry, per symbol; unlisted symbols get Fridays only.
    # A holiday on a listed weekday moves that expiry to the trading day before. Live trading uses the
    # real chain instead, so this only matters for backtests and replays.
    expiry_weekdays: dict[str, list[int]] = field(default_factory=lambda: {
        "SPY": [0, 1, 2, 3, 4], "QQQ": [0, 1, 2, 3, 4], "IWM": [0, 1, 2, 3, 4]})
    crypto_half_spread_pct: float = 0.02  # crypto mode: half the bid/ask spread as % of price
    crypto_fee_pct: float = 0.25      # crypto mode: Alpaca's taker fee, % of each fill's value


@dataclass
class DataConfig:
    source: str = "synthetic"         # synthetic | csv | polygon | alpaca
    csv_dir: str = "data/bars"
    option_bars_dir: str = "data/option_bars"
    live_data: str = "alpaca"         # paper/live price source: alpaca | polygon
    polygon_feed: str = "realtime"    # realtime | delayed
    alpaca_stock_feed: str = "iex"    # iex (free) | sip (paid)
    alpaca_options_feed: str = "indicative"  # indicative (free) | opra (paid)
    quote_poll_seconds: float = 2.0


@dataclass
class BrokerConfig:
    name: str = "sim"                 # sim | alpaca
    order_timeout_seconds: float = 8.0
    exit_retries: int = 3


@dataclass
class DashboardConfig:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass
class Config:
    mode: str = "paper"
    market: str = "options"           # options (US stock options) | crypto (coins, 24/7, long only)
    live_trading_enabled: bool = False
    workers: list[WorkerConfig] = field(default_factory=list)
    risk: RiskConfig = field(default_factory=RiskConfig)
    sim: SimConfig = field(default_factory=SimConfig)
    data: DataConfig = field(default_factory=DataConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    entry_cutoff: str = "15:30"
    flatten_time: str = "15:55"       # half days: 5 min before the 13:00 close
    db_path: str = "data/scalpcity.db"
    reconcile_seconds: float = 60.0
    stale_data_seconds: float = 30.0
    alert_webhook_env: str = "SCALPCITY_ALERT_WEBHOOK"

    @property
    def symbols(self) -> list[str]:
        return sorted({w.symbol for w in self.workers if w.enabled})

    def worker(self, name: str) -> WorkerConfig:
        for w in self.workers:
            if w.name == name:
                return w
        raise KeyError(name)


def _build(cls, raw: dict[str, Any] | None):
    raw = raw or {}
    known = {f.name: f for f in fields(cls)}
    unknown = set(raw) - set(known)
    if unknown:
        raise ValueError(f"unknown {cls.__name__} keys: {sorted(unknown)}")
    kwargs = {}
    nested = {"sizing": Sizing, "exits": ExitRules, "risk": RiskConfig, "sim": SimConfig,
              "data": DataConfig, "broker": BrokerConfig, "dashboard": DashboardConfig}
    for k, v in raw.items():
        if k in nested and isinstance(v, dict):
            kwargs[k] = _build(nested[k], v)
        elif k == "workers":
            kwargs[k] = [_build(WorkerConfig, w) for w in v]
        else:
            kwargs[k] = v
    return cls(**kwargs)


def validate(cfg: Config) -> None:
    if cfg.mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
    if cfg.market not in {"options", "crypto"}:
        raise ValueError("market must be options|crypto")
    if cfg.data.source not in {"synthetic", "csv", "polygon", "alpaca"}:
        raise ValueError("data.source must be synthetic|csv|polygon|alpaca")
    for w in cfg.workers:
        crypto_sym = "/" in w.symbol
        if crypto_sym != (cfg.market == "crypto"):
            raise ValueError(f"{w.name}: {w.symbol} doesn't fit market: {cfg.market} "
                             f"(crypto symbols look like BTC/USD; option underlyings like SPY)")
    if cfg.market == "crypto" and cfg.data.source == "polygon":
        raise ValueError("market: crypto needs data.source: alpaca (or csv / synthetic)")
    names = [w.name for w in cfg.workers]
    if len(names) != len(set(names)):
        raise ValueError("worker names must be unique")
    if not any(w.enabled for w in cfg.workers):
        raise ValueError("at least one worker must be enabled")
    for w in cfg.workers:
        bad = set(w.triggers) - VALID_TRIGGERS
        if bad:
            raise ValueError(f"{w.name}: unknown triggers {sorted(bad)}")
        if w.dte < 0:
            raise ValueError(f"{w.name}: dte must be >= 0")
        if w.sizing.mode not in {"fixed", "budget", "risk"}:
            raise ValueError(f"{w.name}: sizing.mode must be fixed|budget|risk")
        if not (w.strike in {"atm", "otm1", "itm1"} or w.strike.startswith("delta:")):
            raise ValueError(f"{w.name}: strike must be atm|otm1|itm1|delta:<x>")
    if cfg.mode == "live":
        if not cfg.live_trading_enabled:
            raise ValueError("mode=live requires live_trading_enabled: true in config")
        if os.environ.get(LIVE_CONFIRM_ENV) != LIVE_CONFIRM_VALUE:
            raise ValueError(f"mode=live requires env {LIVE_CONFIRM_ENV}={LIVE_CONFIRM_VALUE}")
    if cfg.mode in {"paper", "live"}:
        if cfg.broker.name != "alpaca":
            raise ValueError("paper/live modes need broker.name: alpaca")
        if cfg.data.live_data not in {"alpaca", "polygon"}:
            raise ValueError("data.live_data must be alpaca|polygon")
        if cfg.data.alpaca_stock_feed not in {"iex", "sip"}:
            raise ValueError("data.alpaca_stock_feed must be iex|sip")
        if cfg.data.alpaca_options_feed not in {"indicative", "opra"}:
            raise ValueError("data.alpaca_options_feed must be indicative|opra")


def load(path: str | Path, mode: str | None = None) -> Config:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    if mode:
        raw["mode"] = mode
    cfg = _build(Config, raw)
    from . import calendar as cal
    cal.set_market(cfg.market)
    if cfg.mode in {"backtest", "replay"}:
        cfg.broker.name = "sim"
    validate(cfg)
    return cfg
