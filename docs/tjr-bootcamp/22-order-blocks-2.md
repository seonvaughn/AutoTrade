# Day 22: Order Blocks Pt 2 (how to spot them)
Source: https://www.youtube.com/watch?v=RQSVIKddFHI (26 min). Read in full from the transcript (fetched on retry).

## Concepts
- **Definition (recap):** the order block is the whole move that caused the liquidity sweep, just before the BOS. In an
  uptrend that ends in a sweep of highs, it's the up move that took the highs; its price range is where orders were
  filled. Price is drawn back into it to fill more orders.
- **It's the whole move, not one candle.** On the 4H it may look like one candle; on the 1H it's the whole leg. A big
  range is narrowed by scaling down.
- **Match the stop to the timeframe of the move.** If the order block and BOS are a 4H move, a tight stop from a 1H
  BOS will get hit. The stop goes beyond the 4H structure, and the reward comes from targeting higher-timeframe
  liquidity.
- **Worked buy (GBPUSD), the full top-down chain:**
  1. Daily downtrend. Price enters the daily order block (the leg before the daily BOS).
  2. A 4H BOS up signals the retrace.
  3. On the 1H: a sweep of a low, then a 1H BOS up. Entering there would need a far stop, so he waits.
  4. Price retraces into the 1H order block (the down leg before the 1H BOS).
  5. On the 15m, he waits for the **New York open (09:30)**: no pre-market trades. He then **"monitors the highs"**.
     Each 15m swing high is a candidate. When one is closed through, that's the BOS, and the entry.
  6. TP1 is the nearby liquidity. TP2 is inside the imbalance or at its 50%. TP3 is the higher highs. He closed at
     about **1:12 risk:reward**.
  - "Would you really have been patient enough?" If not, taking the 1H BOS entry is also fine for a daily play.
- **London example:** wait for the session open. Price enters the order block, then the 15m high is broken, then
  entry. A refinement: a 15m FVG inside that gets filled, then a break back above it, then a long.
- **Sometimes price doesn't reach the order block**, because it fills off something else (an FVG). "Be okay with
  that."
- **Stop placement:** beyond the BOS swing, or "beyond the order block itself if you want to play safe".
- Homework: five order blocks on three different timeframes.

## For the bots
- **The "monitor the highs" BOS trigger:** while price is inside an order block or FVG (and in discount or premium),
  watch the most recent lower-timeframe swing high (for longs) or swing low (for shorts). A candle body that closes
  beyond it is the entry trigger.
- **Session rule:** no entries before 09:30 ET (options). Crypto has no open, so the rule doesn't apply there.
- **Stop sizing** follows the timeframe of the setup. Option-premium stops are a poor fit (the corrected backtests
  showed it), so stops should sit at an underlying price level beyond the swing.
- **Targets:** a list of liquidity levels (TP1, TP2, TP3).
