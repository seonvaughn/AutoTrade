---
name: run-scalpcity
description: Launch Scalp City's bots and 3D city dashboard and confirm a change works in the real app - a replay (no keys), a short paper run against Alpaca, or a headless-browser walkthrough of the city (towers, robots, building interiors) with screenshots. Use when asked to run, start, demo, screenshot or smoke-test the bots or the dashboard, or after changing anything in scalpcity/ or dashboard/.
---

# Run and check Scalp City

Read `CLAUDE.md` first for the safety rules. Everything here is **paper or simulated**. Never use
`mode: live`, `live_trading_enabled: true` or the live Alpaca host.

Put throwaway configs, databases, logs and screenshots in your scratchpad, not the repo
(`data/` and `reports/` are gitignored, but keep the owner's real `data/scalpcity.db` clean).

## 0. Fast checks (always)

```bash
python -m pytest -q                                              # all offline, < 20 s
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source  # CI blockers
```

## 1. See the city without any keys: synthetic replay

```bash
S=<scratchpad>
sed "s#db_path: data/scalpcity.db#db_path: $S/ui.db#" config.yaml > $S/ui.yaml
python -m scalpcity --config $S/ui.yaml replay --day 2026-10-15 --source synthetic --pace 0.15
```

Run it in the background. The dashboard is at `http://127.0.0.1:8765` within ~5 s. The replay
keeps serving after the day ends (stop it when done). Synthetic P&L means nothing.

## 2. Walk the city in a headless browser

Chromium and the Node Playwright package are preinstalled in cloud sessions
(`/opt/node22/lib/node_modules/playwright`, browsers in `/opt/pw-browsers`; never run
`playwright install`).

```bash
node scripts/dashboard_smoke.mjs http://127.0.0.1:8765 $S/shots
```

It loads the city, opens a tower, visits every floor, exits, opens a robot card,
repeats on a phone-sized viewport, saves PNGs, and exits non-zero on any page error. Read the
PNGs and look at them: the canvas must show towers and robots, the interior must show floor
buttons and content, and the chart must have candles.

With the research gate on (the default), a real-data replay starts by studying the previous 5
sessions; expect many `🔎 no trade` vetoes in thoughts and few trades. Check a tower's **Research
room** floor: track records, marked levels and the day's decisions. On synthetic prices almost
everything is vetoed; that's correct.

Known failure: a TDZ error such as `Cannot access 'px' before initialization` means a local
variable in `dashboard/app.js` shadows a module-level helper.

## 3. Live data, paper account (needs keys)

Needs `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY` in the environment, and network access to
`paper-api.alpaca.markets`, `data.alpaca.markets` and `stream.data.alpaca.markets`.

```bash
sed "s#db_path: data/scalpcity.db#db_path: $S/paper.db#" config.yaml > $S/paper.yaml
timeout -s INT 45 python -u -m scalpcity --config $S/paper.yaml paper > $S/paper.log 2>&1
```

Healthy log: `PAPER account: equity ...`, `backfilled N bars`, `Alpaca iex stream connected`.
A `no market data ... pausing entries` line must be followed by `market data back`. Ctrl-C
(SIGINT) flattens any position before exiting, so `timeout -s INT` is safe. US options paper
runs (`config.yaml`) only see data 9:30-16:00 ET on trading days.

## 4. Backtests on real data

```bash
python -m scalpcity backtest --start 2026-09-01 --end 2026-10-15 --source alpaca --out $S/reports
```

With `sim.use_historical_option_bars: true` (the default) each traded contract-day is one request,
so months of 12 tickers take hours on a cold cache. Cloud background jobs stop at 2 hours: run
shorter ranges, or reuse a warm `data/` cache. Report the numbers as they are, including losses.

## Stopping background runs

Don't `pkill -f` a pattern that also appears in your own shell's command line (it kills the shell).
Use `for p in $(pgrep -f "replay --day"); do [ "$p" != "$$" ] && kill $p; done`, or stop the
background task by its ID.
