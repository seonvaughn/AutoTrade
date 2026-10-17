"""Dashboard Bot — serves the "Scalp City" 3D view and streams live state to it.

Read-only except for one control: the kill switch button (publishes a
KillSwitchRequest, which the Daily Goal / Kill Switch bot decides on).
"""
from __future__ import annotations

import asyncio
import hmac
import json
import os
from collections import deque
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from ..core import calendar as cal
from ..core.events import (Alert, CandleClosed, DailySummary, EntryVetoed, Fill, KeyLevels, ResearchCleared, Heartbeat, HealthStatus, IndicatorValue,
                           KillSwitch, KillSwitchRequest, Leaderboard, PnLUpdate, PositionOpened, OptionQuote,
                           SessionEvent, SessionKind, SetupUpdate, Thought, Tick, TradeClosed, WorkerStatus, Purpose)
from ..core.costs import fmt_qty
from .base import Bot

STATIC = Path(__file__).resolve().parents[2] / "dashboard"
TOKEN_ENV = "SCALPCITY_DASHBOARD_TOKEN"
LOOPBACK = {"127.0.0.1", "localhost", "::1"}

# Which crew bots work for a worker (shown inside its building), by trigger.
TRIGGER_BOTS = {"vwap_cross": ["vwap", "sig_vwap_cross"], "ema50_cross": ["ema50", "sig_ema50_cross"],
                "orb": ["opening_range", "sig_orb"]}
SHARED_CREW = ["price_feed", "candles", "atr", "key_levels", "edge_tracker", "research_gate",
               "signal_filter", "contract_selector", "position_sizer",
               "risk_manager", "execution", "exit_manager", "ledger", "daily_goal", "journal"]


