"""Loading 1-minute bars for replay/backtest: CSV files, a Polygon or Alpaca download, or synthetic.

CSV layout: <csv_dir>/<SYMBOL>/<YYYY-MM-DD>.csv (BTC/USD is stored as BTC-USD) with header
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

SYNTH_BASE = {"SPY": 770.0, "QQQ": 750.0, "IWM": 245.0, "BTC/USD": 80000.0, "ETH/USD": 2400.0}


def bar_path(csv_dir, symbol: str, day: date) -> Path:
    return Path(csv_dir) / symbol.replace("/", "-") / f"{day}.csv"


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
    open_t, close_t = cal.session_open(day), cal.session_close(day)
    n = int((close_t - open_t).total_seconds() // 60)
    per_min = daily_vol / math.sqrt(n)
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


def fill_gaps(bars: list[Candle], day: date) -> list[Candle]:
    """Crypto: a minute with no trades has no bar; fill it with a flat bar at the last price so the
    replay keeps ticking (a live quote stream never goes quiet like that)."""
    if not bars:
        return bars
    out, i = [], 0
    t, end = bars[0].start, min(cal.session_close(day), bars[-1].start + timedelta(minutes=1))
    last = bars[0].close
    while t < end:
        if i < len(bars) and bars[i].start == t:
            out.append(bars[i])
            last = bars[i].close
            i += 1
        else:
            out.append(Candle(bars[0].symbol, t, last, last, last, last, 0.0))
        t += timedelta(minutes=1)
    return out


class BarLoader:
    """Returns the regular-hours 1-minute bars of one symbol for one day."""

    def __init__(self, source: str, csv_dir: str) -> None:
        self.source, self.dir = source, Path(csv_dir)

    def load(self, symbol: str, day: date) -> list[Candle]:
        if self.source == "synthetic":
            return synthetic_day(symbol, day)
        path = bar_path(self.dir, symbol, day)
        if not path.exists() and self.source in ("polygon", "alpaca"):
            download([symbol], day, day, str(self.dir), self.source)
        bars = read_csv(path, symbol) if path.exists() else []
        return fill_gaps(bars, day) if "/" in symbol else bars


def download(symbols: list[str], start: date, end: date, csv_dir: str, source: str = "polygon") -> list[Path]:
    """Download minute bars for every trading day in [start, end] to CSV.

    source "alpaca": Alpaca's full-market (SIP) stock history or crypto bars, using your Alpaca keys.
    source "polygon": Polygon (the free plan allows about 5 requests a minute, so this is slow)."""

    def client():
        if source == "alpaca":
            from .alpaca_data import AlpacaDataClient
            return AlpacaDataClient(stock_feed="sip")
        from .polygon import PolygonClient
        return PolygonClient()

    async def run() -> list[Path]:
        c = client()
        written = []
        try:
            for d in cal.trading_days(start, end):
                if source == "alpaca" and cal.now_et() < cal.session_close(d) + timedelta(minutes=16):
                    continue  # unfinished day (and the free plan holds back the last 15 min of SIP data)
                for s in symbols:
                    path = bar_path(csv_dir, s, d)
                    if path.exists():
                        continue
                    bars = await c.minute_bars(s, d)
                    if bars:
                        write_csv(path, bars)
                        written.append(path)
        finally:
            await c.close()
        return written

    return asyncio.run(run()) if not _in_loop() else []


def _in_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False
