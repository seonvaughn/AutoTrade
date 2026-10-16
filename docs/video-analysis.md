# "Scalp City" Trading Bot Video: Complete Analysis (Parts 1–3)

**Creator:** Instagram **@NICKAFISCHER**. The clip was edited in CapCut and has burned-in word-by-word captions.
**Footage:** a phone filming a curved gaming monitor (Lenovo / MSI "Optix MAG Series") that runs a 3D browser dashboard.
**Method:** every clip was read frame by frame (2 fps overview, full-resolution stills at key moments) and the captions were read at 4 fps to get the transcript. Speech-to-text could not run here because the model hosts are blocked by the network, so the transcript comes from the creator's own captions.

| File you sent | Length | Actual position in the video |
|---|---|---|
| "Part 2" (`aa2020e0…`) | 17.0 s | **1st**: intro |
| "Part 3" (`68003168…`) | 32.0 s | **2nd**: the strategy explanation |
| "Part 1" (`784fb91f…`) | 45.0 s | **3rd**: inside the towers, then the outro |

The clips join seamlessly. Clip A ends "…so I'll go", clip B starts "ahead and explain…". Clip B ends "So we'll go ahead and just click", and clip C starts "So we'll go ahead and just click QQQ…".

---

## 1. Full transcript in correct order

> **[Intro]** "What you're looking at here is a city dashboard type view that I built for my **Python bots** that are represented by these turrets and they day trade stock options for me. It looks like when Friday we made almost **$5,000**. There was a lot of questions in the last video on how this thing is working, so I'll go…
>
> **[Strategy]** …ahead and explain what it trades and then go ahead and show you around this thing again. So quickly, what it does is it trades stock options off a **one-minute chart** and has **three triggers**: **A candle closes across the VWAP, a candle closes across the 50 EMA, or price breaks out of the first 15 minutes of range.** Closing **above** it means it's going to **buy a call**, and closing **below** means it buys a **put**. It's buying **one day to expiration options**. Once you get up to a **set amount, it will stop trading for the day**. If you go ahead and look at the sides over here, these are the charts for each stock. So we'll go ahead and just click…
>
> **[Tour]** …QQQ and you can see the actual trades that are happening. So we are in one of the QQQ towers here. And as you can see, these are the signals that it was looking for that day, and here's [the] times and here's how much profit it got in, or it might lose. So it is charging up right now for a put. And then here is how much profit it has made so far. Every tower is like this inside. It shows each bot. There's five of — this one trades QQQ. And here's the leaderboard over here, just to show how much each one is made today, or maybe lost. These green beams are when a call is building, and then it fires, and then a red beam is a put signal building and then it fires. That one just lost."

---

## 2. The trading strategy, written as rules

He states these rules directly in the narration.

| Item | Rule |
|---|---|
| Instruments | Options on index ETFs: **QQQ, SPY, IWM** |
| Timeframe | **1-minute candles** |
| Trigger 1: VWAP cross | 1-min candle **closes** on the opposite side of session VWAP from where the prior candle closed |
| Trigger 2: EMA50 cross | 1-min candle **closes** across the 50-period EMA |
| Trigger 3: Opening Range Breakout | Price breaks above the high or below the low of the **first 15 minutes** (9:30–9:45 ET) |
| Direction | Close **above** the level → **buy CALL**. Close **below** → **buy PUT**. Long premium only; no selling or spreads. |
| Expiry | He says "one day to expiration". **But** the city has a "0DTE" district sign, and a fill of $3.68 for a near-the-money QQQ call at about $752 with 6 hours left matches **0DTE** pricing. A 1DTE option would cost roughly $5–6. **This must be a config setting**, and we test both. |
| Exit | Take-profit / trailing "🔒 profit locked", or "STOPPED OUT". Cancel the setup if price moves away ("setup faded, standing down"). |
| Daily stop | Stop trading for the day once a set profit goal is reached ("daily goal +$1,756 · clocking out"). |

