# Scalp City: notes for coding agents

Automated day-trading bots (0DTE options on US stocks/ETFs, plus a crypto edition) with a 3D
"city" dashboard. Owner: seonvaughn. User-facing docs: `README.md`. Strategy background:
`docs/video-analysis.md`.

## Safety rules (never break these)

- **Paper only unless the owner says otherwise in their own words.** Never set
  `live_trading_enabled: true`, never set `SCALPCITY_LIVE_CONFIRM`, never point a broker at
  `api.alpaca.markets` (live). Paper is `paper-api.alpaca.markets`.
- Never print, log, commit or paste API keys. `.env` is gitignored; keep it that way. To check a
  key is loaded, print only its first 4 characters.
- Don't weaken a safety rail (kill switch, daily loss limits, flatten time, stale-data pause,
  position reconciliation, PDT guard) to make a test or backtest pass.
- Report backtest results honestly, losses included. Nothing here is proven profitable. The crypto
  edition has lost money in every backtest so far (README, "Known limits").
- The owner wants "no guessing": every entry must clear the research gate (evidence from past
  sessions). Don't add a path that opens a position without a `ResearchCleared` event, and don't
  promise accuracy or profits: say what the evidence shows and what it can't.

## Layout

```
scalpcity/
  __main__.py        CLI: bots | backtest | replay | paper | live | download
  orchestrator.py    builds and wires the 29 bots; BOT_ORDER = event delivery order (it matters)
  core/              events (the bus messages), bus (deterministic), config, calendar, costs, storage
  bots/              one skill per bot; they talk only through events on the bus
  brokers/           alpaca.py (paper/live), sim.py (backtest/replay)
  data/              alpaca_data.py (live + history), polygon.py, bars.py (CSV cache), option_bars.py, live.py
dashboard/           index.html, app.js (three.js r160, vendored), style.css: the city
tests/               pytest, all offline (mocked HTTP), ~60 tests, < 20 s
config.yaml          options workers (12 towers)      -> dashboard :8765, data/scalpcity.db
config.crypto.yaml   crypto workers (BTC, ETH, SOL)   -> dashboard :8766, data/scalpcity-crypto.db
```

Backtest, replay, paper and live run the exact same bots; only the price source and broker
change. Bots never call each other to *do* things: they publish events, and the owner of the next
step reacts. `ctx.bots[...]` is for read-only queries only.

## Commands

```bash
pip install -r requirements.txt
python -m pytest -q                                                   # must stay green
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source       # what CI fails on
python -m scalpcity bots                                              # list the crew
python -m scalpcity backtest --start 2026-09-01 --end 2026-10-15 --source alpaca
python -m scalpcity replay --day 2026-10-15 --source synthetic --pace 0.15   # city demo, no keys
python -m scalpcity paper                                             # options, market hours
python -m scalpcity --config config.crypto.yaml paper                 # crypto, any time
```

CI (`.github/workflows/python-package.yml`) runs Python 3.9, 3.10 and 3.11. Keep code 3.9
compatible: `from __future__ import annotations` in every module, no `match`, no `X | Y` outside
annotations. Check with `uv run --no-project --python 3.9 --with-requirements requirements.txt
python -m pytest -q`.

To see the city working, use the `run-scalpcity` skill (`.claude/skills/run-scalpcity/`).

## Design facts worth knowing before you edit

- **Research gate (bots/research_bots.py).** `key_levels` marks levels from the last
  `research.lookback_days` sessions; `edge_tracker` scores every signal (history included) on the
  underlying: target_atr before stop_atr within horizon_minutes; `research_gate` sits between
  `signal_filter` (WorkerSignal) and `contract_selector` (which listens to `ResearchCleared`) and
  emits `EntryVetoed` with a reason otherwise. Signals fired on history carry `backfill=True`: the
  edge tracker studies them, while the filter and exit manager ignore them. Mechanics tests turn the
  gate off in `make_cfg()`; research behaviour is tested in `tests/test_research.py`.
- **History must be delivered candle by candle** (`PriceFeedBot._history`: emit, then drain, per
  candle). Queuing all history first and draining once made every past signal see only later
  days, and the edge tracker scored them all as 0R timeouts. Anything time-ordered depends on this.
- **Markets.** `config.market` is `options` or `crypto`; `calendar.set_market()` switches the
  whole process (the orchestrator and `config.load` call it). Crypto days run 00:00 to 24:00 ET,
  every day. Tests reset to `options` through an autouse fixture in `tests/conftest.py`.
