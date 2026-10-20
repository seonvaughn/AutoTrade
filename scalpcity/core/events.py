"""Every message that travels on the bus.

Bots never call each other to *do* things; they publish one of these events and
whoever owns the next step reacts. All timestamps are tz-aware America/New_York.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import ClassVar, Optional, Union


class Side(str, Enum):
    CALL = "CALL"
    PUT = "PUT"

    @property
    def arrow(self) -> str:
        return "▲" if self is Side.CALL else "▼"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Purpose(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"


class SessionKind(str, Enum):
    NEW_DAY = "new_day"            # first heartbeat of a trading date
    OPEN = "open"                  # 9:30 ET
    ENTRY_CUTOFF = "entry_cutoff"  # no new entries after this
    FLATTEN = "flatten"            # close every open position
    CLOSED = "closed"              # 16:00 ET (13:00 on half days)


@dataclass
class Event:
    ts: datetime


# ---------------------------------------------------------------- time / data
@dataclass
class Heartbeat(Event):
    """Advances time. Live: wall clock every second. Replay: data timestamps."""


@dataclass
class SessionEvent(Event):
    kind: SessionKind
    day: date


@dataclass
class Tick(Event):
    symbol: str
    price: float
    size: float = 0.0


@dataclass
class Candle:
    symbol: str
    start: datetime  # minute the bar opened
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def typical(self) -> float:
        return (self.high + self.low + self.close) / 3.0


@dataclass
class CandleClosed(Event):
    candle: Candle
    backfill: bool = False  # True for warm-up / catch-up bars: update state, never trade


@dataclass
class BarClosed(Event):
    """A candle on a timeframe other than 1 minute: "30s", "5m", "15m", "30m" or "1h".
    (1-minute candles keep their own event, CandleClosed.)"""
    tf: str
    candle: Candle
    backfill: bool = False


@dataclass
class BreakOfStructure(Event):
    """TJR's rule: a candle BODY closed beyond the most recent high (bullish, CALL) or low (bearish, PUT).
    `shift` is True when it flips the trend on that timeframe."""
    symbol: str
    tf: str
    side: "Side"
    level: float
    candle: Candle
    shift: bool
    backfill: bool = False


@dataclass
class MorningPlan(Event):
    """The morning study's verdict for one ticker: cleared to trade today, or stood down (with reasons)."""
    symbol: str
    day: date
    cleared: bool
    reasons: list[str]
    details: dict


@dataclass
class LiquiditySweep(Event):
    """Price traded through a resting high ("high": buy-side liquidity) or low ("low": sell-side)."""
    symbol: str
    tf: str
    kind: str
    level: float
    candle: Candle
    backfill: bool = False


@dataclass
class StructureBreak(Event):
    """Price closed beyond the last swing high (bullish, side=CALL) or swing low (bearish, PUT)."""
    symbol: str
    tf: str
    side: "Side"
    level: float
    candle: Candle
    backfill: bool = False


@dataclass
class IndicatorValue(Event):
    name: str          # "vwap" | "ema50" | "atr" | "opening_range"
    symbol: str
    value: float       # for opening_range: the range high
    candle: Candle
    backfill: bool = False
    low: Optional[float] = None    # opening_range low
    ready: bool = True             # False while warming up / range not locked


# ---------------------------------------------------------------- instruments
@dataclass(frozen=True)
class OptionContract:
    underlying: str
    expiry: date
    strike: float
    right: Side
    kind: ClassVar[str] = "option"
    multiplier: ClassVar[int] = 100   # one contract = 100 shares

    @property
    def order_symbol(self) -> str:
        return self.occ

    @property
    def label(self) -> str:
        return f"{self.strike:g} {self.right.value}"

    @property
    def occ(self) -> str:
        """OCC/OSI symbol, e.g. QQQ261002C00752000."""
        cp = "C" if self.right is Side.CALL else "P"
        return f"{self.underlying}{self.expiry:%y%m%d}{cp}{int(round(self.strike * 1000)):08d}"

    @staticmethod
    def from_occ(sym: str) -> "OptionContract":
        root, rest = sym[:-15], sym[-15:]
        exp = datetime.strptime(rest[:6], "%y%m%d").date()
        right = Side.CALL if rest[6] == "C" else Side.PUT
        return OptionContract(root, exp, int(rest[7:]) / 1000.0, right)


@dataclass(frozen=True)
class CryptoAsset:
    """A coin pair bought outright, e.g. BTC/USD. Long only: Alpaca doesn't allow shorting crypto,
    so `right` is always CALL ("long") and a PUT signal can only close a position."""
    underlying: str                   # "BTC/USD"
    right: Side = Side.CALL
    kind: ClassVar[str] = "crypto"
    multiplier: ClassVar[int] = 1
    expiry: ClassVar[None] = None
    strike: ClassVar[None] = None

    @property
    def occ(self) -> str:
        """Position key; matches the symbol Alpaca's positions endpoint returns (no slash)."""
        return self.underlying.replace("/", "")

    @property
    def order_symbol(self) -> str:
        return self.underlying

    @property
    def label(self) -> str:
        return self.underlying


Instrument = Union[OptionContract, CryptoAsset]


def is_crypto_symbol(symbol: str) -> bool:
    return "/" in symbol


