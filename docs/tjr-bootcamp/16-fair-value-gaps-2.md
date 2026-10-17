# Day 16: Fair Value Gaps Pt 2 (how to identify them)
Source: https://www.youtube.com/watch?v=S1kY3Fw6JUQ (13 min). Read in full from the transcript.

## Concepts
- **Recap:** an FVG is a liquidity void with no resting orders against the direction price wants to go. Price is drawn
  back into it and reacts.
- **FVGs are for retracements and continuation, never reversals.**
  - In a bullish trend (confirmed by BOS, with higher highs and higher lows), use only bullish FVGs.
  - In a bearish trend, use only bearish FVGs.
  - FVGs and equilibrium are continuation tools.
- **The three-candle pattern.** Candle 2 is the large displacement candle.
  - Bullish FVG: the zone runs from the high (top wick) of candle 1 to the low (bottom wick) of candle 3. It exists
    only if candle 3's low is above candle 1's high.
  - Bearish FVG: the zone runs from the low of candle 1 to the high of candle 3. It exists only if candle 3's high is
    below candle 1's low.
  - If the wicks of candles 1 and 3 overlap across candle 2's body, it is **not** an FVG: the void was already filled.
- His chart examples:
  - Bullish: BOS confirms bullish, then a big candle with no wicks covering it. Price draws back into it, chops, a
    lower-timeframe BOS forms, and price rallies.
  - Bearish: BOS confirms bearish, price retraces up into the bearish FVG, chops, fills, and drops.
- **The warning:** FVGs are everywhere on the chart, so they are less valuable than they look. Never enter just
  because price touched one. Wait for one of:
  - a reaction candle in your direction (a candle closing bearish for shorts, bullish for longs)
  - or, on a lower timeframe, a BOS or change of structure.
- **Example trade plan (short):**
  - Bearish BOS, then price fills a bearish FVG and closes bearish. That is the entry.
  - Stop above the previous high.
  - Target the previous lows (liquidity).
- Homework: mark 10 FVGs on your one instrument, including ones that are *not* valid, and write a hypothetical trade
  for each.

## For the bots
- `FairValueGapBot` (new): on each closed candle per timeframe, test the last three candles.
  - Bullish if `c3.low > c1.high`; bearish if `c3.high < c1.low`.
  - Store each zone with its direction, top/bottom and timeframe.
  - Mark it filled (or partly filled) as price trades into it. Delete it once price closes through the far side.
  - Keep a minimum size (as a fraction of ATR), so one-tick gaps don't count.
- Use: only FVGs in the direction of the confirmed trend.
- Entry: price inside the FVG, plus a reaction candle closing in the trend direction or a lower-timeframe BOS.
- Stop: beyond the swing high or low that defines the leg.
- Target: the opposite liquidity.
