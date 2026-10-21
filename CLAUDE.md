# Scalp City: notes for coding agents

Automated day-trading bots (options on US stocks/ETFs only) with a 3D
"city" dashboard. Owner: seonvaughn. User-facing docs: `README.md`. Strategy background:
`docs/video-analysis.md` (the original video) and `docs/tjr-bootcamp/` (TJR's boot camp, the strategy the
towers trade now: start with its `README.md`).

## Safety rules (never break these)

- **Paper only unless the owner says otherwise in their own words.** Never set
  `live_trading_enabled: true`, never set `SCALPCITY_LIVE_CONFIRM`, never point a broker at
  `api.alpaca.markets` (live). Paper is `paper-api.alpaca.markets`.
- Never print, log, commit or paste API keys. `.env` is gitignored; keep it that way. To check a
  key is loaded, print only its first 4 characters.
- Don't weaken a safety rail (kill switch, daily loss limits, flatten time, stale-data pause,
  position reconciliation, PDT guard) to make a test or backtest pass.
- Report backtest results honestly, losses included. Nothing here is proven profitable.
- **Options only.** The owner removed crypto on 2026-10-21 and wants it kept for a separate crypto city later
  (`docs/crypto-city-archive.md` lists every crypto file and bot; all of it is in commit `7a28e85`). Don't add crypto
  back to this city.
- The owner wants "no guessing": every entry must clear the research gate (evidence from past
  sessions). Don't add a path that opens a position without a `ResearchCleared` event, and don't
  promise accuracy or profits: say what the evidence shows and what it can't.

## Layout