@dataclass
class OptionQuote(Event):
    """Bid/ask for an instrument (an option contract, or a coin in crypto mode)."""
    contract: Instrument
    bid: float
    ask: float
    delta: Optional[float] = None
    iv: Optional[float] = None
    underlying_price: Optional[float] = None

    @property
    def mid(self) -> float:
        return round((self.bid + self.ask) / 2.0, 4)

    @property
    def spread_pct(self) -> float:
        return (self.ask - self.bid) / self.mid if self.mid > 0 else 1.0


# ---------------------------------------------------------------- signals
@dataclass
class SetupUpdate(Event):
    """How close price is to firing a trigger ("charge %")."""
    symbol: str
    trigger: str
    side: Side
    level: float
    distance_atr: float
    charge: float  # 0..100


@dataclass
class Signal(Event):
    symbol: str
    trigger: str  # "vwap_cross" | "ema50_cross" | "orb"
    side: Side
    close: float
    level: float
    atr: Optional[float]
    ema50: Optional[float] = None
    vwap: Optional[float] = None
    backfill: bool = False  # fired on history (warm-up): studied by the edge tracker, never traded
    # TJR entry models plan the trade on the chart: stop beyond the swept high/low, target at the next
    # resting liquidity (underlying prices). None for the indicator triggers.
    stop: Optional[float] = None
    target: Optional[float] = None
    setup: Optional[dict] = None    # what the chart showed (sweep, break, order block / gap, equilibrium)


@dataclass
class WorkerSignal(Event):
    worker: str
    signal: Signal


@dataclass
class KeyLevel:
    price: float
    label: str      # "prior day high", "5-day low", "turning point ×3", ...
    strength: int   # how many times the market reacted there (1 for prior-day levels)


@dataclass
class KeyLevels(Event):
    """Price levels marked from past sessions, published once per symbol per day."""
    symbol: str
    day: date
    levels: list[KeyLevel]


@dataclass
class ResearchCleared(Event):
    """The research gate found enough evidence: the worker may look for a contract."""
    worker: str
    signal: Signal
    evidence: dict


@dataclass
class EntryVetoed(Event):
    """The research gate refused an entry, with the evidence that failed."""
    worker: str
    signal: Signal
    reason: str
    evidence: dict


@dataclass
class SignalSkipped(Event):
    worker: str
    signal: Signal
    reason: str


@dataclass
class ContractSelected(Event):
    worker: str
    signal: Signal
    quote: OptionQuote


@dataclass
class ContractRejected(Event):
    worker: str
    signal: Signal
    reason: str


# ---------------------------------------------------------------- orders
@dataclass
class OrderIntent(Event):
    worker: str
    contract: Instrument
    side: OrderSide
    qty: float
    limit: float
    purpose: Purpose
    reason: str  # entry: trigger name; exit: "target" | "stop" | "profit_lock" | ...
    signal: Optional[Signal] = None
    intent_id: str = ""


@dataclass
class OrderApproved(Event):
    intent: OrderIntent


@dataclass
class OrderRejected(Event):
    intent: OrderIntent
    reason: str


@dataclass
class Fill(Event):
    intent: OrderIntent
    qty: float
    price: float
    fees: float
    order_id: str


@dataclass
class OrderFailed(Event):
    intent: OrderIntent
    reason: str
    filled_qty: float = 0


# ---------------------------------------------------------------- positions / pnl
@dataclass
class PositionOpened(Event):
    worker: str
    contract: Instrument
    qty: float
    entry_price: float
    signal: Optional[Signal]


@dataclass
class TradeClosed(Event):
    worker: str
    contract: Instrument
    qty: float
    entry_price: float
    exit_price: float
    pnl: float
    reason: str
    opened_at: datetime


@dataclass
class PnLUpdate(Event):
    worker: str
    realized: float
    unrealized: float
    vault: float  # all workers, realized + unrealized


@dataclass
class WorkerStatus(Event):
    worker: str
    clocked_out: bool
    reason: str
    day_pnl: float = 0.0


@dataclass
class KillSwitchRequest(Event):
    reason: str
    engage: bool = True


@dataclass
class KillSwitch(Event):
    engaged: bool
    reason: str


# ---------------------------------------------------------------- ops / reporting
@dataclass
class HealthStatus(Event):
    ok: bool
    reason: str
    source: str = "health"  # each monitor reports separately; trading pauses if ANY source is not ok


@dataclass
class Alert(Event):
    level: str  # "info" | "warning" | "critical"
    text: str


@dataclass
class BotError(Event):
    bot: str
    error: str


@dataclass
class Thought(Event):
    worker: str
    text: str
    tone: str = "info"  # info | good | bad | fire | goal


@dataclass
class WorkerStats:
    worker: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    pnl: float = 0.0
    gross_win: float = 0.0
    gross_loss: float = 0.0
    peak: float = 0.0
    max_drawdown: float = 0.0

    @property
    def win_rate(self) -> float:
        return self.wins / self.trades if self.trades else 0.0

    @property
    def expectancy(self) -> float:
        return self.pnl / self.trades if self.trades else 0.0


@dataclass
class Leaderboard(Event):
    stats: list[WorkerStats]


@dataclass
class DailySummary(Event):
    day: date
    total: float
    by_worker: dict[str, float]
    trades: int
    wins: int
    top_worker: Optional[str] = None
    extra: dict = field(default_factory=dict)