### Details read from the screen
- **"Charge %"** is how close price is to the trigger level, measured in **ATR units**. Examples: `VWAP cross ▼ PUT · 0.66 ATR away` = 38% charged, `0.38 ATR` = 75%, `0.00 ATR` = fire.
- **Size varies by bot.** QQQ OG uses 14–37 contracts, QQQ TREND 4–5, QQQ 3.
- **Real trade log from QQQ OG on Fri 10/2:**
  - 9:35 ▲ 14 calls → +$462
  - 9:46 FIRE ▲ CALL ×18 @ 3.68 (QQQ 752.11) → +$234
  - 9:54 FIRE ▼ PUT ×20 @ 3.40 (QQQ 751.09) → +$320
  - ▼ PUT at EMA50 ×37 @ 3.50 → +$740
  - 10:52 "daily goal +$1,756 · clocking out"

---

## 3. The five bots ("workers" / "turrets")

| Bot | Underlying | Style | End of day Fri 10/2 |
|---|---|---|---|
| **SPY** | SPY | same 3-trigger engine | **+$2,337 (Top Worker)** |
| **QQQ OG** | QQQ | original 3-trigger, large size | about +$1,800 (goal hit at +$1,756) |
| **QQQ TREND** | QQQ | trend-following variant, small size, gets stopped out | about +$328 (was −$39 at 10:40) |
| **IWM** | IWM | same engine | about +$376 |
| **QQQ** | QQQ | small-size variant (3 contracts) | about +$42 |
| **Total** | | "5 workers · one trading day" | **+$4,839** |

Each bot follows the same lifecycle: **watching → setup forming / charging % → FIRE → in trade (WINNING/LOSING live) → profit locked or stopped out → (setup faded) → clock out at daily goal.**

---

## 4. Every screen in the app

1. **Scalp City overview:** 5 towers around **The Vault** (`+$X · 5 workers on shift · tap for payroll`). District signs read `0DTE`, `BUY THE DIP`, `VWAP`. Green beams mean a call is charging or firing; red beams mean a put. A ring pulse animates on fire, and floating badges show `▲ CALL ×5`, `🔒 PROFIT LOCKED +$66` and `STOPPED OUT −$xx`. Live mini-charts for each stock sit on the side walls.
2. **Tower label** (one per bot): name, state (`watching` / `charging ▲ CALL 83%`), and `earned +$X`.
3. **Inside a tower:** a robot worker at a desk with three screens:
   - Signal Scanner: current setup, ATR distance, charge bar, and the THOUGHTS log.
   - `QQQ · 1-MIN` chart with VWAP and EMA50 lines and a live `WINNING/LOSING ±$X` label.
   - EARNED panel: day P&L, trades, wins, win rate, and last trades.
4. **Trade chart:** `QQQ Fri 10/2 · 10:43 · 753.52 +0.46% · 9 trades`, with each trade marked on the chart along with its P&L.
5. **Leaderboard** and **Worker Heatmap** (green/red tiles), the `● MARKET OPEN · 10:40 ET · 5h 19m to close` banner, and a "MONEY NEVER SLEEPS" banner.
6. **End-of-day summary:** `FRI 10/2 +$4,839`, a bar chart per bot, `👑 TOP WORKER SPY +$2,337`, and **Replay** / **Close** buttons.
7. **HUD:** `REPLAY · FRI 10/2`, ET clock, `TO CITY`, camera `SIDE` / `WIDE`, a status line, and a "Trading rules for this bot" link.
8. **Bottom bar:** a calendar of daily P&L chips (Fri 9/4 → Fri 10/2; every day shown is green, the best being Tue 9/29 +$10.9k) and a scrolling fill ticker. Examples: `QQQ TREND 10:14 ▲ bought 4 CALL @ 3.64`, `QQQ TREND 10:15 sold +$76 · 🔒 profit locked`, `SPY 10:02 sold +$68`, `IWM 11:27 sold +$30`.

---

## 5. Honest assessment

**One correction to what I said after part 1:** the numbers are more consistent than I thought. The Vault's +$1.4–1.7k was mid-morning, and the day closed at +$4,839, which matches the calendar chip for Fri 10/2.

**What still needs proving:**
1. **Everything shown was a replay** ("REPLAY · FRI 10/2"), not live trading. The THOUGHTS log already contained 10:52 entries while the clock read 9:50.
2. **No brokerage statement is shown.** These could be paper or simulated fills, which are typically optimistic for options (no slippage on wide spreads).
3. **20 green days out of 20** isn't how real 0DTE scalping behaves. This is marketing content.
4. The rules themselves (VWAP cross, EMA cross, ORB) are **well-known, simple signals**. Any edge comes from the exits, sizing and filters, which he doesn't fully reveal.

