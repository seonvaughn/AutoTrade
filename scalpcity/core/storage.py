"""SQLite persistence for fills, closed trades, thoughts and daily results."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS fills (
  ts TEXT, run TEXT, mode TEXT, worker TEXT, contract TEXT, side TEXT, purpose TEXT,
  qty INTEGER, price REAL, fees REAL, order_id TEXT);
CREATE TABLE IF NOT EXISTS trades (
  closed_at TEXT, opened_at TEXT, run TEXT, mode TEXT, worker TEXT, contract TEXT,
  qty INTEGER, entry REAL, exit REAL, pnl REAL, reason TEXT);
CREATE TABLE IF NOT EXISTS thoughts (ts TEXT, run TEXT, mode TEXT, worker TEXT, text TEXT, tone TEXT);
CREATE TABLE IF NOT EXISTS daily (
  day TEXT, run TEXT, mode TEXT, worker TEXT, pnl REAL, trades INTEGER, wins INTEGER,
  PRIMARY KEY (day, run, worker));
"""


class Storage:
    def __init__(self, path: str, run: str, mode: str) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)
        self.run, self.mode = run, mode

    def add_fill(self, ts, worker, contract, side, purpose, qty, price, fees, order_id) -> None:
        self.db.execute("INSERT INTO fills VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (ts.isoformat(), self.run, self.mode, worker, contract, side, purpose, qty, price, fees, order_id))
        self.db.commit()

    def add_trade(self, closed_at, opened_at, worker, contract, qty, entry, exit_, pnl, reason) -> None:
        self.db.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (closed_at.isoformat(), opened_at.isoformat(), self.run, self.mode, worker, contract,
                         qty, entry, exit_, pnl, reason))
        self.db.commit()

    def add_thought(self, ts, worker, text, tone) -> None:
        self.db.execute("INSERT INTO thoughts VALUES (?,?,?,?,?,?)",
                        (ts.isoformat(), self.run, self.mode, worker, text, tone))
        self.db.commit()

    def set_daily(self, day, worker, pnl, trades, wins) -> None:
        self.db.execute("INSERT OR REPLACE INTO daily VALUES (?,?,?,?,?,?,?)",
                        (day.isoformat(), self.run, self.mode, worker, pnl, trades, wins))
        self.db.commit()

    def daily_totals(self, limit: int = 30) -> list[tuple[str, float]]:
        rows = self.db.execute(
            "SELECT day, SUM(pnl) FROM daily WHERE mode=? AND run=? GROUP BY day ORDER BY day DESC LIMIT ?",
            (self.mode, self.run, limit)).fetchall()
        return list(reversed(rows))

    def trades(self) -> list[tuple]:
        return self.db.execute("SELECT * FROM trades WHERE run=? ORDER BY closed_at", (self.run,)).fetchall()
