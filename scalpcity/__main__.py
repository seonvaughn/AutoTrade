"""Command line.

  python -m scalpcity backtest --start 2026-09-01 --end 2026-10-02
  python -m scalpcity replay   --day 2026-10-02 --pace 1      (watch it in the dashboard)
  python -m scalpcity paper                                    (Alpaca paper broker + live data)
  python -m scalpcity live                                     (real money; see README)
  python -m scalpcity download --start 2026-09-01 --end 2026-10-02
  python -m scalpcity bots                                     (list every bot and its one skill)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import date
from pathlib import Path

from .core import calendar as cal
from .core.config import load


def _days(args) -> list[date]:
    if getattr(args, "day", None):
        return [date.fromisoformat(args.day)]
    return cal.trading_days(date.fromisoformat(args.start), date.fromisoformat(args.end))


def _print_report(r: dict) -> None:
    print("\n================ BACKTEST REPORT ================")
    print(f"days {r['days']}  |  net {r['net_pnl']:+,.2f}  |  green {r['green_days']}  red {r['red_days']}")
    print(f"trades {r['trades']}  |  win rate {r['win_rate']:.1%}  |  profit factor {r['profit_factor']}  "
          f"|  avg/trade {r['avg_trade']:+,.2f}")
    print(f"best day {r['best_day']:+,.2f}  |  worst day {r['worst_day']:+,.2f}  |  max drawdown {r['max_drawdown']:,.2f}")
    print("\nworker            trades  win%     pnl       exp/trade  maxDD")
    for n, w in r["workers"].items():
        print(f"{n:<16} {w['trades']:>6}  {w['win_rate']:>5.1%} {w['pnl']:>10,.2f} {w['expectancy']:>10,.2f} {w['max_drawdown']:>8,.2f}")
    if r.get("blocked_entries"):
        print("\nentries blocked (signal fired but no trade was placed):")
        for reason, n in r["blocked_entries"].items():
            print(f"  {n:>6}  {reason}")
    print("\nday          pnl        trades  top worker")
    for d in r["daily"]:
        print(f"{d['day']}  {d['pnl']:>+10,.2f}  {d['trades']:>6}  {d['top'] or '-'}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="scalpcity")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backtest")
    b.add_argument("--start", required=True)
    b.add_argument("--end", required=True)
    b.add_argument("--source", choices=["synthetic", "csv", "polygon", "alpaca"])
    b.add_argument("--out", default="reports")
    r = sub.add_parser("replay")
    r.add_argument("--day", required=True)
    r.add_argument("--pace", type=float, default=1.0, help="seconds per market minute")
    r.add_argument("--source", choices=["synthetic", "csv", "polygon", "alpaca"])
    sub.add_parser("paper")
    sub.add_parser("live")
    d = sub.add_parser("download")
    d.add_argument("--start", required=True)
    d.add_argument("--end", required=True)
    sub.add_parser("bots")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    for noisy in ("httpx", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    from .orchestrator import Orchestrator

    if args.cmd == "bots":
        cfg = load(args.config, "backtest")
        o = Orchestrator(cfg, db_path=":memory:", dashboard=True)
        for i, (name, skill) in enumerate(o.roster(), 1):
            print(f"{i:>2}. {name:<20} {skill}")
        return 0

    if args.cmd == "download":
        cfg = load(args.config, "backtest")
        from .data.bars import download
        paths = download(cfg.symbols, date.fromisoformat(args.start), date.fromisoformat(args.end), cfg.data.csv_dir,
                         cfg.data.source if cfg.data.source in ("polygon", "alpaca") else "polygon")
        print(f"downloaded {len(paths)} files into {cfg.data.csv_dir}")
        return 0

    if args.cmd in ("backtest", "replay"):
        cfg = load(args.config, args.cmd)
        if args.source:
            cfg.data.source = args.source
        days = _days(args)
        if cfg.data.source in ("polygon", "alpaca"):
            from .data.bars import download
            first = days[0]
            for _ in range(max(1, cfg.research.lookback_days)):  # the sessions the research bots study first
                first = cal.prev_trading_day(first)
            download(cfg.symbols, first, days[-1], cfg.data.csv_dir, cfg.data.source)
        if cfg.data.source == "synthetic":
            logging.getLogger("scalpcity").warning("using SYNTHETIC prices — for testing the machinery only, "
                                                   "results say nothing about real profitability")
        if args.cmd == "backtest":
            o = Orchestrator(cfg, dashboard=False)
            report = asyncio.run(o.replay(days))
            _print_report(report)
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            name = f"{o.storage.run}.json"
            (out / name).write_text(json.dumps(report, indent=2))
            print(f"\nreport: {out / name}   trades + thoughts: {cfg.db_path} (run {o.storage.run})")
        else:
            o = Orchestrator(cfg, dashboard=True)
            print(f"dashboard: http://{cfg.dashboard.host}:{cfg.dashboard.port}")
            asyncio.run(_replay_then_hold(o, days, args.pace))
        return 0

    cfg = load(args.config, args.cmd)
    o = Orchestrator(cfg)
    if o.dashboard:
        print(f"dashboard: http://{cfg.dashboard.host}:{cfg.dashboard.port}")
    asyncio.run(o.run_live())
    return 0


async def _replay_then_hold(o, days, pace) -> None:
    await o.start()
    try:
        await o.feed.replay(days, pace)
        print("replay finished — dashboard stays up, Ctrl-C to exit")
        await asyncio.Event().wait()
    finally:
        await o.stop()


def cli() -> int:
    try:
        return main()
    except KeyboardInterrupt:
        return 130
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # network / API failures at startup
        import httpx
        if isinstance(exc, httpx.HTTPError):
            print(f"\nERROR: could not reach {getattr(exc.request, 'url', 'the API')}: {exc}", file=sys.stderr)
            return 2
        raise


if __name__ == "__main__":
    sys.exit(cli())