class DashboardBot(Bot):
    name = "dashboard"
    skill = "Scalp City 3D dashboard: towers, beams, vault, leaderboard, thoughts, charts (read-only + kill switch)"

    def setup(self) -> None:
        self.clients: set = set()
        self.outbox: list[dict] = []
        self.dirty = True
        self.clock: datetime | None = None
        self.day = None
        self.session = "closed"
        self.health: dict[str, str] = {}
        self.kill = {"engaged": False, "reason": ""}
        self.vault = 0.0
        self.prices: dict[str, float] = {}
        self.setups: dict[tuple[str, str], dict] = {}
        self.positions: dict[str, dict] = {}
        self.pnl: dict[str, dict] = {}
        self.clocked_out: dict[str, str] = {}
        self.stats: dict[str, dict] = {}
        self.last_trades: dict[str, deque] = {}
        self.thoughts: dict[str, deque] = {}
        self.ticker: deque = deque(maxlen=40)
        self.candles: dict[str, dict] = {}
        self.dirty_candles: set = set()
        self.summary: dict | None = None
        self.alerts: deque = deque(maxlen=20)
        self.levels: dict[str, list[dict]] = {}
        self.vetoes: dict[str, deque] = {}
        self.cleared: dict[str, deque] = {}
        for w in self.workers:
            self.vetoes[w.name] = deque(maxlen=40)
            self.cleared[w.name] = deque(maxlen=40)
            self.thoughts[w.name] = deque(maxlen=60)
            self.last_trades[w.name] = deque(maxlen=60)
            self.stats[w.name] = {"trades": 0, "wins": 0, "pnl": 0.0}

        self.on(Heartbeat, self.on_heartbeat)
        self.on(SessionEvent, self.on_session)
        self.on(Tick, lambda e: self.prices.__setitem__(e.symbol, e.price))
        self.on(SetupUpdate, self.on_setup)
        self.on(PositionOpened, self.on_opened)
        self.on(OptionQuote, self.on_quote)
        self.on(TradeClosed, self.on_closed)
        self.on(PnLUpdate, self.on_pnl)
        self.on(WorkerStatus, self.on_status)
        self.on(KillSwitch, self.on_kill)
        self.on(HealthStatus, self.on_health)
        self.on(Thought, self.on_thought)
        self.on(Leaderboard, self.on_leaderboard)
        self.on(DailySummary, self.on_summary)
        self.on(Fill, self.on_fill)
        self.on(Alert, self.on_alert)
        self.on(CandleClosed, self.on_candle)
        self.on(IndicatorValue, self.on_indicator)
        self.on(KeyLevels, self.on_levels)
        self.on(EntryVetoed, self.on_vetoed)
        self.on(ResearchCleared, self.on_cleared)

    def on_levels(self, e: KeyLevels) -> None:
        self.levels[e.symbol] = [{"price": lv.price, "label": lv.label, "strength": lv.strength} for lv in e.levels]
        self.dirty = True

    def on_vetoed(self, e: EntryVetoed) -> None:
        s = e.signal
        self.vetoes.setdefault(e.worker, deque(maxlen=40)).appendleft(
            {"t": e.ts.strftime("%H:%M"), "side": s.side.value, "trigger": s.trigger, "reason": e.reason})
        self.dirty = True

    def on_cleared(self, e: ResearchCleared) -> None:
        s, nxt = e.signal, e.evidence.get("next_level")
        self.cleared.setdefault(e.worker, deque(maxlen=40)).appendleft(
            {"t": e.ts.strftime("%H:%M"), "side": s.side.value, "trigger": s.trigger,
             "edge": e.evidence.get("edge"), "next": nxt})
        self.dirty = True

    @property
    def workers(self):
        return [w for w in self.cfg.workers if w.enabled]

    def push(self, msg: dict) -> None:
        if self.clients:
            self.outbox.append(msg)

    # ---------------------------------------------------------------- event handlers
    def on_heartbeat(self, e: Heartbeat) -> None:
        self.clock = e.ts
        self.dirty = True

    def on_session(self, e: SessionEvent) -> None:
        self.session = {SessionKind.NEW_DAY: "pre-market", SessionKind.OPEN: "open",
                        SessionKind.ENTRY_CUTOFF: "closing", SessionKind.FLATTEN: "flattening",
                        SessionKind.CLOSED: "closed"}[e.kind]
        if e.kind is SessionKind.NEW_DAY:
            self.day = e.day
            self.summary = None
            self.vault = 0.0
            self.pnl.clear()
            for s in self.stats.values():
                s.update(trades=0, wins=0, pnl=0.0)
            for d in self.last_trades.values():
                d.clear()
            for sym in self.candles:
                self.candles[sym] = {k: v for k, v in self.candles[sym].items() if v["t"][:10] == e.day.isoformat()}
            for d in list(self.vetoes.values()) + list(self.cleared.values()):
                d.clear()
            self.push({"type": "reset_day", "day": e.day.isoformat()})
        self.dirty = True

    def on_setup(self, e: SetupUpdate) -> None:
        self.setups[(e.symbol, e.trigger)] = {"side": e.side.value, "charge": e.charge,
                                              "distance": e.distance_atr, "level": round(e.level, 2)}
        self.dirty = True

    def on_opened(self, e: PositionOpened) -> None:
        self.positions[e.worker] = {"contract": e.contract.occ, "right": e.contract.right.value,
                                    "strike": e.contract.strike, "label": e.contract.label,
                                    "kind": e.contract.kind, "mult": e.contract.multiplier,
                                    "expiry": e.contract.expiry.isoformat() if e.contract.expiry else None,
                                    "qty": e.qty, "entry": e.entry_price,
                                    "mark": e.entry_price, "opened": e.ts.isoformat()}
        self.push({"type": "fire", "worker": e.worker, "side": e.contract.right.value})
        self.dirty = True

    def on_quote(self, q: OptionQuote) -> None:
        for p in self.positions.values():
            if p["contract"] == q.contract.occ:
                p["mark"] = q.mid
                self.dirty = True

    def on_closed(self, e: TradeClosed) -> None:
        self.positions.pop(e.worker, None)
        s = self.stats[e.worker]
        s["trades"] += 1
        s["wins"] += 1 if e.pnl > 0 else 0
        s["pnl"] += e.pnl
        self.last_trades[e.worker].appendleft({
            "t": e.opened_at.strftime("%H:%M"), "out": e.ts.strftime("%H:%M"), "side": e.contract.right.value,
            "qty": e.qty, "sym": e.contract.underlying, "label": e.contract.label, "entry": e.entry_price,
            "exit": e.exit_price, "pnl": e.pnl, "reason": e.reason})
        self.push({"type": "closed", "worker": e.worker, "pnl": e.pnl, "reason": e.reason})
        self.dirty = True

    def on_pnl(self, e: PnLUpdate) -> None:
        self.pnl[e.worker] = {"realized": e.realized, "unrealized": e.unrealized}
        self.vault = e.vault
        self.dirty = True

    def on_status(self, e: WorkerStatus) -> None:
        if e.clocked_out:
            self.clocked_out[e.worker] = e.reason
        else:
            self.clocked_out.pop(e.worker, None)
        self.dirty = True

    def on_kill(self, e: KillSwitch) -> None:
        self.kill = {"engaged": e.engaged, "reason": e.reason}
        self.dirty = True

    def on_health(self, e: HealthStatus) -> None:
        if e.ok:
            self.health.pop(e.source, None)
        else:
            self.health[e.source] = e.reason
        self.dirty = True

    def on_thought(self, e: Thought) -> None:
        item = {"t": e.ts.strftime("%H:%M:%S"), "text": e.text, "tone": e.tone}
        self.thoughts.setdefault(e.worker, deque(maxlen=60)).appendleft(item)
        self.push({"type": "thought", "worker": e.worker, **item})

    def on_leaderboard(self, e: Leaderboard) -> None:
        self.dirty = True

    def on_summary(self, e: DailySummary) -> None:
        self.summary = {"day": e.day.isoformat(), "total": e.total, "by_worker": e.by_worker,
                        "top": e.top_worker, "trades": e.trades, "wins": e.wins}
        self.push({"type": "summary", **self.summary})
        self.dirty = True

    def on_fill(self, e: Fill) -> None:
        it = e.intent
        what = it.contract.underlying if it.contract.kind == "crypto" else it.contract.right.value
        if it.purpose is Purpose.ENTRY:
            text = f"{it.worker} {e.ts:%H:%M} {it.contract.right.arrow} bought {fmt_qty(e.qty)} {what} @ {e.price:,.2f}"
            tone = "fire"
        else:
            text = f"{it.worker} {e.ts:%H:%M} sold {fmt_qty(e.qty)} @ {e.price:,.2f} · {it.reason.replace('_', ' ')}"
            tone = "info"
        item = {"text": text, "tone": tone}
        self.ticker.appendleft(item)
        self.push({"type": "ticker", **item})

    def on_alert(self, e: Alert) -> None:
        item = {"t": e.ts.strftime("%H:%M:%S"), "level": e.level, "text": e.text}
        self.alerts.appendleft(item)
        self.push({"type": "alert", **item})

    def on_candle(self, e: CandleClosed) -> None:
        c = e.candle
        if self.day and c.start.date() != self.day:
            return
        key = c.start.isoformat()
        self.candles.setdefault(c.symbol, {})[key] = {"t": key, "o": c.open, "h": c.high, "l": c.low, "c": c.close}
        self.dirty_candles.add((c.symbol, key))

    def on_indicator(self, e: IndicatorValue) -> None:
        if e.name not in ("vwap", "ema50"):
            return
        rec = self.candles.get(e.symbol, {}).get(e.candle.start.isoformat())
        if rec is not None:
            rec[e.name] = round(e.value, 4)
            self.dirty_candles.add((e.symbol, rec["t"]))

    # ---------------------------------------------------------------- state
    def worker_state(self, w) -> dict:
        live = self.session in ("open", "closing")
        setups = {t: (self.setups.get((w.symbol, t)) if live else None) for t in w.triggers}
        best = max((s["charge"] for s in setups.values() if s), default=0)
        best_side = next((s["side"] for s in setups.values() if s and s["charge"] == best), None)
        pos = self.positions.get(w.name)
        if w.name in self.clocked_out:
            status = "clocked_out"
        elif pos:
            status = "in_trade"
        elif best >= 50 and self.session == "open":
            status = "charging"
        else:
            status = "watching"
        pnl = self.pnl.get(w.name, {"realized": 0.0, "unrealized": 0.0})
        st = self.stats[w.name]
        if pos:
            pos = {**pos, "pnl": round((pos["mark"] - pos["entry"]) * pos["qty"] * pos["mult"], 2)}
        crew = [b for t in w.triggers for b in TRIGGER_BOTS.get(t, [])] + SHARED_CREW
        edge_bot = self.bot("edge_tracker")
        today = self.day or (self.clock.date() if self.clock else None)
        edges = [edge_bot.stats(w.symbol, t, today) for t in w.triggers] if edge_bot and today else []
        research = {"gate": self.cfg.research.enabled and w.research_gate, "edges": edges,
                    "vetoes": list(self.vetoes.get(w.name, [])), "cleared": list(self.cleared.get(w.name, []))}
        return {"name": w.name, "symbol": w.symbol, "triggers": w.triggers, "status": status,
                "clock_reason": self.clocked_out.get(w.name), "setups": setups, "charge": best, "side": best_side,
                "position": pos, "realized": round(pnl["realized"], 2), "unrealized": round(pnl["unrealized"], 2),
                "trades": st["trades"], "wins": st["wins"], "last_trades": list(self.last_trades[w.name]),
                "goal": w.daily_goal, "max_loss": w.max_daily_loss, "dte": w.dte, "crew": crew, "research": research,
                "settings": {"strike": w.strike, "dte": w.dte, "window": f"{w.start_time}-{w.end_time}",
                             "sizing": vars(w.sizing), "exits": vars(w.exits), "cooldown": w.cooldown_minutes,
                             "max_trades": w.max_trades_per_day, "trend_filter": w.trend_filter,
                             "min_close_beyond_atr": w.min_close_beyond_atr}}

    def crew(self) -> list[dict]:
        orch = self.bot("orchestrator")
        act = self.bus.activity
        out = []
        for name, skill in (orch.roster() if orch else []):
            a = act.get(name)
            handled, last, ts = (a[0], a[1], a[2]) if a else (0, "", None)
            if name == "price_feed":  # a source: count what it brought in
                handled, last = self.bus.published.get("Tick", 0), "Tick"
            out.append({"name": name, "skill": skill, "handled": handled, "last": last,
                        "ts": ts.strftime("%H:%M:%S") if ts else None})
        return out

    def state(self) -> dict:
        close = cal.session_close(self.day).isoformat() if self.day else None
        orch = self.bot("orchestrator")
        return {
            "mode": self.cfg.mode, "market": self.cfg.market, "day": self.day.isoformat() if self.day else None,
            "clock": self.clock.isoformat() if self.clock else None, "session": self.session, "close": close,
            "health": self.health, "kill": self.kill, "vault": round(self.vault, 2),
            "prices": self.prices, "workers": [self.worker_state(w) for w in self.workers],
            "calendar": [{"day": d, "pnl": round(p or 0, 2)} for d, p in self.ctx.storage.daily_totals(25)],
            "summary": self.summary,
            "roster": [{"name": n, "skill": s} for n, s in orch.roster()] if orch else [],
            "crew": self.crew(),
            "levels": self.levels,
            "research": vars(self.cfg.research),
        }

    def snapshot(self) -> dict:
        return {"type": "snapshot", "state": self.state(),
                "thoughts": {k: list(v) for k, v in self.thoughts.items()},
                "ticker": list(self.ticker), "alerts": list(self.alerts),
                "candles": {s: sorted(v.values(), key=lambda r: r["t"]) for s, v in self.candles.items()}}

    # ---------------------------------------------------------------- server
    @staticmethod
    def token() -> str:
        return os.environ.get(TOKEN_ENV, "")

    def authorized(self, query_token: str | None, cookie_token: str | None) -> bool:
        want = self.token()
        if not want:
            return True
        return any(t and hmac.compare_digest(t, want) for t in (query_token, cookie_token))

    def app(self) -> FastAPI:
        app = FastAPI(title="Scalp City")

        @app.middleware("http")
        async def guard(request: Request, call_next):
            if not self.authorized(request.query_params.get("token"), request.cookies.get("scalpcity_token")):
                return PlainTextResponse("Scalp City: add ?token=<your SCALPCITY_DASHBOARD_TOKEN> to the address",
                                         status_code=401)
            response = await call_next(request)
            if self.token() and request.query_params.get("token"):
                response.set_cookie("scalpcity_token", self.token(), httponly=True, samesite="strict")
            return response

        app.mount("/static", StaticFiles(directory=STATIC), name="static")

        @app.get("/")
        async def index():
            return FileResponse(STATIC / "index.html")

        @app.get("/api/state")
        async def api_state():
            return JSONResponse(self.state())

        @app.post("/api/kill")
        async def api_kill(body: dict):
            engage = bool(body.get("engage", True))
            await self.bus.emit(KillSwitchRequest(self.clock or cal.now_et(),
                                                  "dashboard button" if engage else "released from dashboard", engage))
            return {"ok": True, "kill": self.kill}

        @app.websocket("/ws")
        async def ws(sock: WebSocket):
            if not self.authorized(sock.query_params.get("token"), sock.cookies.get("scalpcity_token")):
                await sock.close(code=4401)
                return
            await sock.accept()
            await sock.send_text(json.dumps(self.snapshot(), default=str))
            self.clients.add(sock)
            try:
                while True:
                    await sock.receive_text()
            except WebSocketDisconnect:
                pass
            finally:
                self.clients.discard(sock)

        return app

    async def start(self) -> None:
        import socket

        import uvicorn

        host, port = self.cfg.dashboard.host, self.cfg.dashboard.port
        if host not in LOOPBACK and not self.token():
            raise RuntimeError(f"dashboard.host is {host}, which other devices can reach: set {TOKEN_ENV} to a "
                               f"long random string first (the dashboard has a kill switch), or use 127.0.0.1")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, port))
            except OSError as exc:
                raise RuntimeError(f"dashboard port {host}:{port} is busy ({exc.strerror}) — is another Scalp City "
                                   f"running? Stop it or change dashboard.port in config.yaml") from None
        server = uvicorn.Server(uvicorn.Config(self.app(), host=self.cfg.dashboard.host, port=self.cfg.dashboard.port,
                                               log_level="warning", lifespan="off"))
        server.install_signal_handlers = lambda: None
        self.server = server
        self.spawn(self._serve(server))
        self.spawn(self._flush())

    async def _serve(self, server) -> None:
        try:
            await server.serve()
        except (SystemExit, Exception) as exc:  # noqa: BLE001 - the UI must never take trading down
            self.log.error("dashboard server stopped: %r — trading continues without the UI", exc)

    async def _flush(self) -> None:
        while True:
            await asyncio.sleep(0.25)
            if not self.clients:
                self.outbox.clear()
                self.dirty_candles.clear()
                continue
            msgs, self.outbox = self.outbox, []
            for sym, key in sorted(self.dirty_candles):
                rec = self.candles.get(sym, {}).get(key)
                if rec:
                    msgs.append({"type": "candle", "symbol": sym, **rec})
            self.dirty_candles.clear()
            if self.dirty:
                msgs.append({"type": "state", "state": self.state()})
                self.dirty = False
            if not msgs:
                continue
            payload = json.dumps({"type": "batch", "items": msgs}, default=str)
            for sock in list(self.clients):
                try:
                    await sock.send_text(payload)
                except Exception:  # noqa: BLE001
                    self.clients.discard(sock)

    async def stop(self) -> None:
        if getattr(self, "server", None):
            self.server.should_exit = True
            await asyncio.sleep(0.3)
        await super().stop()
