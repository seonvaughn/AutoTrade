"""Decision & risk layer."""
from __future__ import annotations

import itertools

from ..core import calendar as cal
from ..core.costs import round_qty
from ..core.events import (ContractRejected, ContractSelected, HealthStatus, KillSwitch, KillSwitchRequest,
                           OrderApproved, OrderFailed, OrderIntent, OrderRejected, OrderSide, PnLUpdate, PositionOpened,
                           Purpose, ResearchCleared, SessionEvent, SessionKind, Side, TradeClosed, WorkerStatus)
from .base import Bot

_intent_ids = itertools.count(1)


class ContractSelectorBot(Bot):
    name = "contract_selector"
    skill = "Pick the option contract (expiry + strike) for a researched signal; reject illiquid ones"

    def setup(self) -> None:
        self.on(ResearchCleared, self.on_signal)

    MAX_EXPIRY_SEARCH = 7  # trading days to look past `dte` for a listed expiry (most stocks list Fridays only)

    async def on_signal(self, ws: ResearchCleared) -> None:
        w = self.cfg.worker(ws.worker)
        sig = ws.signal
        chain_bot = self.bot("options_chain")
        if cal.is_crypto():
            q = await chain_bot.crypto_quote(sig.symbol)
            if q is None:
                self.emit(ContractRejected(sig.ts, ws.worker, sig, f"no quote for {sig.symbol}"))
                return
        else:
            expiry = cal.next_trading_day(sig.ts.date(), w.dte)
            chain = []
            for _ in range(self.MAX_EXPIRY_SEARCH + 1):
                chain = await chain_bot.get_chain(sig.symbol, expiry, sig.side, sig.close)
                if chain:
                    break
                expiry = cal.next_trading_day(expiry)
            if not chain:
                self.emit(ContractRejected(sig.ts, ws.worker, sig, f"no {sig.side.value} chain within "
                                                                   f"{self.MAX_EXPIRY_SEARCH} days of {w.dte}DTE"))
                return
            q = self.pick(chain, w.strike, sig.side, sig.close)
        risk = self.cfg.risk
        if q.contract.kind == "option" and (q.ask < risk.min_premium or q.ask > risk.max_premium):
            self.emit(ContractRejected(sig.ts, ws.worker, sig,
                                       f"premium ${q.ask:.2f} outside ${risk.min_premium}-${risk.max_premium}"))
        elif q.bid <= 0 or q.spread_pct * 100 > risk.max_spread_pct:
            self.emit(ContractRejected(sig.ts, ws.worker, sig, f"spread too wide ({q.bid:.2f}/{q.ask:.2f})"))
        else:
            self.emit(ContractSelected(sig.ts, ws.worker, sig, q))

    @staticmethod
    def pick(chain, mode: str, side: Side, spot: float):
        by_strike = sorted(chain, key=lambda q: q.contract.strike)
        if mode.startswith("delta:"):
            target = float(mode.split(":", 1)[1])
            with_delta = [q for q in by_strike if q.delta is not None]
            if with_delta:
                return min(with_delta, key=lambda q: abs(abs(q.delta) - target))
        i = min(range(len(by_strike)), key=lambda j: abs(by_strike[j].contract.strike - spot))
        step = {"otm1": 1, "itm1": -1}.get(mode, 0)
        if side is Side.PUT:
            step = -step
        return by_strike[max(0, min(len(by_strike) - 1, i + step))]


class PositionSizerBot(Bot):
    name = "position_sizer"
    skill = "Turn the worker's sizing rule into a contract count"

    def setup(self) -> None:
        self.on(ContractSelected, self.on_selected)

    def on_selected(self, e: ContractSelected) -> None:
        w = self.cfg.worker(e.worker)
        s = w.sizing
        c = e.quote.contract
        unit = e.quote.ask * c.multiplier
        if s.mode == "fixed":
            qty = s.contracts
        elif s.mode == "budget":
            qty = s.budget / unit
        else:  # risk: lose `risk` dollars if the stop is hit
            qty = s.risk / (unit * w.exits.stop_loss_pct / 100.0)
        qty = round_qty(c, min(qty, s.max_contracts))
        if qty <= 0 or (c.kind == "option" and qty < 1):
            self.emit(ContractRejected(e.ts, e.worker, e.signal, f"size rounds to 0 at ${e.quote.ask:.2f}"))
            return
        self.emit(OrderIntent(e.ts, e.worker, e.quote.contract, OrderSide.BUY, qty, e.quote.ask, Purpose.ENTRY,
                              e.signal.trigger, e.signal, f"i{next(_intent_ids)}"))


