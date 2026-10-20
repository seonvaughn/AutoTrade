"""Learning bots: review every trade, and keep a lessons book that turns repeated evidence into rules.

  trade_review   after each trade: what went right (wins) or what went wrong (losses), classified from what the
                 stock actually did: target reached, setup failed (the swept high/low broke), stop too tight
                 (stopped, then the target was reached the same day), out of time, or the option lost money
                 although the stock behaved (contract costs)
  lessons        every scored setup and every reviewed trade, tallied by feature (ticker, hour, side, zone,
                 timeframes, with/against the daily bias). A feature that keeps losing, over enough cases to be
                 sure, becomes an "avoid" rule the research gate enforces; a reliable winner becomes "favor".
                 Rules are re-checked as results come in, so a lesson that stops being true is dropped.

One trade proves nothing, so no rule comes from a single loss: a lesson needs `research.lessons_min_n` cases and a
t-statistic beyond `research.lessons_t`. The book is saved to `research.lessons_path` and survives restarts.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from ..core.events import (PositionOpened, SessionEvent, SessionKind, SetupScored, Side, Tick, TradeClosed,
                           TradeReview)
from .base import Bot
from .research_bots import features_of

FEATURES = ("ticker", "side", "trigger", "hour", "weekday", "setup_tf", "sweep_tf", "zone", "vs_daily_bias")


class TradeReviewBot(Bot):
    name = "trade_review"
    skill = "Review every closed trade: what went right on wins, what went wrong on losses, from what the stock did"

    def setup(self) -> None:
        self.open: dict[str, dict] = {}        # worker -> what the trade planned and what the stock did
        self.watch: list[dict] = []            # stopped-out trades: did the stock reach the target later today?
        self.on(PositionOpened, self.on_opened)
        self.on(Tick, self.on_tick)
        self.on(TradeClosed, self.on_closed)
        self.on(SessionEvent, self.on_session)

    def on_opened(self, e: PositionOpened) -> None:
        s = e.signal
        if s is None:
            return
        way = 1 if s.side is Side.CALL else -1
        self.open[e.worker] = {"signal": s, "way": way, "entry": s.close, "best": 0.0, "worst": 0.0,
                               "reached_target": False, "features": features_of(self, s), "opened": e.ts,
                               "contract": e.contract}

    def on_tick(self, t: Tick) -> None:
        for rec in list(self.open.values()) + self.watch:
            s = rec["signal"]
            if s.symbol != t.symbol:
                continue
            move = rec["way"] * (t.price - rec["entry"])
            rec["best"], rec["worst"] = max(rec["best"], move), min(rec["worst"], move)
            if s.target is not None and rec["way"] * (t.price - s.target) >= 0:
                rec["reached_target"] = True
        done = [w for w in self.watch if w["reached_target"]]
        for rec in done:                       # stopped out, then the plan's target printed: the stop was too tight
            self.watch.remove(rec)
            self._review(rec, "stop_too_tight", t.ts)

    def on_closed(self, e: TradeClosed) -> None:
        rec = self.open.pop(e.worker, None)
        if rec is None:
            return
        rec.update(worker=e.worker, pnl=e.pnl, reason=e.reason, closed=e.ts, exit=e.exit_price,
                   entry_px=e.entry_price, qty=e.qty)
        s = rec["signal"]
        if e.pnl > 0:
            self._review(rec, "target" if e.reason == "target" else f"won_on_{e.reason}", e.ts)
        elif rec["reached_target"]:
            self._review(rec, "option_costs", e.ts)  # the stock got there; the contract still lost
        elif e.reason == "stop" and s.target is not None:
            self.watch.append(rec)                    # decide at the close: setup failed, or stop too tight?
        elif e.reason in ("time", "end_of_day"):
            self._review(rec, "out_of_time", e.ts)
        else:
            self._review(rec, f"lost_on_{e.reason}", e.ts)

    def on_session(self, e: SessionEvent) -> None:
        if e.kind in (SessionKind.CLOSED, SessionKind.NEW_DAY):
            for rec in self.watch:
                self._review(rec, "setup_failed", e.ts)
            self.watch.clear()

    def _review(self, rec: dict, verdict: str, ts) -> None:
        s, f = rec["signal"], rec["features"]
        risk = abs(s.close - s.stop) if s.stop is not None else None
        r = (lambda x: f"{x / risk:+.2f}R" if risk else f"{x:+.2f}")
        mins = int((rec["closed"] - rec["opened"]).total_seconds() // 60)
        what = (f"{f.get('ticker')} {s.side.value} · {f.get('trigger')} · {f.get('vs_daily_bias', '?')} the daily bias · "
                f"{f.get('setup_tf', '?')} setup, {f.get('sweep_tf', '?')} sweep, {f.get('zone', '?')} · {f.get('hour')}")
        money = f"${rec['pnl']:+,.0f} in {mins} min (stock best {r(rec['best'])}, worst {r(rec['worst'])})"
        won = rec["pnl"] > 0
        if won:
            text = (f"✅ WIN review: {what}. What went right: the setup held and the stock moved the planned way "
                    f"({verdict.replace('_', ' ')}); the contract kept the move. {money}.")
        else:
            why = {
                "setup_failed": "the setup failed: price closed through the swept high/low (the stop's invalidation "
                                "level) and never reached the target today. The read was wrong, not the stop",
                "stop_too_tight": "the stop was too tight: after stopping out, price went on to the plan's target "
                                  "the same day. The read was right; the stop sat inside normal noise",
                "option_costs": "the stock reached the target but the contract still lost: spread and time decay "
                                "ate the move. The contract choice was the problem",
                "out_of_time": "out of time: neither stop nor target was reached; the move never came",
            }.get(verdict, verdict.replace("_", " "))
            text = f"❌ LOSS review: {what}. What went wrong: {why}. {money}."
        self.emit(TradeReview(ts, rec["worker"], won, verdict, text, dict(f)))


class LessonsBot(Bot):
    name = "lessons"
    skill = "Keep the lessons book: tally every setup and trade by feature; turn repeated losers into avoid rules"

    def setup(self) -> None:
        r = self.cfg.research
        self.path = Path(r.lessons_path) if r.lessons_path else None
        self.stats: dict[str, list[float]] = {}     # "feature=value" -> [n, sum R, sum R^2]
        self.verdicts: dict[str, int] = {}
        self.seen: set[str] = set()
        self._load()
        self.on(SetupScored, self.on_scored)
        self.on(TradeReview, self.on_review)
        self.on(SessionEvent, lambda e: e.kind is SessionKind.CLOSED and self._save())

    def _load(self) -> None:
        if self.path and self.path.exists():
            data = json.loads(self.path.read_text())
            self.stats = {k: list(v) for k, v in data.get("stats", {}).items()}
            self.verdicts = data.get("verdicts", {})
            self.seen = set(data.get("seen", []))

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"stats": self.stats, "verdicts": self.verdicts,
                                         "seen": sorted(self.seen)[-20000:], "lessons": self.lessons()}, indent=1))

    def on_scored(self, e: SetupScored) -> None:
        if not e.plan:
            return                                  # learn from the setups the plan would actually take
        key = f"{e.symbol}|{e.trigger}|{e.ts.isoformat()}"
        if key in self.seen:                        # history replayed again after a restart: count once
            return
        self.seen.add(key)
        for name in FEATURES:
            if e.features.get(name) is not None:
                st = self.stats.setdefault(f"{name}={e.features[name]}", [0, 0.0, 0.0])
                st[0] += 1
                st[1] += e.r
                st[2] += e.r * e.r

    def on_review(self, e: TradeReview) -> None:
        self.verdicts[e.verdict] = self.verdicts.get(e.verdict, 0) + 1

    def lessons(self) -> list[dict]:
        r = self.cfg.research
        out = []
        for key, (n, s, ss) in self.stats.items():
            if n < r.lessons_min_n:
                continue
            mean = s / n
            var = max(ss / n - mean * mean, 1e-9) * n / (n - 1)
            t = mean / math.sqrt(var / n)
            if abs(t) >= r.lessons_t:
                feature, value = key.split("=", 1)
                out.append({"feature": feature, "value": value, "n": int(n), "avg_r": round(mean, 3),
                            "t": round(t, 2), "kind": "avoid" if t < 0 else "favor"})
        return sorted(out, key=lambda x: x["t"])

    def check(self, features: dict) -> Optional[str]:
        """An avoid rule that matches this setup, or None."""
        for les in self.lessons():
            if les["kind"] == "avoid" and str(features.get(les["feature"])) == les["value"]:
                return (f"lesson learned: setups with {les['feature']} = {les['value']} lost "
                        f"{les['avg_r']:+.2f}R on average over {les['n']} cases (t {les['t']:+.1f})")
        return None

