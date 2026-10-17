# Day 41: Learn from Losses (what to do in a losing streak)
Source: https://www.youtube.com/watch?v=PyCPHiO2nj0 (12 min). Read in full from the transcript the owner pasted.
Recorded after he lost two trading days in a row.

## Concepts
- **Don't change the strategy; make small tweaks** based on what your journal shows is going wrong. "The strategy
  doesn't get patched."
- **Two real tweaks he made:**
  1. A streak two months earlier: the S&P was chopping (no clear bias; his usual confluences got stopped out). The
     tweak was **switching instrument** back to Forex, which he'd traded profitably before. Result: a $100k week.
  2. This week: price action was fine and **every daily bias was right** (S&P short stopped twice then fell; gold
     short deep in profit; GBPUSD long would have hit TP1–TP3). The problem was execution: **he was entering on
     low-timeframe sweep + BOS alone**, getting swept and stopped, and then price went his way.
     - The tweak: **only take sweep + BOS + order-block entry, sweep + BOS + FVG entry, or sweep + BOS + OB/FVG +
       equilibrium**, the retracement entries with extra confluence and better risk:reward. (Day 46 shows the result:
       this avoided a loss and paid.)
- **Be patient, don't force trades, and never try to win back the money right away** in a streak.
- **Two losing days isn't a streak** to him; two or three losing *weeks* is. Either way the process is the same: find
  what's going wrong, tweak, adjust.
- **It's never the market's fault**, nor the strategy's. You executed wrong, so find out what and learn from it.
  "Stop acting on what you think the market should do; act on what it gives you."
  - If a higher timeframe breaks structure against your bias, **adapt the bias**. Holding it means getting stopped
    out again and again.
- Review every day: losses (where did I go wrong?) and wins (how could it have been better?). Put hours in on the
  charts, watching and journaling.

## For the bots
- **This confirms the shipped choice:** `smc_retrace` (sweep, BOS, order block or FVG, discount or premium,
  lower-timeframe BOS) is the traded model. `smc_bos` (bare sweep + BOS) stays off. It's still scored separately so the
  evidence can be compared.
- **The bias adapts on structure:** daily bias comes from the last daily break, so it flips as soon as the daily breaks.
  The bots don't hold an opinion against the chart.
- **The losing-streak review:**
  - The edge tracker scores every setup forward, per model, on all tickers, for the setups the plan would have taken.
  - The trade log keeps each trade's setup (sweep, break, area, equilibrium, stop, target).
  - A weekly review of losses by model × ticker × time is how a "small tweak" (e.g. pausing a ticker that's chopping)
    gets chosen from evidence rather than guessed.
- **The instrument switch (tweak 1):** the gate's evidence is pooled across tickers today. A per-ticker check (pause a
  ticker whose recent in-plan setups lose) is a candidate, but it needs more data per ticker than 5 sessions give.
