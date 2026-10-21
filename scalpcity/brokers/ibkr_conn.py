"""One shared connection to Interactive Brokers (IB Gateway or TWS on this Mac), for the futures city.

Needs `pip install -r requirements-futures.txt` (ib_async) and the Gateway logged in to a PAPER account with the API
enabled (docs/futures-city.md). Safety: live ports are refused in config, and after connecting every account the
login can trade must be a paper account (IB paper account ids start with "DU", or "DF" for advisor paper accounts).
"""
from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger("scalpcity.ibkr")
EXCHANGES = {"MES": "CME", "MNQ": "CME", "ES": "CME", "NQ": "CME", "MGC": "COMEX", "GC": "COMEX"}
PAPER_PREFIXES = ("DU", "DF")

_ib = None
_key: Optional[tuple] = None


def paper_only(accounts: list[str]) -> None:
    if not accounts or any(not a.startswith(PAPER_PREFIXES) for a in accounts):
        raise RuntimeError(f"Interactive Brokers login is not a paper account ({', '.join(accounts) or 'none'}): "
                           f"log the Gateway in with your PAPER username (account id starting DU)")


async def connect(cfg):
    """The shared IB connection; connects (and checks it's paper) on first use."""
    global _ib, _key
    b = cfg.broker
    key = (b.ib_host, b.ib_port, b.ib_client_id)
    if _ib is not None and _key in (None, key) and _ib.isConnected():   # None: a test's fake
        return _ib
    try:
        from ib_async import IB
    except ImportError as exc:                       # pragma: no cover - depends on the Mac's install
        raise RuntimeError("the futures city needs ib_async: pip install -r requirements-futures.txt") from exc
    ib = IB()
    try:
        await ib.connectAsync(b.ib_host, b.ib_port, clientId=b.ib_client_id, timeout=15)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"can't reach IB Gateway at {b.ib_host}:{b.ib_port} ({exc}). Is IB Gateway running, logged "
                           f"in to the paper account, with the API enabled?") from exc
    try:
        paper_only(list(ib.managedAccounts()))
    except RuntimeError:
        ib.disconnect()
        raise
    _ib, _key = ib, key
    log.info("connected to Interactive Brokers paper account %s", ", ".join(ib.managedAccounts()))
    return ib


def use(ib) -> None:
    """Tests: install a fake connection."""
    global _ib, _key
    _ib, _key = ib, None


def ib_contract(c, *, expired: bool = False):
    """The IB Future for one of our FuturesContracts."""
    from ib_async import Future
    f = Future(symbol=c.underlying, lastTradeDateOrContractMonth=f"{c.month:%Y%m}",
               exchange=EXCHANGES.get(c.underlying, "CME"), currency="USD")
    f.includeExpired = expired
    return f
