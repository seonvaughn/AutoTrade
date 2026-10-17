# TJR boot camp: study notes and what the bots took from it

Source: the TJR boot camp playlist (46 videos,
https://youtube.com/playlist?list=PLDVXJ0hsxGL_K5M9jTLb2V_cLbWTz4ITR), read video by video from the full transcripts.
Each file has the source link, the concepts in TJR's own terms, his homework, and a "For the bots" section.

**Status: 45 of 46 videos read. Missing: Day 21 ("How to Take a Win & Life Lessons", 61 min,
https://www.youtube.com/watch?v=z9p7OThLkr4).**
- YouTube blocks transcript downloads from the cloud server, so Days 29, 33, 35, 36, 39 and 41 were pasted in by the
  owner.
- When Day 21 arrives, read it in full, write `21-how-to-take-a-win.md`, and check whether it changes any rule below.

## The strategy in one page (Days 4–46)
1. **Daily bias first** (Days 34–36): the direction of the last daily break of structure. The weekly is context. Trade
   only with the daily bias. A lower-timeframe break against it is a retrace, not a reversal.
2. **No news days** (Day 19): never CPI, PPI, FOMC or NFP. After other big releases, wait for price to settle.
3. **Session** (Day 29): the New York open. A trade within the first 1½ hours, or none.
4. **The setup** (Days 6, 8, 10, 12, 30):
   - a sweep of resting liquidity (old highs or lows taken),
   - then a **candle body** closing beyond the most recent high or low, which is the break of structure. Wicks never
     count.
5. **The entry** (Days 14–33, 41, 46):
   - a retrace into the **order block** (the move that made the sweep) or a **fair value gap**, in the **discount**
     (longs) or **premium** (shorts) half of the leg (equilibrium),
   - then a **break one timeframe lower**.
   - The bare sweep + break entry is the riskiest. TJR lost every trade with it in one week and switched to the
     retrace entries (Days 41, 46).
6. **Stop** beyond the swept high or low, plus spread (Day 38). **Target** the next resting liquidity, at least 1:1
   (Day 37).
7. **Risk** (Days 13, 29, 39): 1% per trade, 1–3% a day, **one trade a day while unproven**. Half size on de-risk days.
   Never "confident" double size until proven.
8. **Mindset** (Days 1, 3, 11, 15, 17, 25, 27, 31, 44, 45): no revenge trading, no overtrading, one strategy, one
   instrument. "Try not to trade": the market must give you the trade. No profitable trader wins every trade.

## Where each rule lives in the code
| Rule | Code |
|---|---|
| Two-candle highs and lows, body-close break, trend per timeframe | `scalpcity/bots/smc_bots.py` `Structure`, `market_structure` |
| Resting liquidity and sweeps (incl. prior day high/low) | `liquidity` |
| Fair value gaps (three-candle rule), fill tracking | `imbalances` |
| Order block (the leg that swept, at the break) | `order_blocks` |
| Daily bias, weekly, 4h, daily equilibrium (no look-ahead) | `daily_bias` |
| News blackout, wait after releases, half-size days | `news_calendar`, `config.yaml` `news:` |
| Setup → retrace → lower-timeframe break → signal with stop and target | `sig_smc` (`smc_retrace`; `smc_bos` for the bare model) |
| Daily bias must agree; 15m setup + daily premium/discount when the 1h/4h oppose; reward:risk ≥ 1 | `research_gate.check_tjr` |
| Evidence: only the setups the plan would take, all tickers pooled, judged on expectancy | `edge_tracker` (`in_plan`, `research.pooled_triggers`) |
| Stop and target at chart levels | `exit_manager` (`exits.measure: structure`) |
| Size so the chart stop costs `sizing.risk`; half on de-risk days | `position_sizer` |
| One trade a day for the whole account | `risk_manager` (`risk.max_trades_per_day`) |
| 09:35–11:00 entry window | each worker's `start_time` / `end_time` |

## What can't be coded faithfully (said plainly)
- "**Prominent**" highs and lows are judged by eye. The bots use every two-candle swing on the setup timeframe and
  higher, plus the prior day's high and low.
- **Market experience and intuition**, and TJR's discretionary picks of which zone or which ticker looks clean, can't be
  coded. The bots replace them with measured evidence and refuse trades without it.
- **News dates** must come from the official calendars. The shipped list has the 2026 FOMC days; the CPI/PPI/NFP days
  in it are unverified and incomplete. A missing date means no blackout.
- **No promise of a win rate.** TJR himself says losses are part of the game (Days 11, 41). The bots are judged on
  profit factor and drawdown, reported honestly.
