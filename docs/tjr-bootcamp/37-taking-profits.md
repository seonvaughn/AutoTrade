# Day 37: Taking Profits
Source: https://www.youtube.com/watch?v=FjSiLFrg5fo (11 min). Read in full from the transcript.

## Concepts
- **Take profits sit at building blocks.** These are price magnets: liquidity (prior highs and lows), the top and bottom
  of an order block, the edge or inside of an FVG, and the equilibrium of the swing.
- **TP1 is the first draw on liquidity in the trade direction on one timeframe above the execution timeframe** (enter on
  the 5m, take TP1 from the 15m). For a 1m entry after a 5m BOS, TP1 was a 5m order block: "higher timeframe holds
  higher power."
- **TP1 should be at least 1:1 risk:reward.** Most first targets are 1:1 to 1:5, not 1:10.
- **He usually sets three or four take profits:** TP1 is the higher-timeframe draw on liquidity, and the rest are the
  next building blocks (an FVG, an order block base, further liquidity). Decide the count in your trading plan.
- **Take profits come from the execution timeframe (and the one above),** not from distant 4H levels, unless you
  genuinely intend to hold that long.
- **Priority of what matters most:** daily bias first, then execution, then stop loss, then take profits (the least of
  your worries).
- A real trade: a 1H order block, then a 5m BOS down, then a 1m order block entry. TP1 was the 5m order block, then
  liquidity, then a 15m FVG. It was closed at break-even because it took too long.

## For the bots
- **TargetPlanner (part of the exit manager),** at entry on the underlying:
  - Take the list of liquidity levels and zone edges in the trade direction from the next timeframe up.
  - Drop any closer than 1R.
  - TP1 is the first remaining level, TP2 and TP3 the next ones.
  - If no level is at least 1R away, there's no trade (the research gate's "room" check, using real levels).
- **Exits:**
  - Scale out at the targets when quantity allows.
  - Single-contract positions exit fully at TP1, or at TP2 with the stop moved to break-even after TP1.
  - Which variant is better gets measured by backtest, not assumed.
- **Time stop:** TJR closed a slow trade at break-even. Keep the existing time-based exit.
