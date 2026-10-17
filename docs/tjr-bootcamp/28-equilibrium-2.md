# Day 28: Equilibrium Pt 2 (on the chart)
Source: https://www.youtube.com/watch?v=-E7plUbSJUk (21 min). Read in full from the transcript.
There is no Pt 3: he moves straight on to the trading plan and execution.

## Concepts
- **Drawing it:** a Gann box or a Fibonacci with only the 0, 0.5 and 1 levels.
  - Uptrend: draw from the swing low to the latest swing high. Below 0.5 is discount (where buyers act).
  - Downtrend: draw from the swing high to the latest swing low. Above 0.5 is premium (where sellers act).
  - "Smart money never buys in a premium and never shorts in a discount."
- **Re-anchor every time.** Each time price makes a new extreme without retracing to 0.5, drag the box to the new high
  (uptrend) or new low (downtrend). Only the retrace after the latest extreme counts.
- The 50% and 61.8% Fibonacci retracements work because they sit around equilibrium.
- **It's never enough alone.** Every example needs:
  1. Price reaches equilibrium (discount or premium).
  2. Plus an FVG or order block in the same area.
  3. Scale down to 15m or 1h and wait for a BOS in the trend direction.
  4. Enter, stop beyond the swing, target the previous liquidity pools in sequence.
  - Equilibrium with only a BOS is "not much confirmation" (it worked, but he didn't like it).
- **Multi-timeframe examples:**
  - Gold: the monthly uptrend is in monthly discount, so wait for an FVG or order block there, then a 4H BOS.
  - His Discord swing short:
    1. Daily BOS down while the weekly was also down.
    2. Daily retrace into premium filled a 4H imbalance.
    3. A 1H BOS down gave the short. Stop above the swing.
    4. Four take profits at liquidity pools; three were hit.
- "Play what the market is telling you": trade in the direction of the higher-timeframe structure.

## For the bots
- Equilibrium filter: per timeframe, keep the current leg (last swing low to high in an uptrend, high to low in a
  downtrend), re-anchored on each new extreme. Its 50% line splits premium from discount. A retracement entry needs
  price in discount (longs) or premium (shorts), plus an FVG or order block overlapping that half, plus a
  lower-timeframe BOS.
- Several take profits at successive liquidity pools (see Days 37–38).
- Swing structure note: the current `structure` bot already finds swings and Fibonacci legs. Its 0.382–0.786 fib
  window should become TJR's simpler rule: discount below 0.5 for longs, premium above 0.5 for shorts.