class RiskManagerBot(Bot):
    name = "risk_manager"
    skill = "Final yes/no on every order (exits are always allowed)"

    def setup(self) -> None:
        self.kill = False
        self.problems: dict[str, str] = {}     # health source -> reason
        self.clocked_out: set[str] = set()
        self.exposure: dict[str, float] = {}   # worker -> premium at risk (open + pending)
        self.on(OrderIntent, self.on_intent)
        self.on(KillSwitch, lambda e: setattr(self, "kill", e.engaged))
        self.on(HealthStatus, self.on_health)
        self.on(WorkerStatus, self.on_status)
        self.on(OrderFailed, self.on_failed)
        self.on(PositionOpened, lambda e: self.exposure.__setitem__(e.worker,
                                                                    e.qty * e.entry_price * e.contract.multiplier))
        self.on(TradeClosed, lambda e: self.exposure.pop(e.worker, None))
        self.on(SessionEvent, self.on_session)

    def on_status(self, e: WorkerStatus) -> None:
        (self.clocked_out.add if e.clocked_out else self.clocked_out.discard)(e.worker)

    def on_session(self, e: SessionEvent) -> None:
        if e.kind is SessionKind.NEW_DAY:
            self.clocked_out.clear()

    def on_health(self, e: HealthStatus) -> None:
        if e.ok:
            self.problems.pop(e.source, None)
        else:
            self.problems[e.source] = e.reason

    def on_failed(self, e: OrderFailed) -> None:
        if e.intent.purpose is Purpose.ENTRY and e.filled_qty == 0:
            self.exposure.pop(e.intent.worker, None)

    async def on_intent(self, o: OrderIntent) -> None:
        if o.purpose is Purpose.EXIT:
            self.emit(OrderApproved(o.ts, o))
            return
        reason = await self._check(o)
        if reason:
            self.emit(OrderRejected(o.ts, o, reason))
        else:
            self.exposure[o.worker] = o.qty * o.limit * o.contract.multiplier
            self.emit(OrderApproved(o.ts, o))

    async def _check(self, o: OrderIntent) -> str | None:
        r = self.cfg.risk
        clock = self.bot("clock")
        cost = o.qty * o.limit * o.contract.multiplier
        crypto = o.contract.kind == "crypto"
        if self.kill:
            return "kill switch engaged"
        if self.problems:
            return "paused: " + "; ".join(self.problems.values())
        if clock and not clock.entries_allowed():
            return "market closed or past entry cutoff"
        if o.worker in self.clocked_out:
            return "worker clocked out"
        if len(self.exposure) >= r.max_open_positions:
            return f"max {r.max_open_positions} open positions"
        if sum(self.exposure.values()) + cost > r.max_premium_exposure:
            return f"premium exposure would exceed ${r.max_premium_exposure:,.0f}"
        acct = await self.ctx.broker.account()
        bp = acct.crypto_buying_power if crypto else acct.options_buying_power
        if cost > bp:
            return f"not enough buying power (${bp:,.0f})"
        if r.pdt_guard and not crypto and not acct.cash_account and acct.equity < 25000 and acct.daytrade_count >= 3:
            return "pattern-day-trader guard: 3 day trades in 5 days on a sub-$25k margin account"
        return None


class DailyGoalBot(Bot):
    name = "daily_goal"
    skill = "Clock workers out at their daily goal / loss limit; own the kill switch"

    def setup(self) -> None:
        self.pnl: dict[str, float] = {}
        self.out: set[str] = set()
        self.kill = False
        self.kill_reason = ""
        self.on(TradeClosed, self.on_closed)
        self.on(PnLUpdate, self.on_pnl)
        self.on(KillSwitchRequest, self.on_request)
        self.on(SessionEvent, self.on_session)

    def on_pnl(self, e: PnLUpdate) -> None:
        """Open losses count too: trip the kill switch on realized + unrealized."""
        if not self.kill and e.vault <= -self.cfg.risk.max_daily_loss:
            self.kill, self.kill_reason = True, "max daily loss"
            self.emit(KillSwitch(e.ts, True, f"account down ${-e.vault:,.0f} today incl. open trades "
                                             f"(limit ${self.cfg.risk.max_daily_loss:,.0f})"))

    def on_closed(self, e: TradeClosed) -> None:
        self.pnl[e.worker] = self.pnl.get(e.worker, 0.0) + e.pnl
        w = self.cfg.worker(e.worker)
        p = self.pnl[e.worker]
        if e.worker not in self.out:
            if p >= w.daily_goal:
                self.out.add(e.worker)
                self.emit(WorkerStatus(e.ts, e.worker, True, "daily goal", p))
            elif p <= -w.max_daily_loss:
                self.out.add(e.worker)
                self.emit(WorkerStatus(e.ts, e.worker, True, "daily loss limit", p))
        total = sum(self.pnl.values())
        if not self.kill and total <= -self.cfg.risk.max_daily_loss:
            self.kill, self.kill_reason = True, "max daily loss"
            self.emit(KillSwitch(e.ts, True, f"account down ${-total:,.0f} today (limit ${self.cfg.risk.max_daily_loss:,.0f})"))

    def on_request(self, e: KillSwitchRequest) -> None:
        if e.engage != self.kill:
            self.kill = e.engage
            self.kill_reason = "manual" if e.engage else ""
            self.emit(KillSwitch(e.ts, e.engage, e.reason))

    def on_session(self, e: SessionEvent) -> None:
        if e.kind is SessionKind.NEW_DAY:
            for w in list(self.out):
                self.emit(WorkerStatus(e.ts, w, False, "new day"))
            self.pnl.clear()
            self.out.clear()
            if self.kill and self.kill_reason != "manual":
                self.kill = False
                self.emit(KillSwitch(e.ts, False, "new day"))
