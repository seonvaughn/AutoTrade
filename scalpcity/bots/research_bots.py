"""Research bots — no trade on a hunch.

  key_levels     studies past sessions and marks the price levels that matter
  edge_tracker   scores every trigger on every ticker from past signals
  research_gate  lets an entry through only when the evidence supports it

The edge tracker scores signals on the *underlying*: did price move `target_atr` ATRs the
trade's way before `stop_atr` ATRs against it, within `horizon_minutes`? Only outcomes that
have fully played out by the time of a decision are counted, so there is no look-ahead.
Nothing here can promise a winning trade; it makes sure every entry has evidence behind it,
and that every refusal says why.
"""
from __future__ import annotations

from datetime import date, timedelta

from ..core import calendar as cal
from ..core.events import (CandleClosed, EntryVetoed, KeyLevel, KeyLevels, ResearchCleared, Side, Signal,
                           WorkerSignal)
from .base import Bot

BUCKET_MINUTES = 15  # turning points are found on 15-minute bars


def _lookback_start(today: date, days: int) -> date:
    d = today
    for _ in range(days):
        d = cal.prev_trading_day(d)
    return d


class KeyLevelsBot(Bot):
    name = "key_levels"
    skill = "Study past sessions and mark key levels: prior day high/low/close, multi-day range, repeated turning points"

    def setup(self) -> None:
        self.days: dict[str, dict[date, dict]] = {}   # symbol -> day -> {"h", "l", "c", "q": {bucket: [hi, lo]}}
        self.cache: dict[tuple[str, date], tuple[int, list[KeyLevel]]] = {}
        self.published: set[tuple[str, date]] = set()
        self.on(CandleClosed, self.on_candle)

    def on_candle(self, e: CandleClosed) -> None:
        c = e.candle
        d = c.start.date()
        per = self.days.setdefault(c.symbol, {})
        rec = per.get(d)
        if rec is None:
            rec = per[d] = {"h": c.high, "l": c.low, "c": c.close, "q": {}}
            for old in sorted(per)[:-(self.cfg.research.lookback_days + 2)]:
                del per[old]
        else:
            rec["h"], rec["l"], rec["c"] = max(rec["h"], c.high), min(rec["l"], c.low), c.close
        bucket = int((c.start - cal.session_open(d)).total_seconds() // (60 * BUCKET_MINUTES))
        q = rec["q"].setdefault(bucket, [c.high, c.low])
        q[0], q[1] = max(q[0], c.high), min(q[1], c.low)
        if not e.backfill and (c.symbol, d) not in self.published:
            self.published.add((c.symbol, d))
            self.emit(KeyLevels(e.ts, c.symbol, d, self.levels(c.symbol, d)))

    def past_days(self, symbol: str, day: date) -> list[date]:
        return sorted(x for x in self.days.get(symbol, {}) if x < day)[-self.cfg.research.lookback_days:]

    def levels(self, symbol: str, day: date) -> list[KeyLevel]:
        past = self.past_days(symbol, day)
        hit = self.cache.get((symbol, day))
        if hit and hit[0] == len(past):
            return hit[1]
        out = self._compute(symbol, past)
        self.cache[(symbol, day)] = (len(past), out)
        return out

    def _compute(self, symbol: str, past: list[date]) -> list[KeyLevel]:
        if not past:
            return []
        recs = [self.days[symbol][d] for d in past]
        prev = recs[-1]
        out = [KeyLevel(prev["h"], "prior day high", 1), KeyLevel(prev["l"], "prior day low", 1),
               KeyLevel(prev["c"], "prior day close", 1)]
        if len(past) > 1:
            out += [KeyLevel(max(r["h"] for r in recs), f"{len(past)}-day high", 1),
                    KeyLevel(min(r["l"] for r in recs), f"{len(past)}-day low", 1)]
        pivots: list[float] = []
        for r in recs:
            bars = [r["q"][k] for k in sorted(r["q"])]
            for i in range(1, len(bars) - 1):
                if bars[i][0] > bars[i - 1][0] and bars[i][0] > bars[i + 1][0]:
                    pivots.append(bars[i][0])
                if bars[i][1] < bars[i - 1][1] and bars[i][1] < bars[i + 1][1]:
                    pivots.append(bars[i][1])
        tol = self.cfg.research.level_merge_pct / 100.0
        clusters: list[list[float]] = []
        for p in sorted(pivots):
            if clusters and abs(p - sum(clusters[-1]) / len(clusters[-1])) <= tol * p:
                clusters[-1].append(p)
            else:
                clusters.append([p])
        for cl in clusters:
            if len(cl) >= 2:
                out.append(KeyLevel(round(sum(cl) / len(cl), 4), f"turning point ×{len(cl)}", len(cl)))
        merged: dict[float, KeyLevel] = {}  # one level per price; keep every reason it matters
        for lv in sorted(out, key=lambda x: x.price):
            key = round(lv.price, 2)
            if key in merged:
                m = merged[key]
                merged[key] = KeyLevel(m.price, f"{m.label} · {lv.label}", max(m.strength, lv.strength))
            else:
                merged[key] = lv
        return list(merged.values())


class EdgeTrackerBot(Bot):
    name = "edge_tracker"
    skill = "Score each trigger on each ticker from past signals: how often price reached target before stop"

    def setup(self) -> None:
        self.pending: list[dict] = []
        self.results: dict[tuple[str, str], list[tuple[date, str, str, float]]] = {}  # (sym, trigger) -> (day, side, outcome, R)
        self.on(Signal, self.on_signal)
        self.on(CandleClosed, self.on_candle)

    def on_signal(self, s: Signal) -> None:
        if not s.atr or s.atr <= 0:
            return
        r = self.cfg.research
        way = 1 if s.side is Side.CALL else -1
        self.pending.append({"sym": s.symbol, "trigger": s.trigger, "side": s.side.value, "day": s.ts.date(),
                             "entry": s.close, "way": way, "risk": r.stop_atr * s.atr,
                             "target": s.close + way * r.target_atr * s.atr, "stop": s.close - way * r.stop_atr * s.atr,
                             "until": s.ts + timedelta(minutes=r.horizon_minutes), "last": s.close})

    def on_candle(self, e: CandleClosed) -> None:
        c = e.candle
        keep = []
        for p in self.pending:
            if p["sym"] != c.symbol:
                keep.append(p)
                continue
            if c.start.date() != p["day"]:          # session ended before it played out
                self._record(p, "timeout", p["way"] * (p["last"] - p["entry"]) / p["risk"])
                continue
            up, down = c.high, c.low
            hit_stop = down <= p["stop"] if p["way"] > 0 else up >= p["stop"]
            hit_target = up >= p["target"] if p["way"] > 0 else down <= p["target"]
            if hit_stop:                            # both in one candle: assume the worst
                self._record(p, "loss", -1.0)
            elif hit_target:
                self._record(p, "win", self.cfg.research.target_atr / self.cfg.research.stop_atr)
            elif c.start + timedelta(minutes=1) >= p["until"]:
                self._record(p, "timeout", p["way"] * (c.close - p["entry"]) / p["risk"])
            else:
                p["last"] = c.close
                keep.append(p)
        self.pending = keep

    def _record(self, p: dict, outcome: str, r: float) -> None:
        rows = self.results.setdefault((p["sym"], p["trigger"]), [])
        rows.append((p["day"], p["side"], outcome, round(r, 3)))
        oldest = _lookback_start(p["day"], self.cfg.research.lookback_days + 1)
        if rows[0][0] < oldest:
            rows[:] = [x for x in rows if x[0] >= oldest]

    def stats(self, symbol: str, trigger: str, today: date) -> dict:
        r = self.cfg.research
        start = _lookback_start(today, r.lookback_days)
        rows = [x for x in self.results.get((symbol, trigger), []) if start <= x[0] <= today]
        n = len(rows)
        wins = sum(1 for x in rows if x[2] == "win")
        losses = sum(1 for x in rows if x[2] == "loss")
        avg_r = sum(x[3] for x in rows) / n if n else 0.0
        win_rate = wins / n if n else 0.0
        proven = n >= r.min_samples and win_rate >= r.min_win_rate and avg_r >= r.min_avg_r
        return {"symbol": symbol, "trigger": trigger, "n": n, "wins": wins, "losses": losses,
                "timeouts": n - wins - losses, "win_rate": round(win_rate, 3), "avg_r": round(avg_r, 3),
                "proven": proven, "since": start.isoformat()}


class ResearchGateBot(Bot):
    name = "research_gate"
    skill = "Let an entry through only with evidence: a proven edge for this trigger on this ticker and room to run"

    def setup(self) -> None:
        self.on(WorkerSignal, self.on_signal)

    def on_signal(self, ws: WorkerSignal) -> None:
        w = self.cfg.worker(ws.worker)
        sig = ws.signal
        if not self.cfg.research.enabled or not w.research_gate:
            self.emit(ResearchCleared(ws.ts, ws.worker, sig, {"gate": "off"}))
            return
        evidence, reason = self.check(sig)
        if reason:
            self.emit(EntryVetoed(ws.ts, ws.worker, sig, reason, evidence))
        else:
            self.emit(ResearchCleared(ws.ts, ws.worker, sig, evidence))

    def check(self, sig: Signal) -> tuple[dict, str | None]:
        r = self.cfg.research
        day = sig.ts.date()
        edge = self.bot("edge_tracker").stats(sig.symbol, sig.trigger, day)
        levels = list(self.bot("key_levels").levels(sig.symbol, day))
        hi, lo, locked = self.bot("opening_range").range(sig.symbol)
        if locked:
            levels += [KeyLevel(hi, "opening range high", 1), KeyLevel(lo, "opening range low", 1)]
        htf = self.bot("htf_levels")
        if htf:
            levels += htf.study(sig.symbol, day)["levels"]
        zones = self.bot("zones")
        # opposing zones are obstacles: supply above a CALL, demand below a PUT
        inside = None
        for z in (zones.zones(sig.symbol) if zones else []):
            opposing = (sig.side is Side.CALL and z["kind"] == "supply") or (sig.side is Side.PUT and z["kind"] == "demand")
            if not opposing:
                continue
            if z["lo"] <= sig.close <= z["hi"]:
                inside = z
            elif sig.side is Side.CALL and z["lo"] > sig.close:
                levels.append(KeyLevel(z["lo"], f"{z['tf']} supply zone", 2))
            elif sig.side is Side.PUT and z["hi"] < sig.close:
                levels.append(KeyLevel(z["hi"], f"{z['tf']} demand zone", 2))
        st = self.bot("structure")
        trends = {tf: st.trend(sig.symbol, tf, day) for tf in r.align_timeframes} if st else {}
        ev: dict = {"edge": edge, "levels_studied": len(levels), "trend": trends}
        if not sig.atr:
            return ev, "not enough data yet (ATR still warming up)"
        if edge["n"] < r.min_samples:
            return ev, (f"not proven: only {edge['n']} past {sig.trigger} signals on {sig.symbol} in "
                        f"{r.lookback_days} sessions (need {r.min_samples})")
        if edge["win_rate"] < r.min_win_rate or edge["avg_r"] < r.min_avg_r:
            return ev, (f"no edge: {sig.trigger} on {sig.symbol} won {edge['wins']}/{edge['n']} "
                        f"({edge['win_rate']:.0%}), avg {edge['avg_r']:+.2f}R over {r.lookback_days} sessions")
        against = "bearish" if sig.side is Side.CALL else "bullish"
        bad = [tf for tf, t in trends.items() if t == against]
        if bad:
            return ev, f"against the {', '.join(bad)} trend ({against})"
        if inside:
            return ev, f"inside a {inside['tf']} {inside['kind']} zone ({inside['lo']:,.2f}-{inside['hi']:,.2f})"
        if sig.side is Side.CALL:
            ahead = [lv for lv in levels if lv.price > sig.close]
            nxt = min(ahead, key=lambda lv: lv.price) if ahead else None
        else:
            ahead = [lv for lv in levels if lv.price < sig.close]
            nxt = max(ahead, key=lambda lv: lv.price) if ahead else None
        if nxt is not None:
            room = abs(nxt.price - sig.close) / sig.atr
            ev["next_level"] = {"price": nxt.price, "label": nxt.label, "room_atr": round(room, 2)}
            if room < r.min_room_atr:
                return ev, f"blocked by {nxt.label} at {nxt.price:,.2f}, only {room:.1f} ATR away"
        return ev, None
