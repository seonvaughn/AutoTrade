"""Records & reporting: Ledger (money), Journal (the bots' "THOUGHTS"), Analyst (stats)."""
from __future__ import annotations

from datetime import date

from ..core.events import (DailySummary, EntryVetoed, KeyLevels, ResearchCleared, Fill, KillSwitch, Leaderboard, OptionQuote, OrderRejected, OrderSide,
                           PnLUpdate, PositionOpened, Purpose, SessionEvent, SessionKind, SetupUpdate, SignalSkipped,
                           ContractRejected, Thought, TradeClosed, WorkerStats, WorkerStatus)
from ..core.costs import QTY_EPS, fmt_qty
from .base import Bot
from .signal_filter_bot import LONG_ONLY

TRIGGER_LABEL = {"vwap_cross": "VWAP", "ema50_cross": "EMA50", "orb": "opening range",
                 "zone_reaction": "supply/demand zone", "structure_break": "5m structure break",
                 "fib_pullback": "Fibonacci pullback", "smc_retrace": "TJR sweep + break + retrace",
                 "smc_bos": "TJR sweep + break"}

WHY = {"vwap_cross": "VWAP cross", "ema50_cross": "EMA50 cross", "orb": "range breakout",
       "zone_reaction": "bounce off a supply/demand zone", "structure_break": "5m break of structure",
       "fib_pullback": "Fibonacci pullback in the 15m trend",
       "smc_retrace": "liquidity sweep, break of structure, retrace into an order block / gap, lower-timeframe break",
       "smc_bos": "liquidity sweep then break of structure"}


def money(x: float) -> str:
    return f"{'+' if x >= 0 else '-'}${abs(x):,.0f}"


