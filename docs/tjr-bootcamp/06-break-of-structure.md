# Day 6: Break of Structure
Source: https://www.youtube.com/watch?v=PmhuPbY8ZHo (31 min). Read in full from the transcript.

## Definitions (exact)
- **A high = a move up then a move down: just two candles,** an up candle followed by a down candle. The high's price is
  the **highest wick of those two candles**. It doesn't need to look pretty.
- **A low = a move down then a move up:** a down candle followed by an up candle; price = the **lowest wick of the two**.
- **Break of structure (BOS) = a shift in the trend**, confirmed only by a **candle body closing** beyond the level:
  - **Bullish BOS** (downtrend → uptrend): a candle **closes above the most recent high**.
  - **Bearish BOS** (uptrend → downtrend): a candle **closes below the most recent low**.
  - **A wick beyond the level is NOT a break of structure.** "It is not a break of structure unless the candle closes
    above a high or below a low." Wicks through a level are usually **liquidity sweeps** (Day 8) that fake out
    traders who sell or buy the wick.
- **Only the most recent high or low counts.** Once a newer low forms, older lows don't matter ("no one cares about this
  low"). Use the newest one even if an older one is more extreme.
- **What to watch:** in an **uptrend watch the lows** (the trend breaks only when the most recent low is closed below);
  in a **downtrend watch the highs**.
- **Consolidation:** alternating highs and lows with no trend; no break of structure, nothing to trade ("market had no
  clue where it wanted to go").
- A BOS doesn't mean price goes that way forever. **Higher timeframes hold more power** (monthly > weekly > daily): a
  daily bearish BOS while the weekly is bullish is just a retracement.
- Wait for the close; don't trade "good enough". Taking a wick as a break only lowers your odds.

## His checklist
1. Identify the trend (higher highs and lows, or lower highs and lows). 2. Uptrend → watch the most recent low.
3. Downtrend → watch the most recent high. 4. Bearish BOS = a candle closes below the most recent low.
5. Bullish BOS = a candle closes above the most recent high.

## Homework (his)
- 10 real breaks of structure and 10 fake ones (wicks beyond a high or low that didn't close).

## For the bots
- **Rebuild `structure` to these rules.** Highs and lows from the two-candle pattern (not 5-candle fractals). Trend
  = direction of the last body-close BOS. In an uptrend only a close below the *most recent* low breaks it; in a
  downtrend only a close above the most recent high. Wicks never count.
- A wick through the most recent high or low with no close = a **liquidity sweep candidate** (Day 8 onward).
