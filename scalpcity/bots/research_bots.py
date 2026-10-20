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
from ..core.events import (CandleClosed, EntryVetoed, KeyLevel, KeyLevels, ResearchCleared, SetupScored, Side,
                           Signal, WorkerSignal)
from ..core.config import PLANNED_TRIGGERS, SMC_TRIGGERS
from .base import Bot

BUCKET_MINUTES = 15  # turning points are found on 15-minute bars


def wanted_bias(cfg, side: Side) -> str | None:
    """The daily bias an entry on `side` needs under smc.bias_mode (None: any direction)."""
    with_trend = "bullish" if side is Side.CALL else "bearish"
    mode = cfg.smc.bias_mode
    if mode == "any":
        return None
    return with_trend if mode == "with" else ("bearish" if with_trend == "bullish" else "bullish")


def features_of(bot, s: Signal) -> dict:
    """What a setup looked like when it fired: the facts the lessons book learns from (no outcomes)."""
    setup = s.setup or {}
    f = {"ticker": s.symbol, "side": s.side.value, "trigger": s.trigger,
         "hour": f"{s.ts:%H}:00-{s.ts.hour + 1:02d}:00", "weekday": f"{s.ts:%A}"}
    if setup:
        f["setup_tf"] = setup.get("setup_tf")
        f["sweep_tf"] = (setup.get("sweep") or {}).get("tf") or "none"
        poi = setup.get("poi") or []
        f["zone"] = ("order block + gap" if any("order" in x for x in poi) and any("gap" in x for x in poi)
                     else "order block" if any("order" in x for x in poi) else "gap" if poi else "none")
    db = bot.bot("daily_bias")
    if db:
        d = db.bias(s.symbol, s.ts.date())["D"]
        trend = "bullish" if s.side is Side.CALL else "bearish"
        f["vs_daily_bias"] = "unknown" if d == "unknown" else ("with" if d == trend else "against")
    return f


