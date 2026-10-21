"""Orchestrator — builds, wires, starts and stops every bot.

The registration order below is the delivery order on the bus, and it matters:
indicators (ATR first) before signals, signals before the filter, ledger before
exit manager, and so on.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta

from .bots.base import Context
from .bots.candle_bot import CandleBot
from .bots.chart_bots import HigherTimeframeBot, StructureBot, TimeframeBot, ZonesBot
from .bots.clock_bot import ClockBot
from .bots.decision_bots import ContractSelectorBot, DailyGoalBot, PositionSizerBot, RiskManagerBot
from .bots.execution_bots import ExecutionBot, ExitManagerBot, ReconciliationBot
from .bots.learning_bots import LessonsBot, TradeReviewBot
from .bots.indicator_bots import ATRBot, EMABot, OpeningRangeBot, VWAPBot
from .bots.ops_bots import AlertBot, HealthBot
from .bots.options_chain_bot import OptionsChainBot
from .bots.orb_bots import OpeningRange15Bot, OpeningRangeNTZBot
from .bots.price_feed_bot import PriceFeedBot
from .bots.record_bots import AnalystBot, JournalBot, LedgerBot
from .bots.research_bots import EdgeTrackerBot, KeyLevelsBot, ResearchGateBot
from .bots.signal_bots import (EMACrossBot, FibPullbackBot, ORBBot, StructureBreakBot, VWAPCrossBot,
                               ZoneReactionBot)
from .bots.signal_filter_bot import SignalFilterBot
from .bots.smc_bots import (DailyBiasBot, ImbalanceBot, LiquidityBot, MarketStructureBot, MorningStudyBot,
                            NewsCalendarBot, OrderBlockBot, SmartMoneyEntryBot)
from .core import calendar as cal
from .core.bus import EventBus
from .core.config import Config
from .core.events import Alert, KillSwitchRequest
from .core.storage import Storage

log = logging.getLogger("scalpcity.orchestrator")

BOT_ORDER = [
    ClockBot, HealthBot, CandleBot, TimeframeBot, OptionsChainBot,
    ATRBot, VWAPBot, EMABot, OpeningRangeBot, KeyLevelsBot, HigherTimeframeBot, StructureBot, ZonesBot,
    MarketStructureBot, LiquidityBot, ImbalanceBot, OrderBlockBot, DailyBiasBot, NewsCalendarBot,
    VWAPCrossBot, EMACrossBot, ORBBot, ZoneReactionBot, StructureBreakBot, FibPullbackBot, SmartMoneyEntryBot,
    OpeningRange15Bot, OpeningRangeNTZBot, EdgeTrackerBot, MorningStudyBot,
    SignalFilterBot, ResearchGateBot, ContractSelectorBot, PositionSizerBot, RiskManagerBot, ExecutionBot,
    LedgerBot, ExitManagerBot, TradeReviewBot, LessonsBot, DailyGoalBot, ReconciliationBot,
    JournalBot, AnalystBot, AlertBot,
]

# Bots that only serve the older indicator/chart triggers. They are built only when an enabled tower trades one
# of them, so the crew stays focused on what the towers actually trade.
LEGACY = {
    "vwap_cross": [VWAPCrossBot], "ema50_cross": [EMACrossBot], "orb": [OpeningRangeBot, ORBBot],
    "zone_reaction": [ZonesBot, ZoneReactionBot], "structure_break": [StructureBot, StructureBreakBot],
    "fib_pullback": [StructureBot, FibPullbackBot],
    "orb15_breakout": [OpeningRange15Bot], "orb15_retest": [OpeningRange15Bot], "orb15_reversal": [OpeningRange15Bot],
    "orb_ntz_retest": [OpeningRangeNTZBot],
}


def bot_order(cfg: Config) -> list:
    traded = {t for w in cfg.workers if w.enabled for t in w.triggers}
    legacy = {cls for classes in LEGACY.values() for cls in classes}
    wanted = {cls for t in traded for cls in LEGACY.get(t, [])}
    return [cls for cls in BOT_ORDER if cls not in legacy or cls in wanted]


class Orchestrator:
    name = "orchestrator"
    skill = "Build, wire, start and stop every bot; graceful shutdown flattens positions"

    def __init__(self, cfg: Config, run_id: str | None = None, db_path: str | None = None,
                 dashboard: bool | None = None) -> None:
        self.cfg = cfg
        self.live = cfg.mode in {"paper", "live"}
        run_id = run_id or (cfg.mode if self.live else f"{cfg.mode}-{datetime.now():%Y%m%d-%H%M%S}")
        self.bus = EventBus()
        self.storage = Storage(db_path or cfg.db_path, run_id, cfg.mode)
        self.ctx = Context(cfg, self.bus, self.storage, broker=None, live=self.live)  # type: ignore[arg-type]
        self.ctx.bots[self.name] = self
        self.bots = [cls(self.ctx) for cls in bot_order(cfg)]
        self.ctx.broker = self._make_broker()
        want_dash = cfg.dashboard.enabled if dashboard is None else dashboard
        self.dashboard = None
        if want_dash:
            from .bots.dashboard_bot import DashboardBot
            self.dashboard = DashboardBot(self.ctx)
            self.bots.append(self.dashboard)
        self.feed = PriceFeedBot(self.ctx)  # last: it only produces events
        self.bots.append(self.feed)

    def _make_broker(self):
        if self.cfg.broker.name == "ibkr":
            from .brokers.ibkr import IBKRBroker
            return IBKRBroker(self.cfg)
        if self.cfg.broker.name == "alpaca":
            from .brokers.alpaca import AlpacaBroker
            return AlpacaBroker("live" if self.cfg.mode == "live" else "paper")
        from .brokers.sim import SimBroker
        chain = self.ctx.bots["options_chain"]
        clock = self.ctx.bots["clock"]
        return SimBroker(self.cfg.sim.starting_cash, self.cfg.sim, chain.quote_now,
                         lambda: clock.day or date.today())

    def roster(self) -> list[tuple[str, str]]:
        return [(self.name, self.skill)] + [(b.name, b.skill) for b in self.bots]

    async def start(self) -> None:
        for b in self.bots:
            await b.start()

    async def stop(self) -> None:
        for b in reversed(self.bots):
            await b.stop()
        await self.ctx.broker.close()

    # ---------------------------------------------------------------- replay / backtest
    async def replay(self, days: list[date], pace: float = 0.0) -> dict:
        if days:
            self.ctx.span = (days[0], days[-1])
        await self.start()
        try:
            await self.feed.replay(days, pace)
        finally:
            await self.stop()
        return self.ctx.bots["analyst"].report()

    # ---------------------------------------------------------------- paper / live
    async def run_live(self) -> None:
        await self._preflight()
        await self.start()
        stop = asyncio.Event()
        try:
            import signal
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError):
            pass
        try:
            await stop.wait()
        finally:
            await self._flatten_and_stop()

    async def _preflight(self) -> None:
        acct = await self.ctx.broker.account()
        log.warning("%s account: equity $%.2f, options buying power $%.2f, day trades %d",
                    self.cfg.mode.upper(), acct.equity, acct.options_buying_power, acct.daytrade_count)
        if hasattr(self.ctx.broker, "calendar"):
            today = cal.now_et().date()
            broker_days = set(await self.ctx.broker.calendar(today, today + timedelta(days=45)))
            ours = {d.isoformat() for d in cal.trading_days(today, today + timedelta(days=45))}
            if broker_days != ours:
                log.warning("market calendar differs from broker: ours-only %s, broker-only %s",
                            sorted(ours - broker_days), sorted(broker_days - ours))

    async def _flatten_and_stop(self) -> None:
        ledger = self.ctx.bots["ledger"]
        if ledger.pos:
            log.warning("shutting down with open positions — flattening first")
            await self.bus.emit(KillSwitchRequest(cal.now_et(), "shutdown"))
            for _ in range(60):
                if not ledger.pos:
                    break
                await asyncio.sleep(0.5)
            if ledger.pos:
                await self.bus.emit(Alert(cal.now_et(), "critical",
                                          f"shutdown: positions still open at broker: {ledger.holdings()}"))
        await self.stop()
