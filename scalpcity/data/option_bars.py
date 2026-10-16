"""Real option minute bars for backtests, cached to disk as CSV (sync; backtest only).

Provider follows data.source: "alpaca" uses Alpaca's option bars (your Alpaca keys);
anything else uses Polygon (POLYGON_API_KEY, needs an options plan with minute history).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import logging
import time

import httpx

from ..core import calendar as cal
from ..core.events import Candle, OptionContract
from .bars import read_csv, write_csv

log = logging.getLogger("scalpcity.option_bars")


def _fetch_polygon(contract: OptionContract, day: date) -> list[Candle]:
    from .polygon import BASE, _bars_from_results, api_key
    with httpx.Client(base_url=BASE, timeout=20.0, headers={"Authorization": f"Bearer {api_key()}"}) as h:
        r = h.get(f"/v2/aggs/ticker/O:{contract.occ}/range/1/minute/{day}/{day}",
                  params={"adjusted": "true", "sort": "asc", "limit": 50000})
        r.raise_for_status()
        return _bars_from_results(contract.occ, r.json().get("results") or [])


def _fetch_alpaca(contract: OptionContract, day: date) -> list[Candle]:
    from .alpaca_data import BASE, _bars_from_results, keys
    key, secret = keys()
    start = datetime.combine(day, datetime.min.time(), cal.ET)
    params = {"symbols": contract.occ, "timeframe": "1Min", "start": start.isoformat(),
              "end": (start + timedelta(days=1)).isoformat(), "limit": 10000, "sort": "asc"}
    out: list[dict] = []
    with httpx.Client(base_url=BASE, timeout=20.0,
                      headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}) as h:
        while True:
            for attempt in range(6):
                r = h.get("/v1beta1/options/bars", params=params)
                if r.status_code != 429:
                    break
                time.sleep(min(2 ** attempt, 30))
            r.raise_for_status()
            body = r.json()
            out += (body.get("bars") or {}).get(contract.occ, [])
            if not body.get("next_page_token"):
                break
            params["page_token"] = body["next_page_token"]
    return _bars_from_results(contract.occ, out)


class HistoricalOptionBars:
    def __init__(self, cache_dir: str, source: str = "polygon") -> None:
        self.dir = Path(cache_dir)
        self.fetch = _fetch_alpaca if source == "alpaca" else _fetch_polygon
        self.mem: dict[tuple[str, date], list[Candle]] = {}
        self.failures = 0

    def bars(self, contract: OptionContract, day: date) -> list[Candle]:
        k = (contract.occ, day)
        if k in self.mem:
            return self.mem[k]
        path = self.dir / contract.occ / f"{day}.csv"
        if path.exists():
            bars = read_csv(path, contract.occ)
        else:
            try:
                bars = self.fetch(contract, day)
            except Exception as exc:  # noqa: BLE001 - fall back to the model price, don't cache the miss
                self.failures += 1
                if self.failures <= 3:
                    log.warning("option bars for %s %s unavailable (%s); using the model price", contract.occ, day, exc)
                return []
            write_csv(path, bars)
        self.mem[k] = bars
        return bars

    def price_at(self, contract: OptionContract, ts: datetime) -> Optional[float]:
        """Close of the last option bar fully completed at ts (None if it never traded yet)."""
        last = None
        for b in self.bars(contract, ts.date()):
            if (ts - b.start).total_seconds() >= 60:
                last = b.close
            else:
                break
        return last