class LedgerBot(Bot):
    name = "ledger"
    skill = "Book every fill; track positions, realized and unrealized P&L per worker and the Vault"

    def setup(self) -> None:
        self.pos: dict[str, dict] = {}
        self.realized: dict[str, float] = {}
        self.unrealized: dict[str, float] = {}
        self.on(Fill, self.on_fill)
        self.on(OptionQuote, self.on_quote)
        self.on(SessionEvent, self.on_session)

    def holdings(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for p in self.pos.values():
            out[p["contract"].occ] = out.get(p["contract"].occ, 0) + p["qty"]
        return out

    def vault(self) -> float:
        return sum(self.realized.values()) + sum(self.unrealized.values())

    def _pnl(self, worker: str, ts) -> None:
        self.emit(PnLUpdate(ts, worker, self.realized.get(worker, 0.0), self.unrealized.get(worker, 0.0), self.vault()))

    def on_fill(self, f: Fill) -> None:
        it = f.intent
        self.ctx.storage.add_fill(f.ts, it.worker, it.contract.occ, it.side.value, it.purpose.value, f.qty, f.price,
                                  f.fees, f.order_id)
        p = self.pos.get(it.worker)
        if it.side is OrderSide.BUY:
            if p is None:
                p = self.pos[it.worker] = {"contract": it.contract, "qty": 0, "avg": 0.0, "fees": 0.0,
                                           "opened": f.ts, "orig": 0, "pnl": 0.0, "exit_notional": 0.0,
                                           "signal": it.signal}
            p["avg"] = (p["avg"] * p["qty"] + f.price * f.qty) / (p["qty"] + f.qty)
            p["qty"] += f.qty
            p["orig"] += f.qty
            p["fees"] += f.fees
            self.emit(PositionOpened(f.ts, it.worker, it.contract, p["qty"], p["avg"], it.signal))
            return
        if p is None:
            self.log.error("sell fill for %s with no position", it.worker)
            return
        entry_fees = p["fees"] * f.qty / p["qty"]
        p["fees"] -= entry_fees
        part = (f.price - p["avg"]) * f.qty * it.contract.multiplier - f.fees - entry_fees
        p["pnl"] += part
        p["exit_notional"] += f.price * f.qty
        p["qty"] -= f.qty
        self.realized[it.worker] = self.realized.get(it.worker, 0.0) + part
        if p["qty"] <= QTY_EPS:
            del self.pos[it.worker]
            self.unrealized[it.worker] = 0.0
            exit_px = p["exit_notional"] / p["orig"]
            self.ctx.storage.add_trade(f.ts, p["opened"], it.worker, it.contract.occ, p["orig"], p["avg"], exit_px,
                                       round(p["pnl"], 2), it.reason)
            self.emit(TradeClosed(f.ts, it.worker, it.contract, p["orig"], p["avg"], exit_px, round(p["pnl"], 2),
                                  it.reason, p["opened"]))
        self._pnl(it.worker, f.ts)

    def on_quote(self, q: OptionQuote) -> None:
        for worker, p in self.pos.items():
            if p["contract"] == q.contract:
                u = (q.mid - p["avg"]) * p["qty"] * q.contract.multiplier
                if abs(u - self.unrealized.get(worker, 0.0)) >= 0.5:
                    self.unrealized[worker] = u
                    self._pnl(worker, q.ts)

    def on_session(self, e: SessionEvent) -> None:
        if e.kind is SessionKind.NEW_DAY:
            self.realized.clear()
            self.unrealized = {w: v for w, v in self.unrealized.items() if w in self.pos}


class JournalBot(Bot):
    name = "journal"
    skill = "Write each worker's readable THOUGHTS log (what it saw, did, and why)"

    def setup(self) -> None:
        self.armed: dict[tuple[str, str], bool] = {}
        self.busy: set[str] = set()
        self.on(SetupUpdate, self.on_setup)
        self.on(SignalSkipped, self.on_skipped)
        self.on(ContractRejected, lambda e: self.say(e.ts, e.worker, f"passed on {e.signal.side.arrow} {e.signal.side.value}: {e.reason}", "bad"))
        self.on(OrderRejected, lambda e: e.intent.purpose is Purpose.ENTRY and self.say(e.ts, e.intent.worker, f"order blocked: {e.reason}", "bad"))
        self.on(PositionOpened, self.on_opened)
        self.on(TradeClosed, self.on_closed)
        self.on(WorkerStatus, self.on_status)
        self.on(KillSwitch, self.on_kill)
        self.on(KeyLevels, self.on_levels)
        self.on(EntryVetoed, self.on_vetoed)
        self.on(ResearchCleared, self.on_cleared)

    def on_levels(self, e: KeyLevels) -> None:
        if not e.levels:
            text = "📚 no past sessions to study yet — research gate will hold entries"
        else:
            key = ", ".join(f"{lv.label} {lv.price:,.2f}" for lv in e.levels
                            if lv.label.startswith(("prior day", f"{self.cfg.research.lookback_days}-day")))
            text = f"📚 studied past sessions: {len(e.levels)} levels marked ({key})"
        for w in self._symbol_workers(e.symbol):
            self.say(e.ts, w, text)

    def on_vetoed(self, e: EntryVetoed) -> None:
        s = e.signal
        self.say(e.ts, e.worker, f"🔎 no trade {s.side.arrow} {s.side.value} ({TRIGGER_LABEL[s.trigger]}): {e.reason}", "bad")

    def on_cleared(self, e: ResearchCleared) -> None:
        edge = e.evidence.get("edge")
        if not edge:
            return
        room = e.evidence.get("next_level")
        where = f"; {room['room_atr']:.1f} ATR to {room['label']}" if room else "; no level in the way"
        self.say(e.ts, e.worker, f"🔎 evidence ok: {TRIGGER_LABEL[e.signal.trigger]} won {edge['wins']}/{edge['n']} "
                                 f"({edge['win_rate']:.0%}), {edge['avg_r']:+.2f}R{where}", "good")

    def _symbol_workers(self, symbol: str):
        return [w.name for w in self.cfg.workers if w.enabled and w.symbol == symbol]

    def say(self, ts, worker: str, text: str, tone: str = "info") -> None:
        self.ctx.storage.add_thought(ts, worker, text, tone)
        self.emit(Thought(ts, worker, text, tone))

    def _workers(self, symbol: str, trigger: str):
        return [w.name for w in self.cfg.workers if w.enabled and w.symbol == symbol and trigger in w.triggers]

    def on_setup(self, e: SetupUpdate) -> None:
        key = (e.symbol, e.trigger)
        armed = self.armed.get(key, False)
        label = TRIGGER_LABEL[e.trigger]
        if not armed and e.charge >= 70:
            self.armed[key] = True
            for w in self._workers(e.symbol, e.trigger):
                if w not in self.busy:
                    self.say(e.ts, w, f"setup forming: {e.side.arrow} {e.side.value} at {label}, {e.distance_atr:.2f} ATR")
        elif armed and e.charge < 20:
            self.armed[key] = False
            for w in self._workers(e.symbol, e.trigger):
                if w not in self.busy:
                    self.say(e.ts, w, "setup faded, standing down")

    def on_skipped(self, e: SignalSkipped) -> None:
        if e.reason in {"already in a trade", "clocked out for the day", "order already working", LONG_ONLY} \
                or e.reason.startswith("outside trading window"):
            return
        s = e.signal
        self.say(e.ts, e.worker, f"skipped {s.side.arrow} {s.side.value} ({TRIGGER_LABEL[s.trigger]}): {e.reason}", "bad")

    def on_opened(self, e: PositionOpened) -> None:
        self.busy.add(e.worker)
        s = e.signal
        why = f" · {WHY.get(s.trigger, TRIGGER_LABEL[s.trigger])}" if s else ""
        if e.contract.kind == "crypto":
            text = f"FIRE ▲ BUY {fmt_qty(e.qty)} {e.contract.underlying} @ {e.entry_price:,.2f}{why}"
        else:
            under = f" ({e.contract.underlying} {s.close:.2f})" if s else ""
            text = f"FIRE {e.contract.right.arrow} {e.contract.right.value} ×{e.qty:g} @ {e.entry_price:.2f}{under}{why}"
        self.say(e.ts, e.worker, text, "fire")
        for key in list(self.armed):
            if key[0] == e.contract.underlying:
                self.armed[key] = False

    def on_closed(self, e: TradeClosed) -> None:
        self.busy.discard(e.worker)
        lock = "🔒 profit locked" if e.pnl >= 0 else "🔒 trailing stop gapped through"
        label = {"profit_lock": lock, "target": "🎯 target hit", "stop": "🛑 stopped out",
                 "time": "⏱ time stop", "reversal": "↩ reversal exit", "end_of_day": "🔔 end-of-day exit",
                 "kill": "⛔ kill-switch exit"}.get(e.reason, e.reason)
        self.say(e.ts, e.worker, f"{label} {money(e.pnl)}", "good" if e.pnl >= 0 else "bad")

    def on_status(self, e: WorkerStatus) -> None:
        if e.clocked_out and e.reason == "daily goal":
            self.say(e.ts, e.worker, f"🏆 daily goal {money(e.day_pnl)} · clocking out", "goal")
        elif e.clocked_out:
            self.say(e.ts, e.worker, f"{e.reason} {money(e.day_pnl)} · clocking out", "bad")
        else:
            self.say(e.ts, e.worker, "back on shift")

    def on_kill(self, e: KillSwitch) -> None:
        for w in self.cfg.workers:
            if w.enabled:
                self.say(e.ts, w.name, f"{'⛔ KILL SWITCH ON' if e.engaged else 'kill switch released'}: {e.reason}",
                         "bad" if e.engaged else "info")


class AnalystBot(Bot):
    name = "analyst"
    skill = "Leaderboard, win rate, expectancy, drawdown, end-of-day summary"

    def setup(self) -> None:
        names = [w.name for w in self.cfg.workers if w.enabled]
        self.run = {n: WorkerStats(n) for n in names}
        self.day = {n: WorkerStats(n) for n in names}
        self.summaries: list[DailySummary] = []
        self.blocked: dict[str, int] = {}
        self.on(TradeClosed, self.on_closed)
        self.on(SessionEvent, self.on_session)
        self.on(OrderRejected, lambda e: e.intent.purpose is Purpose.ENTRY and self._block(e.reason))
        self.on(ContractRejected, lambda e: self._block(e.reason))
        self.on(EntryVetoed, lambda e: self._block("research: " + e.reason.split(":")[0]))

    def _block(self, reason: str) -> None:
        key = reason.split("(")[0].split(":")[0].split("$")[0].strip()
        self.blocked[key] = self.blocked.get(key, 0) + 1

    @staticmethod
    def _add(s: WorkerStats, pnl: float) -> None:
        s.trades += 1
        s.pnl += pnl
        if pnl > 0:
            s.wins += 1
            s.gross_win += pnl
        else:
            s.losses += 1
            s.gross_loss += -pnl
        s.peak = max(s.peak, s.pnl)
        s.max_drawdown = max(s.max_drawdown, s.peak - s.pnl)

    def on_closed(self, e: TradeClosed) -> None:
        self._add(self.run[e.worker], e.pnl)
        self._add(self.day[e.worker], e.pnl)
        self.emit(Leaderboard(e.ts, sorted(self.day.values(), key=lambda s: -s.pnl)))

    def on_session(self, e: SessionEvent) -> None:
        if e.kind is SessionKind.NEW_DAY:
            self.day = {n: WorkerStats(n) for n in self.day}
            self.emit(Leaderboard(e.ts, list(self.day.values())))
        elif e.kind is SessionKind.CLOSED:
            self.close_day(e.ts, e.day)

    def close_day(self, ts, day: date) -> None:
        by = {n: round(s.pnl, 2) for n, s in self.day.items()}
        for n, s in self.day.items():
            self.ctx.storage.set_daily(day, n, s.pnl, s.trades, s.wins)
        top = max(by, key=by.get) if by and max(by.values()) > 0 else None
        summary = DailySummary(ts, day, round(sum(by.values()), 2), by, sum(s.trades for s in self.day.values()),
                               sum(s.wins for s in self.day.values()), top)
        self.summaries.append(summary)
        self.emit(summary)

    def report(self) -> dict:
        totals = [s.total for s in self.summaries]
        equity, peak, dd = 0.0, 0.0, 0.0
        for t in totals:
            equity += t
            peak = max(peak, equity)
            dd = max(dd, peak - equity)
        trades = sum(s.trades for s in self.run.values())
        wins = sum(s.wins for s in self.run.values())
        gw = sum(s.gross_win for s in self.run.values())
        gl = sum(s.gross_loss for s in self.run.values())
        return {
            "days": len(totals),
            "net_pnl": round(sum(totals), 2),
            "green_days": sum(1 for t in totals if t > 0),
            "red_days": sum(1 for t in totals if t < 0),
            "best_day": round(max(totals), 2) if totals else 0,
            "worst_day": round(min(totals), 2) if totals else 0,
            "max_drawdown": round(dd, 2),
            "trades": trades,
            "win_rate": round(wins / trades, 3) if trades else 0,
            "profit_factor": round(gw / gl, 2) if gl else None,
            "avg_trade": round(sum(totals) / trades, 2) if trades else 0,
            "workers": {n: {"trades": s.trades, "win_rate": round(s.win_rate, 3), "pnl": round(s.pnl, 2),
                            "expectancy": round(s.expectancy, 2), "max_drawdown": round(s.max_drawdown, 2)}
                        for n, s in self.run.items()},
            "daily": [{"day": s.day.isoformat(), "pnl": s.total, "trades": s.trades, "top": s.top_worker}
                      for s in self.summaries],
            "blocked_entries": dict(sorted(self.blocked.items(), key=lambda kv: -kv[1])),
        }
