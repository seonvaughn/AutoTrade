# Day 14: Fair Value Gaps Pt 1 (what they are)
Source: https://www.youtube.com/watch?v=d0AxLACYaqU (10 min). Read in full from the transcript.

## Concepts
- Fair value gap, liquidity void and imbalance all mean the same thing (he says "liquidity void").
- **Definition:** a price range with no opposing orders. A big, unhesitating move up means there were no sell orders
  in that range, and a big drop means no resting buy orders. It usually shows as one large candle.
- In a trend, retracements are drawn back into these voids. There, market makers can fill orders and price moves on in
  the trend's direction.
- **How he uses them:** for retracements and second entries, not as entries on their own. Liquidity sweeps say where
  the market is going, and FVGs say where a pullback is likely to reach.
- **The continuation model:** the trend is up, and price retraces into a higher-timeframe FVG. Wait for a lower-timeframe
  break of structure in the trend direction, then enter.
- He prefers this to "support/resistance off a drawing", because it is based on orders being filled.
- Works on any timeframe and any market. How to spot them comes in Day 16.

## For the bots
- Fair value gap detection (exact three-candle rule in Day 16).
- Entry model 2 (FVG continuation): the higher-timeframe trend agrees, price trades into an unfilled HTF FVG, then a
  lower-timeframe body-close BOS in the trend direction. That gives the entry.
