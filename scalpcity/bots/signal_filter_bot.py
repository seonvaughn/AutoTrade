"""Signal Filter Bot — routes raw signals to the workers that trade them, and
drops the ones a worker shouldn't take (busy, clocked out, cooling down, too
early/late, weak close, against the trend, too many trades today)."""
from __future__ import annotations

from datetime import datetime, timedelta

from ..core import calendar as cal
from ..core.events import (ContractRejected, EntryVetoed, OrderFailed, OrderRejected, PositionOpened, Purpose, SessionEvent,
                           SessionKind, Side, Signal, SignalSkipped, TradeClosed, WorkerSignal, WorkerStatus)
from .base import Bot


LONG_ONLY = "long only (Alpaca can't short crypto)"


class SignalFilterBot(Bot):
    name = "signal_filter"
    skill = "Decide which worker (if any) acts on each signal"

    def setup(self) -> None:
        self.state = {w.name: self._fresh() for w in self.cfg.workers if w.enabled}
        self.on(Signal, self.on_signal)
        self.on(PositionOpened, self.on_opened)
        self.on(TradeClosed, self.on_closed)
        self.on(WorkerStatus, self.on_status)
        self.on(ContractRejected, lambda e: self._clear(e.worker))
        self.on(EntryVetoed, lambda e: self._clear(e.worker))
        self.on(OrderRejected, lambda e: e.intent.purpose is Purpose.ENTRY and self._clear(e.intent.worker))
        self.on(OrderFailed, self.on_failed)
        self.on(SessionEvent, self.on_session)

    @staticmethod
    def _fresh() -> dict:
        return {"in_position": False, "pending": False, "clocked_out": False, "last_exit": None,
                "trades": 0, "last_candle": None}

    def _clear(self, worker: str) -> None:
        if worker in self.state:
            self.state[worker]["pending"] = False

    def on_failed(self, e: OrderFailed) -> None:
        if e.intent.purpose is Purpose.ENTRY and e.filled_qty == 0:
            self._clear(e.intent.worker)

    def on_session(self, e: SessionEvent) -> None:
        if e.kind is SessionKind.NEW_DAY:
            for name, s in self.state.items():
                self.state[name] = {**self._fresh(), "in_position": s["in_position"]}

    def on_opened(self, e: PositionOpened) -> None:
        s = self.state.get(e.worker)
        if s:
            s.update(in_position=True, pending=False)
            s["trades"] += 1

    def on_closed(self, e: TradeClosed) -> None:
        s = self.state.get(e.worker)
        if s:
            s.update(in_position=False, last_exit=e.ts)

    def on_status(self, e: WorkerStatus) -> None:
        if e.worker in self.state:
            self.state[e.worker]["clocked_out"] = e.clocked_out

    def on_signal(self, sig: Signal) -> None:
        if sig.backfill:
            return  # history is for research, not for trading
        for w in self.cfg.workers:
            if not w.enabled or w.symbol != sig.symbol or sig.trigger not in w.triggers:
                continue
            reason = self._reject_reason(w, sig, self.state[w.name])
            if reason:
                self.emit(SignalSkipped(sig.ts, w.name, sig, reason))
                continue
            s = self.state[w.name]
            s["pending"] = True
            s["last_candle"] = sig.ts.replace(second=0, microsecond=0)
            self.emit(WorkerSignal(sig.ts, w.name, sig))

    def _reject_reason(self, w, sig: Signal, s: dict) -> str | None:
        ts: datetime = sig.ts
        d = ts.date()
        if cal.is_crypto() and sig.side is Side.PUT:
            return LONG_ONLY
        if s["clocked_out"]:
            return "clocked out for the day"
        if s["in_position"]:
            return "already in a trade"
        if s["pending"]:
            return "order already working"
        if s["last_candle"] == ts.replace(second=0, microsecond=0):
            return "already acted on this candle"
        if ts < cal.at(d, w.start_time) or ts >= cal.at(d, w.end_time):
            return f"outside trading window {w.start_time}-{w.end_time}"
        if s["trades"] >= w.max_trades_per_day:
            return f"max {w.max_trades_per_day} trades today"
        if s["last_exit"] and ts - s["last_exit"] < timedelta(minutes=w.cooldown_minutes):
            return f"cooling down ({w.cooldown_minutes:g} min)"
        if sig.atr and abs(sig.close - sig.level) / sig.atr < w.min_close_beyond_atr:
            return f"weak close ({abs(sig.close - sig.level) / sig.atr:.2f} ATR past level)"
        if w.trend_filter and sig.ema50 is not None and sig.vwap is not None:
            if sig.side is Side.CALL and not (sig.close > sig.ema50 and sig.close > sig.vwap):
                return "against trend (call below EMA50/VWAP)"
            if sig.side is Side.PUT and not (sig.close < sig.ema50 and sig.close < sig.vwap):
                return "against trend (put above EMA50/VWAP)"
        return None
