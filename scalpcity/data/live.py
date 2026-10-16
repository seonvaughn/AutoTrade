"""Picks the paper/live market-data client from config (data.live_data)."""
from __future__ import annotations


def live_client(cfg):
    d = cfg.data
    if d.live_data == "alpaca" or cfg.market == "crypto":
        from .alpaca_data import AlpacaDataClient
        return AlpacaDataClient(d.alpaca_stock_feed, d.alpaca_options_feed)
    from .polygon import PolygonClient
    return PolygonClient()
