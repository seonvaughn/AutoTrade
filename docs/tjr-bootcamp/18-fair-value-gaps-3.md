# Day 18: Fair Value Gaps Pt 3 (putting it together)
Source: https://www.youtube.com/watch?v=qecF411R83s (18 min). Read in full from the transcript.

## His live S&P 500 trade (the model, step by step)
1. A small uptrend, then a **15m break of structure down**, which leaves an FVG. Only one candle group qualifies:
   the neighbouring groups have overlapping wicks, so they aren't FVGs.
2. Pre-market: price taps the 15m FVG and breaks structure down. He ignores it because he takes **no trades before
   the market open** (the value of the open is covered later).
3. A lower low confirms the downtrend. At the open, price pushes up into another imbalance.
4. He drops to the **1m**. The two confirmations are the HTF trend shift (BOS) and the HTF imbalance being filled.
   He waits for a lower-timeframe BOS, then refines to an even lower timeframe: he marks a 5m imbalance, price pushes
   into it at the open, and **a 1m candle closes as a BOS**. He enters short there.
5. Targets: nearby liquidity (lows) and a small order block. Both targets were hit. The rest of the position was
   stopped at **break-even**, so he scales out and moves the stop to break-even.
6. Entering on the touch of the imbalance, or on the first BOS alone, would have been stopped out. **Wait for the
   lower-timeframe BOS inside the zone.**

## Concepts
- **Use FVGs for the "patient entry".** If a sweep and BOS dump without offering a good risk:reward, wait for the
  retrace into an FVG, then take the lower-timeframe BOS back in the trend direction.
- **Lower-timeframe BOS against a higher-timeframe trend is a retrace, not a reversal.** When the 15m and 1h are
  bearish, a 5m BOS up just means a 15m retrace is coming. Wait for it to fill the imbalance, then a 5m BOS down
  gives the short. Stop above the highs; targets are liquidity, accumulation or the imbalance below.
- **Invalidation:** once price pushes all the way through an FVG, stop considering it.
- **Confluence stacks:**
  - A 4H BOS, an imbalance and liquidity sitting in the same area. Gold spiked into it, then a 15m BOS gave the short.
  - Targets: previous liquidity, the accumulation the move came from, or the start / 50% / end of an imbalance below.
- **Refine the gap:**
  - If a later wick already filled part of an FVG, only the unfilled part counts.
  - Prioritize the timeframe whose imbalance is still clean (his example: the 1H inside a 4H).
- **A doji in the zone signals indecision.** Don't act until the BOS candle closes.
- **Top-down example (bullish):**
  1. Daily BOS up gives the bullish bias.
  2. 1H BOS up, then a retrace into a 1H FVG.
  3. 15m BOS up gives the entry. The first take profit may miss and price may revisit the FVG, then it runs to the
     liquidity above.
- He uses imbalances mainly to find where a retrace goes, then wants another reason to enter (order block, BOS, a
  sweep inside the imbalance followed by a BOS). An imbalance is confirmation, not an entry.
- Next: order blocks (three parts), then equilibrium, then the strategy.

## For the bots
- Entry chain for the FVG continuation model:
  1. HTF (15m/1h) BOS sets the direction.
  2. An unfilled HTF FVG in that direction.
  3. Price trades into it.
  4. A 1m/5m body-close BOS in the HTF direction inside or just after the zone.
  5. Entry, with the stop beyond the swing that made the BOS.
- No entries before the 09:30 open (the bots already start at 09:35).
- Exits: scale out at the first liquidity target, then move the stop to break-even on the rest. This needs partial
  exits in the exit manager. Options contracts are whole numbers, so it only applies when qty ≥ 2.
- FVG state: track the unfilled part, and invalidate a zone once price closes through it.