**Conclusion:** we can replicate this system faithfully. Whether it makes money must be proven by our own backtest plus weeks of paper trading before any real capital goes in.

---

## 6. Our build: one bot per skill

Python backend (as he uses), an async event bus, and a web dashboard. Every bot does exactly one job and talks only through events.

### Data layer
| # | Bot | Single skill |
|---|---|---|
| 1 | **Clock Bot** | Market calendar, session state, holidays, half-days, "Xh to close"; broadcasts OPEN / CLOSE / opening-range-done events |
| 2 | **Price Feed Bot** | Streams real-time trades and quotes for SPY, QQQ, IWM |
| 3 | **Candle Bot** | Builds clean 1-minute OHLCV candles and emits `CANDLE_CLOSED` |
| 4 | **Options Chain Bot** | Streams the option chain (0DTE / 1DTE) with bid, ask, greeks and spreads |

### Indicator layer
| 5 | **VWAP Bot** | Session VWAP from 9:30 |
| 6 | **EMA Bot** | EMA(50) on 1-min closes, warmed up with prior-day data |
| 7 | **ATR Bot** | ATR used for distance / "charge %" and stop sizing |
| 8 | **Opening Range Bot** | High and low of 9:30–9:45; publishes when locked |

### Signal layer (one bot per trigger, so each is independently testable)
| 9 | **VWAP Cross Signal Bot** | Candle closes across VWAP → CALL/PUT signal plus charge % |
| 10 | **EMA50 Cross Signal Bot** | Candle closes across EMA50 → signal |
| 11 | **ORB Signal Bot** | Breakout of the 15-min range → signal |
| 12 | **Signal Filter Bot** | Removes chop: dedupes simultaneous triggers, applies cooldowns, enforces a minimum ATR, blocks the last 15 minutes |

### Decision and risk layer
| 13 | **Contract Selector Bot** | Picks the strike and expiry (ATM/delta target, 0DTE or 1DTE) and rejects wide spreads |
| 14 | **Position Sizer Bot** | Converts risk-per-trade dollars into a contract count |
| 15 | **Risk Manager Bot** | Final yes/no on every order: max loss/day, max open positions, buying power, PDT rule |
| 16 | **Daily Goal / Kill-Switch Bot** | "Clocks out" a worker at its profit goal or loss limit; global emergency stop |

### Execution layer
| 17 | **Order Execution Bot** | Sends limit orders to the broker API and handles partial fills, timeouts and retries |
| 18 | **Exit Manager Bot** | Take-profit, trailing "profit lock", stop-loss, and time-stop before close; flattens everything by 3:55 pm |
| 19 | **Reconciliation Bot** | Every minute, confirms broker positions match what the bots think they hold |

### Record-keeping and analysis layer
| 20 | **Ledger Bot** | Records every fill; P&L per worker, per day, and Vault total |
| 21 | **Journal Bot** | Writes the "THOUGHTS" log (setup forming, FIRE, profit locked, setup faded, clocking out) |
| 22 | **Backtest / Replay Bot** | Replays historical days through the exact same bots, including his REPLAY mode |
| 23 | **Performance Analyst Bot** | Leaderboard, win rate, expectancy, drawdown, end-of-day summary |

### Operations and display layer
| 24 | **Health Monitor Bot** | Detects stale data, feed lag and broker disconnects; alerts you by phone and pauses trading |
| 25 | **Orchestrator Bot** | Starts and stops workers and wires each "worker" (ticker + strategy config) to the shared bots |
| 26 | **Dashboard Bot** | The Scalp City 3D view (towers, beams, vault, heatmap, leaderboard, replay); read-only |

A **"worker"** (SPY, QQQ OG, QQQ TREND, IWM, QQQ) is just a config: ticker, enabled triggers, size, and daily goal. It runs through bots 9–18, which is how he gets 5 towers from one codebase.

### Build order
1. Data + indicators + signals + **Backtest Bot**, to verify the strategy on history first.
2. Ledger, Journal and Analyst, so we can see the results.
3. Paper trading through the broker's paper API, with Risk, Exit, Kill-switch, Reconciliation and Health bots.
4. The Scalp City dashboard.
5. Live trading with small size, and only after paper results justify it.