- **Instruments.** `OptionContract` (multiplier 100, whole contracts) and `CryptoAsset`
  (multiplier 1, fractional qty, long only). Use `contract.multiplier`, `contract.kind`,
  `costs.fees()`, `costs.round_qty()` and `costs.QTY_EPS`; never hard-code `* 100`, `int(qty)` or
  `qty <= 0`. `OptionQuote` carries either instrument.
- **Expiries.** The contract selector walks forward from `dte` to the nearest listed expiry (up
  to 7 trading days). The simulator models listed weekdays per symbol in
  `sim.expiry_weekdays` (Fridays if unlisted). In Oct 2026: SPY/QQQ/IWM daily; NVDA, AAPL, META,
  AMZN, AMD, MSFT Mon/Wed/Fri; TSLA Mon/Fri. Live uses the real chain.
- **Data.** Paper/live prices come from Alpaca by default (`data.live_data: alpaca`; free feeds
  `iex` stocks and `indicative` options). Polygon is optional. Backtests: `data.source: alpaca`
  (fast, SIP history) or `polygon` (free plan about 5 req/min, unusably slow for months).
  Crypto candles come from quote midpoints (Alpaca's crypto trades are too sparse), and
  `bars.fill_gaps` fills quiet minutes in crypto replays so the stale-data check doesn't pause.
- **Crypto fees.** Alpaca takes the fee out of the coin received, so holdings run slightly short:
  `AlpacaBroker.submit` sells what is really held on a full exit and scales the reported fill,
  and `ReconciliationBot.matches` allows 2% on fractional quantities.
- **Dashboard.** `DashboardBot` serves FastAPI + one WebSocket. State includes `crew` (per-bot
  activity from `EventBus.activity`) and per-worker `settings`/`crew` for the building
  interiors. Off-localhost access needs `SCALPCITY_DASHBOARD_TOKEN` (query `?token=` once, then a
  cookie); `start()` refuses a non-loopback host without it. In `app.js`, module-level `const`
  names are shared: don't shadow helpers like `px`, `qty`, `money` with locals (a shadowed `px`
  once broke the chart with a TDZ error).

## Environment gotchas (learned the hard way)

- **macOS python.org builds have no trusted root certificates** for the `ssl` module. httpx
  bundles certifi, so REST works, but WebSockets fail with `CERTIFICATE_VERIFY_FAILED`. Streams
  pass `ssl=tls_context()` (certifi) for this reason; keep it on any new socket.
- **Alpaca data rate limit** is ~200 requests/min on the free plan; `_get` retries 429 with
  backoff. Don't run two big downloads at once.
- **Long backtests with real option bars are slow** (one request per contract-day; ~22,000 files
  for 12 tickers over June to mid-October 2026). In a cloud session, background jobs stop after
  2 hours: run shorter ranges there, or let the owner run long ones locally. Bars cache under
  `data/bars/` and `data/option_bars/`, so reruns are fast.
- With `--source synthetic`, real option bars are skipped (synthetic strikes don't exist).
- `pkill -f <pattern>` from a shell whose own command line contains the pattern kills that
  shell. Match on something narrower, or skip `$$`.

## Owner context

- Runs the bots on a **Mac** (Python 3.15, Terminal, zsh), repo at `~/AutoTrade`, virtualenv
  `.venv`. New to the command line: give one step at a time, say what success looks like, and ask
  them to paste output.
- Alpaca **paper** account with options level 3. Polygon key is a free-tier plan: stock and
  option minute history only; no real-time WebSocket or option snapshots.
- Wants the city live and explorable; the crypto edition is how to see it outside US market
  hours.

## Status (2026-10-17)

- Work branch: `claude/blissful-ride-nikmtn`. No PR opened yet.
- Done: Alpaca live data, crypto edition, seven single-stock option towers, nearest-expiry
  selection, Alpaca historical source, walkable city (robots, building interiors, Vault), phone
  access token, macOS certificate fix, double-click launchers (`Start … City.command`), research
  bots (key levels, edge tracker, research gate) with a Research room in every tower.
- One real-data day (2026-10-15, after studying 10-08..10-14) with the gate on: 15 trades on SPY,
  META, AMZN, IWM, +$1,418; every QQQ/TSLA/AAPL/MSFT trigger was vetoed for a losing record. One day
  proves nothing.
- Open: a full options backtest on real data has not finished yet (stopped at the 2-hour cloud
  limit). Run `backtest --start 2026-09-01 --end 2026-10-15 --source alpaca` first, then longer.
