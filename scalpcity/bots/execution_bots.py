"""Execution layer: placing orders, managing exits, reconciling with the broker."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from ..core import calendar as cal
from ..core.costs import QTY_EPS, fees
from ..core.events import (Alert, Fill, Heartbeat, HealthStatus, KillSwitch, OptionQuote, OrderApproved, OrderFailed,
                           OrderIntent, OrderRejected, OrderSide, PositionOpened, Purpose, SessionEvent, SessionKind,
                           Side, Signal, Tick, TradeClosed)
from .base import Bot


class ExecutionBot(Bot):
    name = "execution"
    skill = "Send approved orders to the broker and report fills (entries: limit at ask; exits: walk down to market)"

    def setup(self) -> None:
        self.on(OrderApproved, self.on_approved)

    async def on_approved(self, e: OrderApproved) -> None:
        if self.ctx.broker.synchronous_fills:
            await self._run(e.intent, inline=True)
        else:
            self.spawn(self._run(e.intent, inline=False))

    async def _out(self, event, inline: bool) -> None:
        if inline:
            self.emit(event)
        else:
            await self.bus.emit(event)

    def _now(self, intent: OrderIntent, inline: bool) -> datetime:
        return intent.ts if inline else cal.now_et()

    async def _run(self, intent: OrderIntent, inline: bool) -> None:
        broker = self.ctx.broker
        exit_ = intent.purpose is Purpose.EXIT
        attempts = 1 + (self.cfg.broker.exit_retries if exit_ else 0)
        remaining, filled, notional, last_oid, last_err = intent.qty, 0, 0.0, "", "not filled"
        for attempt in range(attempts):
            limit = intent.limit
            if exit_:
                limit = None if attempt == attempts - 1 else await self._exit_limit(intent, attempt)
            try:
                last_oid = await broker.submit(intent.contract, intent.side, remaining, limit)
                st = await self._wait(last_oid)
            except Exception as exc:  # noqa: BLE001
                last_err = f"broker error: {exc}"
                await self._out(Alert(self._now(intent, inline), "warning", f"{intent.worker}: {last_err}"), inline)
                if not exit_:
                    break
                continue
            if st.filled_qty:
                filled += st.filled_qty
                notional += st.filled_qty * st.avg_price
                remaining -= st.filled_qty
            if remaining <= QTY_EPS or not exit_:
                last_err = f"order {st.status}"
                break
            last_err = f"order {st.status}"
        if filled > QTY_EPS:
            fee = fees(intent.contract, filled, notional / filled, self.cfg.sim)
            await self._out(Fill(self._now(intent, inline), intent, filled, round(notional / filled, 4), fee,
                                 last_oid), inline)
        if remaining > QTY_EPS:
            await self._out(OrderFailed(self._now(intent, inline), intent, last_err, filled), inline)

    async def _exit_limit(self, intent: OrderIntent, attempt: int):
        q = await self.bot("options_chain").quote(intent.contract)
        if q is None or q.bid <= 0:
            return None
        if intent.contract.kind == "crypto":  # walk down 0.05% of price per attempt
            return q.bid * (1 - 0.0005 * attempt)
        return max(0.01, round(q.bid - 0.01 * attempt, 2))

    async def _wait(self, oid: str):
        broker = self.ctx.broker
        if broker.synchronous_fills:
            return await broker.status(oid)
        deadline = asyncio.get_running_loop().time() + self.cfg.broker.order_timeout_seconds
        while True:
            st = await broker.status(oid)
            if st.done:
                return st
            if asyncio.get_running_loop().time() >= deadline:
                await broker.cancel(oid)
                for _ in range(10):
                    await asyncio.sleep(0.3)
                    st = await broker.status(oid)
                    if st.done:
                        return st
                return st
            await asyncio.sleep(0.4)


class ExitManagerBot(Bot):
    name = "exit_manager"
    skill = "Decide when to get out: profit lock, target, stop, time stop, reversal, end of day, kill switch"

    def setup(self) -> None:
        self.pos: dict[str, dict] = {}
        self.on(PositionOpened, self.on_opened)
        self.on(TradeClosed, lambda e: self.pos.pop(e.worker, None))
        self.on(Fill, self.on_fill)
        self.on(OrderFailed, self.on_not_done)
        self.on(OrderRejected, self.on_not_done)
        self.on(OptionQuote, self.on_quote)
        self.on(Tick, self.on_tick)
        self.on(Heartbeat, self.on_heartbeat)
        self.on(Signal, self.on_signal)
        self.on(SessionEvent, self.on_session)
        self.on(KillSwitch, lambda e: e.engaged and self.exit_all("kill", e.ts))

    def on_opened(self, e: PositionOpened) -> None:
        p = self.pos[e.worker] = {"contract": e.contract, "qty": e.qty, "entry": e.entry_price, "opened": e.ts,
                                  "peak": 0.0, "exiting": False, "quote": None, "under": None}
        s = e.signal
        x = self.cfg.worker(e.worker).exits
        way = 1 if s and s.side is Side.CALL else -1
        if s and x.measure == "structure" and s.stop is not None and s.target is not None:
            p["under"] = {"symbol": s.symbol, "stop": s.stop, "target": s.target, "way": way}
        elif s and x.measure == "underlying" and s.atr:
            p["under"] = {"symbol": s.symbol, "stop": s.close - way * x.stop_atr * s.atr,
                          "target": s.close + way * x.target_atr * s.atr, "way": way}

    def on_fill(self, e: Fill) -> None:
        p = self.pos.get(e.intent.worker)
        if p and e.intent.purpose is Purpose.EXIT:
            p["qty"] -= e.qty
            p["exiting"] = False  # if anything is left, try again on the next quote

    def on_not_done(self, e) -> None:
        p = self.pos.get(e.intent.worker)
        if p and e.intent.purpose is Purpose.EXIT:
            p["exiting"] = False

    def on_quote(self, q: OptionQuote) -> None:
        for worker, p in self.pos.items():
            if p["contract"] == q.contract:
                p["quote"] = q
                self.evaluate(worker, p, q.ts)

    def on_heartbeat(self, hb: Heartbeat) -> None:
        for worker, p in list(self.pos.items()):
            if p["quote"] is not None:
                self.evaluate(worker, p, hb.ts)

    def on_tick(self, t: Tick) -> None:
        for worker, p in list(self.pos.items()):
            u = p["under"]
            if u and u["symbol"] == t.symbol and not p["exiting"] and p["qty"] > QTY_EPS:
                if u["way"] * (t.price - u["stop"]) <= 0:
                    self.exit(worker, "stop", t.ts)
                elif u["way"] * (t.price - u["target"]) >= 0:
                    self.exit(worker, "target", t.ts)

    def evaluate(self, worker: str, p: dict, ts: datetime) -> None:
        if p["exiting"] or p["quote"] is None or p["qty"] <= QTY_EPS:
            return
        x = self.cfg.worker(worker).exits
        if p["under"]:  # stop and target are measured on the stock (on_tick); only the clock is checked here
            if ts - p["opened"] >= timedelta(minutes=x.max_hold_minutes):
                self.exit(worker, "time", ts)
            return
        gain = (p["quote"].bid - p["entry"]) / p["entry"] * 100
        p["peak"] = max(p["peak"], gain)
        reason = None
        if gain <= -x.stop_loss_pct:
            reason = "stop"
        elif gain >= x.take_profit_pct:
            reason = "target"
        elif p["peak"] >= x.trail_activate_pct and gain <= p["peak"] * x.trail_lock_ratio:
            reason = "profit_lock"
        elif ts - p["opened"] >= timedelta(minutes=x.max_hold_minutes):
            reason = "time"
        if reason:
            self.exit(worker, reason, ts)

    def on_signal(self, s: Signal) -> None:
        if s.backfill:
            return
        for worker, p in list(self.pos.items()):
            w = self.cfg.worker(worker)
            if (w.exits.exit_on_reversal and w.symbol == s.symbol and s.trigger in w.triggers
                    and p["contract"].right is not s.side):
                self.exit(worker, "reversal", s.ts)

    def on_session(self, e: SessionEvent) -> None:
        if e.kind in (SessionKind.FLATTEN, SessionKind.CLOSED):
            self.exit_all("end_of_day", e.ts)

    def exit_all(self, reason: str, ts) -> None:
        for worker in list(self.pos):
            self.exit(worker, reason, ts)

    def exit(self, worker: str, reason: str, ts) -> None:
        p = self.pos[worker]
        if p["exiting"] or p["qty"] <= QTY_EPS:
            return
        p["exiting"] = True
        bid = p["quote"].bid if p["quote"] else 0.01
        self.emit(OrderIntent(ts, worker, p["contract"], OrderSide.SELL, p["qty"], max(bid, 0.01), Purpose.EXIT,
                              reason))


class ReconciliationBot(Bot):
    name = "reconciliation"
    skill = "Check the broker's real positions match what the bots think they hold"
    CRYPTO_TOLERANCE = 0.02  # Alpaca takes crypto fees out of the coin received, so holdings run slightly short

    @classmethod
    def matches(cls, expected: dict, actual: dict) -> bool:
        if expected.keys() != actual.keys():
            return False
        for k, want in expected.items():
            have = actual[k]
            if float(want).is_integer() and float(have).is_integer():
                if want != have:
                    return False
            elif abs(have - want) > cls.CRYPTO_TOLERANCE * max(abs(want), abs(have)):
                return False
        return True

    def setup(self) -> None:
        self.last = None
        self.mismatches = 0
        self.flagged = False
        self.on(Heartbeat, self.on_heartbeat)

    async def on_heartbeat(self, hb: Heartbeat) -> None:
        if self.last and (hb.ts - self.last).total_seconds() < self.cfg.reconcile_seconds:
            return
        self.last = hb.ts
        expected = self.bot("ledger").holdings()
        try:
            actual = await self.ctx.broker.positions()
        except Exception as exc:  # noqa: BLE001
            self.emit(Alert(hb.ts, "warning", f"reconciliation: could not read broker positions: {exc}"))
            return
        if self.matches(expected, actual):
            self.mismatches = 0
            if self.flagged:
                self.flagged = False
                self.emit(HealthStatus(hb.ts, True, "positions reconciled", "reconciliation"))
            return
        self.mismatches += 1
        if self.mismatches >= 2 and not self.flagged:  # one check of grace for in-flight orders
            self.flagged = True
            text = f"position mismatch — bots think {expected}, broker has {actual}"
            self.emit(Alert(hb.ts, "critical", text))
            self.emit(HealthStatus(hb.ts, False, text, "reconciliation"))
