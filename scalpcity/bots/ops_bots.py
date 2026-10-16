"""Operations: Health Monitor and Alert bots."""
from __future__ import annotations

import logging
import os
from datetime import timedelta

from ..core import calendar as cal
from ..core.events import Alert, BotError, Heartbeat, HealthStatus, OrderFailed, Purpose, Tick
from .base import Bot


class HealthBot(Bot):
    name = "health"
    skill = "Detect stale market data and failing bots; pause new entries until healthy"

    def setup(self) -> None:
        self.watching_since = None
        self.last_tick: dict[str, object] = {}
        self.flagged = False
        self.on(Tick, lambda t: self.last_tick.__setitem__(t.symbol, t.ts))
        self.on(Heartbeat, self.on_heartbeat)
        self.on(BotError, lambda e: self.emit(Alert(e.ts, "warning", f"bot '{e.bot}' error: {e.error}")))
        self.on(OrderFailed, self.on_failed)

    def on_failed(self, e: OrderFailed) -> None:
        level = "critical" if e.intent.purpose is Purpose.EXIT else "info"
        self.emit(Alert(e.ts, level, f"{e.intent.worker}: {e.intent.purpose.value} order failed ({e.reason})"))

    def on_heartbeat(self, hb: Heartbeat) -> None:
        clock = self.bot("clock")
        if not clock or not clock.is_open() or hb.ts < cal.session_open(hb.ts.date()) + timedelta(minutes=1):
            return
        limit = timedelta(seconds=self.cfg.stale_data_seconds)
        if self.watching_since is None:
            self.watching_since = hb.ts  # a symbol we never heard from gets the same grace as one that went quiet
        stale = [s for s in self.cfg.symbols if hb.ts - self.last_tick.get(s, self.watching_since) > limit]
        if stale and not self.flagged:
            self.flagged = True
            text = f"no market data for {', '.join(stale)} in {self.cfg.stale_data_seconds:g}s — pausing entries"
            self.emit(Alert(hb.ts, "critical", text))
            self.emit(HealthStatus(hb.ts, False, text, "data"))
        elif not stale and self.flagged:
            self.flagged = False
            self.emit(Alert(hb.ts, "info", "market data back — resuming"))
            self.emit(HealthStatus(hb.ts, True, "data ok", "data"))


class AlertBot(Bot):
    name = "alerts"
    skill = "Deliver alerts: log + optional Discord/Slack webhook (env SCALPCITY_ALERT_WEBHOOK)"

    def setup(self) -> None:
        self.recent: dict[str, object] = {}
        self.history: list[Alert] = []
        self.webhook = os.environ.get(self.cfg.alert_webhook_env, "")
        self.on(Alert, self.on_alert)

    def on_alert(self, a: Alert) -> None:
        last = self.recent.get(a.text)
        if last and (a.ts - last).total_seconds() < 60:
            return
        self.recent[a.text] = a.ts
        self.history.append(a)
        lvl = {"info": logging.INFO, "warning": logging.WARNING, "critical": logging.CRITICAL}.get(a.level, logging.INFO)
        self.log.log(lvl, a.text)
        if self.webhook and self.ctx.live and a.level != "info":
            self.spawn(self._post(f"[{a.level.upper()}] Scalp City: {a.text}"))

    async def _post(self, text: str) -> None:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as h:
                await h.post(self.webhook, json={"content": text, "text": text})
        except Exception as exc:  # noqa: BLE001
            self.log.warning("webhook failed: %s", exc)
