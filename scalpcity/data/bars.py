"""Loading 1-minute bars for replay/backtest: CSV files, Polygon download, or synthetic.

CSV layout: <csv_dir>/<SYMBOL>/<YYYY-MM-DD>.csv with header
    timestamp,open,high,low,close,volume
timestamp = ISO-8601 with offset, or epoch milliseconds.
"""
from __future__ import annotations

import asyncio
import csv
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from ..core import calendar as cal
from ..core.events import Candle

SYNTH_BASE = {"SPY": 770.0, "QQQ": 750.0, "IWM": 245.0}


def read_csv(path: Path, symbol: str) -> list[Candle]:
    out = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            raw = row["timestamp"]
            ts = (datetime.fromtimestamp(int(raw) / 1000, tz=cal.ET) if raw.isdigit()
                  else datetime.fromisoformat(raw).astimezone(cal.ET))
            out.append(Candle(symbol, ts, float(row["open"]), float(row["high"]), float(row["low"]),
                              float(row["close"]), float(row.get("volume") or 0)))
    return out


def write_csv(path: Path, bars: list[Candle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for b in bars:
            w.writerow([b.start.isoformat(), b.open, b.high, b.low, b.close, b.volume])


def synthetic_day(symbol: str, day: date) -> list[Candle]:
    """Deterministic fake market data for demos and tests. NOT real prices.

    A driftless random walk with U-shaped intraday volatility and volume. It is
    deliberately trend-free: fake trends hand crossover strategies a fake edge
    (a trending version of this generator showed +$20k over 3 months), so here
    any strategy should lose roughly its spread + fee costs. Use it to test the
    machinery, never to judge the strategy.
    """
    rng = random.Random(f"{symbol}-{day.isoformat()}")
    day_index = (day - date(2026, 1, 1)).days
    price = SYNTH_BASE.get(symbol, 100.0) * (1 + 0.0004 * day_index) * (1 + rng.gauss(0, 0.004))
    daily_vol = {"SPY": 0.008, "QQQ": 0.011, "IWM": 0.014}.get(symbol, 0.012) * rng.uniform(0.7, 1.4)
    per_min = daily_vol / math.sqrt(390)
    open_t, close_t = cal.session_open(day), cal.session_close(day)
    n = int((close_t - open_t).total_seconds() // 60)
    drift = 0.0
    bars = []
    for i in range(n):
        x = i / max(n - 1, 1)
        u = 0.75 + 1.6 * (x - 0.5) ** 2 * 4 / 2  # ~1.55 at the open/close, 0.75 midday
        o = price
        hi = lo = o
        p = o
        for _ in range(6):
            p *= 1 + drift / 6 + rng.gauss(0, per_min * u / math.sqrt(6))
            hi, lo = max(hi, p), min(lo, p)
        c = p
        vol = int(rng.lognormvariate(math.log(40000 * u * u), 0.35))
        bars.append(Candle(symbol, open_t + timedelta(minutes=i), round(o, 2), round(hi, 2), round(lo, 2),
                           round(c, 2), vol))
        price = c
    return bars


class BarLoader:
    """Returns the regular-hours 1-minute bars of one symbol for one day."""

    def __init__(self, source: str, csv_dir: str) -> None:
        self.source, self.dir = source, Path(csv_dir)

    def load(self, symbol: str, day: date) -> list[Candle]:
        if self.source == "synthetic":
            return synthetic_day(symbol, day)
        path = self.dir / symbol / f"{day}.csv"
        if not path.exists() and self.source == "polygon":
            download([symbol], day, day, str(self.dir))
        return read_csv(path, symbol) if path.exists() else []


def download(symbols: list[str], start: date, end: date, csv_dir: str) -> list[Path]:
    """Download Polygon minute bars for every trading day in [start, end] to CSV."""
    from .polygon import PolygonClient

    async def run() -> list[Path]:
        client = PolygonClient()
        written = []
        try:
            for d in cal.trading_days(start, end):
                for s in symbols:
                    path = Path(csv_dir) / s / f"{d}.csv"
                    if path.exists():
                        continue
                    bars = await client.minute_bars(s, d)
                    if bars:
                        write_csv(path, bars)
                        written.append(path)
        finally:
            await client.close()
        return written

    return asyncio.run(run()) if not _in_loop() else []


def _in_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False