```
scalpcity/
  __main__.py        CLI: bots | backtest | replay | paper | live | download
  orchestrator.py    builds and wires the bots (37 with config.yaml; legacy trigger bots only when traded); BOT_ORDER = event delivery order (it matters)
  core/              events (the bus messages), bus (deterministic), config, calendar, costs, storage
  bots/              one skill per bot; they talk only through events on the bus
  brokers/           alpaca.py (paper/live), sim.py (backtest/replay)
  data/              alpaca_data.py (live + history), polygon.py, bars.py (CSV cache), option_bars.py, live.py
dashboard/           index.html, app.js (three.js r160, vendored), style.css: the city
tests/               pytest, all offline (mocked HTTP), ~60 tests, < 20 s
config.yaml          options workers (12 towers)      -> dashboard :8765, data/scalpcity.db
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
- **Chart reading (bots/chart_bots.py + three triggers in signal_bots.py).** `timeframes` emits
  `BarClosed(tf)` for 30s/5m/15m/30m/1h (1m stays `CandleClosed`); history's 30s bars are split from
  1m bars along `PriceFeedBot.path`. `htf_levels` loads daily candles (`data/daily.py`, cached in
  `data.daily_dir`) for the replay span (`ctx.span`) or live, and `study(sym, day)` uses only days
  before `day`. `structure` (swings, trend, breaks, Fibonacci) and `zones` (supply/demand) are
  read-only queries for the triggers `zone_reaction` (30s), `structure_break` (5m), `fib_pullback`
  (1m) and for the gate (`research.align_timeframes`, zones as obstacles). The owner asked for a
  95% win rate: don't promise it; report win rate *and* profit factor.
- **TJR model (bots/smc_bots.py, docs/tjr-bootcamp/README.md maps every rule to code).**
  - `market_structure`: TJR's two-candle highs and lows. A break of structure is a candle BODY closing beyond the most
    recent high or low; wicks never count.
  - `liquidity`: resting highs and lows per timeframe plus the prior day's; records sweeps.
  - `imbalances`: three-candle fair value gaps. `order_blocks`: the leg that swept, marked at the break.
  - `daily_bias`: the last daily break, from days before the session; also the daily equilibrium and the 4h trend.
  - `news_calendar`: blackout days, a wait after releases, half-size days.
  - `sig_smc` (trigger `smc_retrace`): a sweep then a break on 5m/15m; then a retrace into an order block or FVG in
    the discount/premium half; then a break one timeframe lower. The Signal carries `stop` (beyond the swept extreme)
    and `target` (the next resting liquidity ≥ min_rr).
  - `research_gate.check_tjr`: news; daily bias must agree; when the 1h/4h oppose it, a 15m setup and price in the
    daily premium/discount; reward:risk.
  - The edge tracker scores chart-planned signals at their own stop/target, counts only setups the plan would have
    taken (`in_plan`: bias, window, news), pools tickers (`research.pooled_triggers`) and judges them on expectancy
    (avg R), not win rate.
  - Exits: `exits.measure: structure`. Sizing: `mode: risk` from the chart stop × delta. `risk.max_trades_per_day`
    caps the whole account (1, TJR Day 29).
  - `morning_study` (07:00 ET, `research.morning_study`): per ticker, news + daily bias + the setup record
    (`research.edge_lookback_days`, 20) → `MorningPlan` cleared/stood down; `check_tjr` refuses TJR entries without
    a cleared plan. `scripts/morning_autostart.sh install` starts the options city at 6:50 on the owner's Mac.
  - `smc.bias_mode` with|against|any and `smc.target_mode` liquidity|fixed. Shipped: against + fixed 1R (the only
    variant that held up on unseen months; see `docs/research-log.md`, which also counts every variant tried).
  - Contract scout (`strike: auto`, `contract_selector.scout`): prices each liquid contract's gain/loss at the plan's
    target/stop halfway through the hold (BS with the quote's IV, time decay included) minus the spread; picks the
    best ratio; refuses if none profits at the target.
  - Learning (bots/learning_bots.py):
    - `trade_review` writes a review after every trade. Wins say what went right. Losses are classified:
      setup_failed, stop_too_tight (target reached after the stop), out_of_time, option_costs.
    - `lessons` tallies every in-plan scored setup (`SetupScored` from the edge tracker) by feature. A feature becomes
      an avoid/favor rule only with n ≥ `research.lessons_min_n` (30) and |t| ≥ `lessons_t` (2.5). The gate enforces
      avoid rules. The book persists at `research.lessons_path` and dedupes replayed history. Never make a rule from
      one trade.
  - Keep it faithful to the notes: when changing a rule, cite the day it comes from. When the evidence overrides
    TJR, say so and log it in `docs/research-log.md` (discovery period, holdout once, trial count).
- **Options course (docs/options-course/README.md, SkyView Trading playlist).** Entries try a limit at the mid first,
  then the ask (`broker.entry_mid_first`; the sim never fills at the mid, so backtests are unchanged).
  `risk.max_delta_leverage` caps the stock-equivalent exposure of open options (|delta| × qty × multiplier × price)
  at that many times equity. The journal explains each pick: break-even, delta (≈ chance ITM), decay per hour. The
  course itself argues against buying options for direction (it sells premium); that, and debit verticals, are
  documented as owner decisions, not built.
- **Never price a backtest fill from a stale option trade.** `SimChain._from_last_trade` moves the
  last real trade by delta × the stock's move since that trade. Using the last trade as-is let the
  bots "buy" at prices from before the move that fired the signal: a losing strategy showed
  +$41k with zero drawdown. Results that look too good (no red days, ~0 drawdown, 80%+ wins) are a
  bug until proven otherwise: compare against `use_historical_option_bars: false`.
- **History must be delivered candle by candle** (`PriceFeedBot._history`: emit, then drain, per
  candle). Queuing all history first and draining once made every past signal see only later
  days, and the edge tracker scored them all as 0R timeouts. Anything time-ordered depends on this.
- **Instruments.** `OptionContract` only (multiplier 100, whole contracts; `Instrument` is an alias). Use
  `contract.multiplier`, `costs.fees()` and `costs.round_qty()`; never hard-code `* 100`. Config refuses a symbol with
  a "/" (a coin pair). `AlpacaBroker.positions()` returns option positions only, so stock or coins in the account
  never trip reconciliation.
- **Expiries.** The contract selector walks forward from `dte` to the nearest listed expiry (up
  to 7 trading days). The simulator models listed weekdays per symbol in
  `sim.expiry_weekdays` (Fridays if unlisted). In Oct 2026: SPY/QQQ/IWM daily; NVDA, AAPL, META,
  AMZN, AMD, MSFT Mon/Wed/Fri; TSLA Mon/Fri. Live uses the real chain.
- **Data.** Paper/live prices come from Alpaca by default (`data.live_data: alpaca`; free feeds
  `iex` stocks and `indicative` options). Polygon is optional. Backtests: `data.source: alpaca`
  (fast, SIP history) or `polygon` (free plan about 5 req/min, unusably slow for months).
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
- Wants the city live and explorable. Outside market hours, use a replay (`run-scalpcity` skill).

## Status (2026-10-17)

- Work branch: `claude/blissful-ride-nikmtn`. No PR opened yet.
- Done: Alpaca live data, seven single-stock option towers, nearest-expiry
  selection, Alpaca historical source, walkable city (robots, building interiors, Vault), phone
  access token, macOS certificate fix, double-click launchers (`Start … City.command`), research
  bots (key levels, edge tracker, research gate) with a Research room in every tower.
- **Backtest results before 2026-10-17 that used real option bars are invalid** (stale-price bug,
  below), including a +$41,310 / 88.7% win / 32-of-32 green run for 2026-09-01..10-15 and a +$1,418
  single day. With model prices the same gated run was −$5,615, 40.8% wins, profit factor 0.53.
- **Corrected baseline (2026-09-01..10-15, real option bars with the stale-price fix, research gate
  on, config.yaml as shipped):** −$5,620, 234 trades, 38.9% wins, profit factor 0.43, 2 green /
  16 red / 14 flat days. Exits: 92 stops (−$8,324), 21 targets (+$2,508), 73 profit locks
  (+$1,708), 48 reversals (−$1,512). The gate scores edge with ATR-based stops/targets on the stock,
  but positions exit on −10%/+12% of option premium, which 0DTE noise hits fast: aligning the
  exits with what the gate measured is the obvious next experiment. 790 entries were blocked by
  the PDT guard once the $30k sim account fell below $25k.
- **Aligned-exits experiment (same period, `exits.measure: underlying`, 0.7/1.0 ATR, 20 min, no
  reversal exits):** −$5,444, 201 trades, 38.8% wins, profit factor 0.53. 122 stops (−$11,509) vs
  79 targets (+$6,065). Matching the exits to the gate's yardstick changed almost nothing: triggers
  "proven" over the past 5 sessions won ~39% going forward, below the 45% the gate required. The
  past-5-session edge does not persist, so the gate is selecting noise. Shipped config still uses
  premium exits.
- **Six-strategy run (charts + gate, before TJR):** −$5,423, 363 trades, 44.6% wins, profit factor 0.58, 5 green /
  20 red days. Every indicator/chart trigger lost; they remain in the code but no tower trades them.
- **TJR boot camp (2026-10-17):** 45 of 46 videos studied (`docs/tjr-bootcamp/`). **Day 21 ("How to Take a Win",
  https://www.youtube.com/watch?v=z9p7OThLkr4) is still missing.** YouTube blocks the cloud server, so ask the owner to
  paste its transcript, then read it in full and write `21-how-to-take-a-win.md`.
- **News dates:** the 2026 FOMC days are in `config.yaml`. The CPI/PPI/NFP dates there are unverified (bls.gov is
  unreachable from cloud sessions) and incomplete. Ask the owner to check https://www.bls.gov/schedule/.
- **TJR first results (2026-10-17):**
  - Backtest Sep 1–Oct 15 (real option bars, gate on): −$412, 4 trades (1 win), PF 0.15. 106 entries vetoed, mostly
    "no edge" over the past 5 sessions. Too few trades to judge.
  - Raw setup record Jun 1–Oct 15, all 10 tickers, scored on the underlying at each setup's own stop/target within
    120 min:
    - all 2,090 setups: 22% wins, −0.011R avg, PF 0.97
    - the 208 setups the plan would take (bias, 09:35–11:00, no news): 20% wins, −0.039R, PF 0.91
    - 44% timed out before either level
  - Following TJR's filters did not improve the record. Per-ticker splits (n 15–31) are noise; don't cherry-pick
    them. As coded, the model is break-even-to-negative before option costs.
  - Next experiments: closer targets (TJR TP1 = first liquidity one timeframe up), the time limit, and whether
    "prominent" liquidity (the prior day only, or 1h+) changes it.
- **2026-10-20 evidence-based settings** (docs/research-log.md, docs/research/evidence-based-intraday-strategies.md):
  - Discovery Jun–Aug (~810 variants), then a holdout on Sep–Oct run once.
  - Variant A (retrace against the daily bias, 1R, hold to close): 44 holdout setups, 55% wins, +0.15R, PF 1.41 on
    the underlying. Not statistically significant (t ≈ 1.6).
  - Backtest Sep 1–Oct 15 with real option bars (delta 0.70, 2 DTE, morning study): 4 trades, 2 wins, −$233. The
    morning study stood the towers down on most days because the 20-session record wasn't proven.
  - Backtests with every agent on (real option bars): Jun–Aug 16 trades, 43.8% wins, −$227, PF 0.87; Sep–Oct 4 trades
    −$233 (0.70 delta) / −$529 (scout). Not profitable yet; see docs/research-log.md.
- A 65% win rate is only reachable with 0.5R targets, and those lose (PF 0.98). Don't chase it.
- The owner wants a high win rate and no guessing. Report win rate AND expectancy/PF; never tune toward a win-rate
  number alone.
- Towers now trade `smc_retrace` only, 09:35–11:00, one trade a day for the account, $300 risk (1%). QQQ TREND and QQQ
  are disabled (same ticker as QQQ OG).
- **2026-10-20:** TJR with all fixes, Jun 1–Oct 15, real option bars: −$151, 45 trades, 48.9% wins, PF 0.97.
  New trigger `orb_ntz_retest` (docs/videos/boring-orb-ntz.md; `data/premarket.py` caches pre-market ranges):
  discovery +0.094R/PF 1.31 (n 98), holdout −0.022R/PF 0.93 (n 29), not confirmed. Towers now paper-trade
  `[smc_retrace, orb_ntz_retest]` behind the gate. The owner is starting live paper trading on the Mac.
- **2026-10-21:** crypto removed (options only; `docs/crypto-city-archive.md`). Afternoon session 13:00–15:00 for a
  missed morning, judged on its own record (afternoon lost in both test periods). Morning study now judges each
  strategy apart. Backtest Jun 1–Oct 15 as shipped: −$274, 48 trades, 47.9% wins, PF 0.94. The owner is starting
  live paper trading in the city.
