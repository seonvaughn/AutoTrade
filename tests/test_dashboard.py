"""Dashboard server: access token, crew activity, building interiors' data."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg
from tests.test_system import DAYS


def dash(cfg=None):
    o = Orchestrator(cfg or make_cfg(), db_path=":memory:", dashboard=True)
    return o, o.dashboard


def test_open_without_token_on_loopback(monkeypatch):
    monkeypatch.delenv("SCALPCITY_DASHBOARD_TOKEN", raising=False)
    _, d = dash()
    c = TestClient(d.app())
    assert c.get("/").status_code == 200
    assert c.get("/api/state").status_code == 200


def test_token_required_when_set(monkeypatch):
    monkeypatch.setenv("SCALPCITY_DASHBOARD_TOKEN", "s3cret-long-token")
    _, d = dash()
    c = TestClient(d.app())
    assert c.get("/").status_code == 401
    assert c.get("/api/state?token=wrong").status_code == 401
    assert c.post("/api/kill", json={"engage": True}).status_code == 401      # kill switch is guarded too
    r = c.get("/?token=s3cret-long-token")
    assert r.status_code == 200 and "scalpcity_token" in r.cookies
    assert c.get("/api/state").status_code == 200                            # cookie carries on
    with c.websocket_connect("/ws") as ws:
        assert json.loads(ws.receive_text())["type"] == "snapshot"
    c2 = TestClient(d.app())
    with pytest.raises(Exception):
        with c2.websocket_connect("/ws") as ws:
            ws.receive_text()


def test_refuses_lan_host_without_token(monkeypatch):
    monkeypatch.delenv("SCALPCITY_DASHBOARD_TOKEN", raising=False)
    cfg = make_cfg()
    cfg.dashboard.host = "0.0.0.0"
    _, d = dash(cfg)
    with pytest.raises(RuntimeError, match="SCALPCITY_DASHBOARD_TOKEN"):
        asyncio.run(d.start())


def test_state_has_crew_activity_and_interior_data():
    o, d = dash()

    async def no_server():  # don't bind a real port in tests
        return None

    d.start = no_server
    asyncio.run(o.replay(DAYS[:1]))
    s = d.state()
    crew = {c["name"]: c for c in s["crew"]}
    assert len(crew) == 41 and crew["candles"]["handled"] > 0 and crew["price_feed"]["handled"] > 0
    w = s["workers"][0]
    assert {"vwap", "sig_vwap_cross", "execution"} <= set(w["crew"])
    assert w["settings"]["exits"]["stop_loss_pct"] > 0 and w["settings"]["window"] == "09:35-15:30"
    t = w["last_trades"][0]
    assert {"label", "entry", "exit", "out"} <= set(t)
    json.dumps(s, default=str)
