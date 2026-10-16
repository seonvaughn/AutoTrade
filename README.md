# Scalp City: automated 0DTE options bots

A rebuild of the "Scalp City" system from the @NICKAFISCHER video. Python bots day-trade options on
QQQ, SPY and IWM using the three triggers he describes. A 3D city dashboard shows each bot as a
tower.

> "It trades stock options off a one-minute chart and has three triggers: a candle closes across the
> VWAP, a candle closes across the 50 EMA, or price breaks out of the first 15 minutes of range.
> Closing above means it's going to buy a call, closing below means it buys a put… Once you get up to
> a set amount, it will stop trading for the day."

**Read this first.** Nothing here is proven to make money. The video only showed a *replay*, never a
brokerage statement. Use this order: **backtest on real data → paper trade for weeks → tiny size
live**. Options can lose 100% of what you pay, and 0DTE options can do it in minutes.

---

## 1. How it works: 26 bots, one skill each

Bots never call each other to do things. Each one publishes events on a deterministic event bus, and
the bot that owns the next step reacts. Backtest, replay, paper and live run **the exact same bots**.
Only the price source and the broker plug-in change.

```
 price_feed ─▶ candles ─▶ atr / vwap / ema50 / opening_range ─▶ sig_vwap_cross / sig_ema50_cross / sig_orb
                                                                         │ Signal
                                                                         ▼
 signal_filter ─▶ contract_selector ─▶ position_sizer ─▶ risk_manager ─▶ execution ─▶ broker (Alpaca | sim)
                                                                         │ Fill
                                                                         ▼
 ledger ─▶ exit_manager (profit lock / target / stop / time / reversal / EOD / kill) ─▶ risk_manager ─▶ execution
   │
   └▶ daily_goal (clock-out + kill switch) · journal (THOUGHTS) · analyst (leaderboard) · dashboard
 clock · options_chain · health · reconciliation · alerts · orchestrator run alongside
```

| # | Bot | Its one skill |
|---|---|---|
| 1 | orchestrator | Build, wire, start, stop; on shutdown it flattens positions first |
| 2 | clock | Market session: new day, open, entry cutoff (15:30), flatten (15:55), close; knows holidays and half days |
| 3 | health | Detects stale data and failing bots; pauses new entries until healthy |
| 4 | candles | Builds 1-minute candles from the tick stream |
| 5 | options_chain | Option chain and live quotes for held contracts (Alpaca or Polygon live; Black-Scholes or real option bars in sim) |
| 6 | atr | ATR(14): the yardstick for "charge %" and filters |
| 7 | vwap | Session VWAP |
| 8 | ema50 | 50-period EMA of 1-minute closes |
| 9 | opening_range | High/low of 9:30–9:45 |
| 10 | sig_vwap_cross | Candle closes across VWAP: above = CALL, below = PUT |
| 11 | sig_ema50_cross | Candle closes across EMA50: above = CALL, below = PUT |
| 12 | sig_orb | Candle closes outside the 15-minute range (once per side per day) |
| 13 | signal_filter | Routes signals to workers; skips when busy, clocked out, cooling down, outside hours, weak close, or against trend |
| 14 | contract_selector | Picks expiry (0DTE/1DTE) and strike (ATM/OTM/ITM/delta); rejects wide spreads |
| 15 | position_sizer | Fixed contracts, a $ budget, or $ risk to the stop |
| 16 | risk_manager | Final yes/no on every entry (exposure, max positions, buying power, PDT, kill switch, health). Exits are always allowed |
| 17 | execution | Entries: limit at the ask with a timeout. Exits: walk the price down, then send a market order |
| 18 | ledger | Positions, realized/unrealized P&L per worker, the Vault total |
| 19 | exit_manager | Profit lock (trailing), target, stop, time stop, reversal, end-of-day flatten, kill switch |
| 20 | daily_goal | Clocks a worker out at its daily goal or loss limit; trips the kill switch on account-wide max loss (open losses count) |
| 21 | reconciliation | Every 60 s, checks the broker's real positions match the ledger; pauses on mismatch |
| 22 | journal | The readable THOUGHTS log: "setup forming", "FIRE ▲ CALL ×18 @ 3.68", "🔒 profit locked +$234", "🏆 daily goal · clocking out" |
| 23 | analyst | Leaderboard, win rate, expectancy, drawdown, end-of-day summary, backtest report |
| 24 | alerts | Logs alerts and optionally sends them to a Discord/Slack webhook |
| 25 | dashboard | The Scalp City 3D view (read-only, plus a kill switch button) |
| 26 | price_feed | Brings prices in: replayed bars or the live Alpaca (or Polygon) stream |

The five **workers** (towers) from the video are QQQ OG, QQQ TREND, QQQ, SPY and IWM. Each is just a
block in `config.yaml`: ticker, triggers, sizing, exits and daily goal. Add or remove towers by editing
that list.

## 2. Accounts you need