def edge_days(cfg, trigger: str) -> int:
    r = cfg.research
    return r.edge_lookback_days if trigger in PLANNED_TRIGGERS and r.edge_lookback_days else r.lookback_days


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
        if s.stop is not None and s.target is not None:   # the trade the chart planned: its own stop and target
            risk = abs(s.close - s.stop)
            if risk <= 0 or way * (s.target - s.close) <= 0:
                return
            p = {"risk": risk, "target": s.target, "stop": s.stop, "win_r": abs(s.target - s.close) / risk,
                 "until": s.ts + timedelta(minutes=self.cfg.smc.horizon_minutes)}
        else:
            p = {"risk": r.stop_atr * s.atr, "target": s.close + way * r.target_atr * s.atr,
                 "stop": s.close - way * r.stop_atr * s.atr, "win_r": r.target_atr / r.stop_atr,
                 "until": s.ts + timedelta(minutes=r.horizon_minutes)}
        p.update(sym=s.symbol, trigger=s.trigger, side=s.side.value, day=s.ts.date(), entry=s.close, way=way,
                 last=s.close, plan=self.in_plan(s), ts=s.ts, features=features_of(self, s))
        self.pending.append(p)

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
                self._record(p, "win", p["win_r"])
            elif c.start + timedelta(minutes=1) >= p["until"]:
                self._record(p, "timeout", p["way"] * (c.close - p["entry"]) / p["risk"])
            else:
                p["last"] = c.close
                keep.append(p)
        self.pending = keep

    def in_plan(self, s: Signal) -> bool:
        """Would the trading plan have taken this chart-planned setup? With the daily bias, inside a worker's
        trading window, not on a news blackout (TJR Days 19, 29, 34). Those are the setups whose record counts."""
        if s.stop is None:
            return True
        news = self.bot("news_calendar")
        if news and news.blocked(s.ts):
            return False
        d = s.ts.date()
        if not any(w.enabled and w.symbol == s.symbol and s.trigger in w.triggers
                   and cal.at(d, w.start_time) <= s.ts < cal.at(d, w.end_time) for w in self.cfg.workers):
            return False
        if s.trigger not in SMC_TRIGGERS:
            return True                               # the opening range needs no daily bias (the video's rule)
        db = self.bot("daily_bias")
        bias = db.bias(s.symbol, d)["D"] if db else "unknown"
        if self.cfg.smc.require_daily_bias and bias == "unknown":
            return False
        want = wanted_bias(self.cfg, s.side)
        return want is None or bias == want

    def _record(self, p: dict, outcome: str, r: float) -> None:
        if "ts" in p:
            self.emit(SetupScored(p["ts"], p["sym"], p["trigger"], Side(p["side"]), outcome, round(r, 3),
                                  p["features"], p.get("plan", True)))
        rows = self.results.setdefault((p["sym"], p["trigger"]), [])
        rows.append((p["day"], p["side"], outcome, round(r, 3), p.get("plan", True)))
        oldest = _lookback_start(p["day"], edge_days(self.cfg, p["trigger"]) + 1)
        if rows[0][0] < oldest:
            rows[:] = [x for x in rows if x[0] >= oldest]

    def stats(self, symbol: str, trigger: str, today: date) -> dict:
        r = self.cfg.research
        start = _lookback_start(today, edge_days(self.cfg, trigger))
        if trigger in r.pooled_triggers:             # one model, every market: score all tickers together
            pool = [x for (_, t), xs in self.results.items() if t == trigger for x in xs]
        else:
            pool = self.results.get((symbol, trigger), [])
        rows = [x for x in pool if start <= x[0] <= today and (len(x) < 5 or x[4])]  # only setups the plan would have taken
        n = len(rows)
        wins = sum(1 for x in rows if x[2] == "win")
        losses = sum(1 for x in rows if x[2] == "loss")
        avg_r = sum(x[3] for x in rows) / n if n else 0.0
        win_rate = wins / n if n else 0.0
        # Chart-planned triggers carry their own reward:risk, so a low win rate can still pay: they are judged
        # on expectancy (average R per setup). The indicator triggers keep the win-rate bar too.
        planned = trigger in PLANNED_TRIGGERS
        proven = n >= r.min_samples and avg_r >= r.min_avg_r and (planned or win_rate >= r.min_win_rate)
        return {"symbol": symbol, "trigger": trigger, "n": n, "wins": wins, "losses": losses,
                "timeouts": n - wins - losses, "win_rate": round(win_rate, 3), "avg_r": round(avg_r, 3),
                "proven": proven, "since": start.isoformat(), "pooled": trigger in r.pooled_triggers,
                "judged_on": "expectancy" if planned else "win rate and expectancy"}


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
        if not reason:
            evidence, reason = self.check_tjr(sig, evidence)
        if reason:
            self.emit(EntryVetoed(ws.ts, ws.worker, sig, reason, evidence))
        else:
            self.emit(ResearchCleared(ws.ts, ws.worker, sig, evidence))

    def check(self, sig: Signal) -> tuple[dict, str | None]:
        r = self.cfg.research
        day = sig.ts.date()
        edge = self.bot("edge_tracker").stats(sig.symbol, sig.trigger, day)
        levels = list(self.bot("key_levels").levels(sig.symbol, day))
        orng = self.bot("opening_range")
        hi, lo, locked = orng.range(sig.symbol) if orng else (None, None, False)
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
                        f"{edge_days(self.cfg, sig.trigger)} sessions (need {r.min_samples})")
        if not edge["proven"]:
            return ev, (f"no edge: {sig.trigger} on {sig.symbol} won {edge['wins']}/{edge['n']} "
                        f"({edge['win_rate']:.0%}), avg {edge['avg_r']:+.2f}R over {edge_days(self.cfg, sig.trigger)} sessions")
        against = "bearish" if sig.side is Side.CALL else "bullish"
        bad = [tf for tf, t in trends.items() if t == against and sig.stop is None]
        if bad:
            return ev, f"against the {', '.join(bad)} trend ({against})"
        if inside and sig.stop is None:              # TJR setups bring their own zones (order blocks, gaps)
            return ev, f"inside a {inside['tf']} {inside['kind']} zone ({inside['lo']:,.2f}-{inside['hi']:,.2f})"
        if sig.target is not None:
            return ev, None                           # chart-planned trades: reward:risk is judged in check_tjr
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

    def _trend(self, symbol: str, tf: str) -> str:
        ms = self.bot("market_structure")
        return ms.trend(symbol, tf) if ms else "unknown"

    def check_tjr(self, sig: Signal, ev: dict) -> tuple[dict, str | None]:
        """The boot camp rules that apply to every entry: no news days (Day 19); for the chart-planned TJR
        models also the daily bias (Day 34) and the planned reward:risk (Day 37)."""
        news = self.bot("news_calendar")
        why = news.blocked(sig.ts) if news else None
        if why:
            return ev, why
        if sig.stop is None:
            return ev, None
        ms = self.bot("morning_study")
        plan = ms.plan(sig.symbol, sig.ts.date()) if ms else None
        if plan is None:
            return ev, "no morning study for today yet: nothing trades before it"
        ev["morning"] = {"cleared": plan.cleared, "reasons": plan.reasons}
        if not plan.cleared:
            return ev, "stood down at the morning study: " + "; ".join(plan.reasons)
        lessons = self.bot("lessons")
        lesson = lessons.check(features_of(self, sig)) if lessons else None
        if lesson:
            return ev, lesson
        m = self.cfg.smc
        if sig.trigger not in SMC_TRIGGERS:           # opening range: no daily bias rule; judge the plan's reward
            return self._reward(sig, ev)
        db = self.bot("daily_bias")
        bias = db.bias(sig.symbol, sig.ts.date()) if db else {"D": "unknown"}
        ev["daily_bias"] = bias
        ev["setup"] = sig.setup
        want = wanted_bias(self.cfg, sig.side)
        setup = "bullish" if sig.side is Side.CALL else "bearish"
        if m.require_daily_bias and bias["D"] == "unknown":
            return ev, f"no daily bias yet (needs daily candles), this is a {setup} setup"
        if want is not None and bias["D"] != want:
            rule = "with" if m.bias_mode == "with" else "against"
            return ev, f"daily bias is {bias['D']}: the plan trades {rule} the daily bias, this is a {setup} setup"
        against = [] if m.bias_mode != "with" else \
            [tf for tf in ("4h", "1h") if self._trend(sig.symbol, tf) == ("bearish" if want == "bullish" else "bullish")]
        setup_tf = (sig.setup or {}).get("setup_tf", "5m")
        if against:          # the lower timeframes are retracing the daily: only fade it from the right place
            if setup_tf in ("1m", "5m"):
                return ev, (f"the {' and '.join(against)} trend opposes the daily bias: needs a 15m setup, "
                            f"this one is {setup_tf} (Day 35)")
            rng = bias.get("D_range")
            half = "premium" if want == "bearish" else "discount"
            if not rng:
                return ev, f"the {' and '.join(against)} trend opposes the daily bias and the daily range is unknown"
            if (want == "bearish" and sig.close < rng["eq"]) or (want == "bullish" and sig.close > rng["eq"]):
                return ev, (f"the {' and '.join(against)} trend opposes the daily bias and price isn't in the daily "
                            f"{half} yet (equilibrium {rng['eq']:,.2f}, Day 36)")
        return self._reward(sig, ev)

    def _reward(self, sig: Signal, ev: dict) -> tuple[dict, str | None]:
        m = self.cfg.smc
        if sig.target is None:
            return ev, "no resting liquidity ahead to target"
        risk, reward = abs(sig.close - sig.stop), abs(sig.target - sig.close)
        rr = reward / risk if risk > 0 else 0.0
        ev["plan"] = {"stop": round(sig.stop, 4), "target": round(sig.target, 4), "rr": round(rr, 2)}
        if rr < m.min_rr:
            return ev, f"reward:risk {rr:.2f} below {m.min_rr:g} (target {sig.target:,.2f}, stop {sig.stop:,.2f})"
        return ev, None
