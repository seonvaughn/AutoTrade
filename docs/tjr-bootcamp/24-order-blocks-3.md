# Day 24: Order Blocks Pt 3 (marking them, putting it together)
Source: https://www.youtube.com/watch?v=12_F-mIUfL0 (28 min). Read in full from the transcript.
(Day 22, Order Blocks Pt 2, had no transcript available at the time of writing.)

## Concepts
- **Definition:** the leg up or down just before the break of structure. That leg made the liquidity sweep and filled
  the orders. They are best when the leg itself swept liquidity.
- **How to box one:**
  - Beginners: box the **entire leg**, from where it started to the swept extreme. "Don't shoot threes before you can
    make a layup."
  - TJR himself boxes only the wick part, from the extreme wick to where the candle's body starts. Price often
    reacts at the start of the body ("market experience, who knows why").
- **The entry is never the touch.** In every example:
  1. Price taps into the order block.
  2. Wait for a BOS back in the new direction on the same or a lower timeframe (e.g. 15m inside a 1H block).
  3. Enter.
  4. Target previous liquidity, one pool after another.
- **Retracement tools (until equilibrium is taught):** the FVG and the order block. If price doesn't confirm in the
  FVG, wait for the order block below it. Each zone needs its own BOS.
- **Order blocks as targets:** an opposing order block can be a take profit.
- **Top-down chain example (bullish):**
  1. Daily BOS up gives the daily bias.
  2. Price retraces into the daily order block. That alone is "not enough".
  3. 4H BOS up, then a 1H BOS up.
  4. Price retraces into the 1H order block, then a BOS gives the long.
  5. Targets are liquidity pools.
  - It's stronger when it lines up with the daily and weekly bias.
- When the BOS only comes long after the sweep, the block is too far away. Drop to a lower timeframe to find a closer
  BOS and block.
- "If you see a liquidity sweep then a leg higher, assume there's an order block."

## For the bots
- **Order-block marking:** after each sweep followed by a BOS, mark the opposite leg (from its start to the swept
  extreme). Also keep the "wick to body start" sub-zone as the preferred reaction area.
- **Order-block retest entry:** price enters the block, then a 1m/5m BOS in the new trend direction gives the entry.
  - Stop beyond the swept extreme.
  - Targets: the opposite liquidity pools, nearest first.
  - Invalidate the block if price closes through it.
- Bias stack: the order-block or FVG trade is stronger when the 1h, 4h and daily trends agree. Gate on agreement.
