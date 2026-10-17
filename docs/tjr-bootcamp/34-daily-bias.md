# Day 34: Daily Bias Pt 1
Source: https://www.youtube.com/watch?v=sjuWqKDsQtI (20 min). Read in full from the transcript.
(Days 35 and 36 continue this; see their notes.)

## Concepts
- **Why daily bias matters:** a trade against where the market wants to go for the day is likely short-lived or a
  loser. Most of the S&P's daily range is made in the **New York session**; "everything else is chop". So the intraday
  trade usually *is* part of the daily candle. If it isn't, the bias was wrong and the stop gets hit.
- **Top-down analysis:**
  1. **Weekly:** just the recent direction (a line chart is enough). It's long-term context. A day trader doesn't need
     it beyond knowing where weekly equilibrium and liquidity are.
  2. **Daily = the bias.** It's the **current daily market structure: the direction of the last daily BOS.** Before a
     bearish daily BOS he was bullish; after it, bearish.
  3. **4H:** ideally agrees. If the daily is bearish but the 4H is still bullish (no 4H BOS down yet), it's "tricky":
     look for bearish confirmation on the 1H, but keep **take profits modest**. Don't target far daily levels until
     the 4H confirms. Ideally a 4H close below the last 4H low makes the daily and 4H agree.
  4. **1H/15m/5m:** execution, using the building blocks, in the direction of the bias.
- **A lower-timeframe move against the daily bias is a retrace.** Daily bullish with a 4H downtrend means the daily is
  retracing. That's ideal: wait for price to reach a 4H/daily FVG, order block or equilibrium, then a 1H BOS up, then
  scale down to 15m/5m for the entry.
- **Think of the day as a higher-timeframe trade.** Ask: "How would I take this trade on the daily, 4H and 1H?" Find
  the HTF building blocks that confirm the bias (draws on liquidity, sweep, BOS, FVG, order block, equilibrium), then
  scale down to a 5m or 15m BOS for a precise entry. A 5m entry can then take 4H or daily targets.
- **Ignore lower-timeframe signals against the bias.** A 15m sweep and BOS up while the daily is bearish is not a
  long; wait for the bearish setup.
- Don't trade the S&P in the London session. He didn't trade this day because Powell was speaking.
- Example targets: 4H retracement levels (imbalance, equilibrium of the swing, the order block), then daily liquidity.

## For the bots
- **DailyBiasBot (new),** run each morning from daily candles (no look-ahead):
  - Daily bias = direction of the last daily body-close BOS, using TJR's 2-candle highs and lows.
  - 4H trend = direction of the last 4H BOS.
  - Publish them as `DailyBias(symbol, daily, h4, weekly)`.
- **Gate rules:**
  - Entries only in the direction of the daily bias.
  - If the 4H disagrees, entries are still allowed, but the target is capped at the nearest liquidity, not daily
    levels.
  - Lower-timeframe signals against the bias are vetoed with the reason "against daily bias".
- **Session rule:** options entries only during New York hours (from 09:30, already the case).
- **4H candles** are needed. They come from aggregating the 1H; for stocks, use regular-hours sessions only (two 4H
  bars a day: 09:30–13:30 and 13:30–16:00).
