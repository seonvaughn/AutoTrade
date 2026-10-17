# Day 44: Try Not to Trade (when to skip an instrument)
Source: https://www.youtube.com/watch?v=uGi6EeKnWSk (26 min). Read from the transcript; the trading part is the
first half, and the rest is about work ethic.

## Concepts
- **Each morning, about 30 minutes before the NY open,** he reviews every instrument and picks the ones that look good.
- **A good instrument:**
  - The setup agrees with the daily bias.
  - The 4H agrees: e.g. daily bullish, 4H BOS up, price takes out a 1H building block, then 5m confirmation.
- **Skip the instrument when:**
  1. **The timeframes disagree and price is near nothing:** the daily is bearish, the 4H and 1H are bullish, no
     building block is near, and there's no lower-timeframe confirmation.
  2. **There's no direction (chop):** BOS, then a sweep against it, then a BOS back, then another sweep. That is
     unreadable. "The highest probability markets are **trending** markets", with clean HH/HL or LH/LL on the
     execution timeframes.
  3. **The setup is against the daily bias.** Beginners take these, and "those are the losing trades that stack up".
- **Higher timeframes hold higher power.** A 5m BOS can be a 15m retrace, and a 15m BOS can be a 1H retrace. Don't
  flip the day's bias on a small-timeframe break.
- **If not everything on the checklist is met:** skip that instrument, and if you only trade one, skip the day. "The
  best traders take the most days off." The more days in the market, the more chances to lose. A top trader took
  about 8 trades in a month.

## For the bots
- **Instrument selection each morning** (`DailyBias` per symbol):
  - Mark the symbol tradeable today only if the daily and 4H agree, or the daily is clear and the 4H is retracing
    into a building block.
  - Otherwise the worker sits the day out with the reason ("timeframes disagree" or "no trend").
- **Chop detector:** count BOS direction flips on the execution timeframe over the last N swings. Too many flips means
  "no direction", and entries are vetoed.
- **Fewer instruments:** the 12-tower setup goes against "take the best one or two trades". The account-wide trade cap
  and the per-symbol daily filter keep the count low.