1. **Alpaca** (broker): <https://alpaca.markets>. Open an account, then use the **paper trading**
   keys first. Options must be enabled on the account (level 2 or higher to buy calls/puts). Options
   trades are commission-free; small regulatory fees still apply.
   - By default paper/live also take their **prices from Alpaca** (`data.live_data: alpaca`), using
     the same keys. The free feeds work: `iex` stock trades (real-time, but only the IEX exchange, a
     small share of all volume) and `indicative` option quotes (derived from the exchange feed, not
     the exchange quotes themselves). Alpaca's paid market data plan unlocks `sip` and `opra`, which
     are the full feeds. Set them under `data:` in `config.yaml`.
   - The free plan allows **one data stream per account**, so run one copy of the bots at a time.
2. **Polygon.io** (market data, now also branded Massive): <https://polygon.io>.
   - Backtests on real data need **minute history** for stocks. Turning on
     `sim.use_historical_option_bars` also needs options minute history.
   - Optional for paper/live: set `data.live_data: polygon` instead of Alpaca. That needs
     **real-time stock data with WebSocket access** and an **options plan that includes snapshots**.
3. Optional: a Discord or Slack **incoming webhook URL**, so critical alerts reach your phone.

## 3. Install

Requires Python 3.9+ (tested on 3.9 through 3.13; GitHub Actions runs the tests on every push).

```bash
cd scalp-city
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in your keys
set -a; source .env; set +a        # load keys into this terminal (Windows: set them in System Properties)
```

## 4. Run it

```bash
python -m scalpcity bots                                   # list the crew
python -m pytest                                           # 39 tests, all offline

# Backtest on REAL data (downloads Polygon minute bars to data/bars/ first)
python -m scalpcity backtest --start 2026-06-01 --end 2026-09-30 --source polygon

# Watch any past day play back in the 3D city (1 second per market minute)
python -m scalpcity replay --day 2026-10-02 --source polygon --pace 1
#   then open http://127.0.0.1:8765

# Paper trading (Alpaca paper broker + Alpaca live data), during market hours
python -m scalpcity paper
#   open http://127.0.0.1:8765. Ctrl-C closes open positions, then stops.
```

`--source synthetic` gives fake random prices with no account needed. It's good for checking that the
machinery works, but **its P&L means nothing**.

Backtests write a JSON report to `reports/`. Every fill, trade and thought goes to SQLite at
`data/scalpcity.db`.

## 5. Safety rails (all on by default)

- **Paper by default.** Live needs `live_trading_enabled: true` in the config **and**
  `SCALPCITY_LIVE_CONFIRM=I_UNDERSTAND_THIS_TRADES_REAL_MONEY` in the environment.
- **Per-worker daily goal and loss limit**: the worker clocks out for the day once either is reached.
- **Account-wide daily loss limit.** Open losses count too. Hitting it trips the kill switch, which
  flattens everything and stops trading for the day.
- **Kill switch button** on the dashboard.
- **Entry rules**: no new entries outside each worker's window or after 15:30. Everything is
  flattened at 15:55 (shifted on half days).
- **Max open positions, max premium at risk, spread and premium limits.**
- **Pattern-day-trader guard** for margin accounts under $25k.
- **Stale data or a position mismatch** pauses new entries and sends an alert.
- **Shutdown**: Ctrl-C flattens before exiting.
- **Exits are never blocked**: the risk manager always lets a closing order through.

## 6. Go-live checklist

1. Run backtests on **real Polygon data** over at least 3–6 months, with
   `use_historical_option_bars: true`. Is the profit factor above 1.2 *after* spreads? If not, stop
   here and tune.
2. Paper trade for **at least 4–8 weeks**, and compare paper fills to backtest expectations.
3. Check the PDT situation. A margin account under $25k is limited to 3 day trades per 5 days.
   FINRA has been changing this rule, so check the current status.
4. Go live with the **smallest size** (1–2 contracts per worker) and low daily limits. Scale up only
   after weeks of results that match paper.

## 7. Background

`docs/video-analysis.md` has the full breakdown of the original video: transcript, every on-screen detail, and how each part maps to a bot.

## 8. Known limits (be aware)

- **Backtest option prices** are modeled with Black-Scholes and a fixed IV per symbol, unless you
  turn on real option bars. Real 0DTE IV changes through the day, so modeled P&L is approximate.
- **Replay detail**: replay walks each 1-minute bar along a smooth open→low→high→close path. Real
  intra-minute moves are choppier, so stops and targets fill a bit worse live.
- **Mid-session start** in paper/live backfills today's candles via REST, so VWAP and the range
  are correct. The first partial minute may be slightly off.
- **The video's exact exit rules and sizing were not revealed.** The defaults here (lock profit
  after +4%, target +12%, stop −10%) are inferred from the trade sizes shown on screen. They are a
  starting point, not his settings.
- **Free Alpaca data is thinner than the full feed.** On `iex`, candles and VWAP come from IEX trades
  only. Prices track the market closely, but volume is a fraction of the total, and a quiet symbol
  (IWM is the likeliest) can go 30 s without a trade, which pauses new entries until one arrives.
  Raise `stale_data_seconds` if that happens often. `indicative` option quotes can be wider than the
  real market, so the spread filter may skip more contracts than it would with `opra`.
