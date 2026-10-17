# Day 30: Execution (putting the pieces together, Pt 1)
Source: https://www.youtube.com/watch?v=ESsy0uoFAz4 (9 min). Read in full from the transcript.
**This is the core of the strategy.**

## The five building blocks and what each tells us
| Block | What it says |
|---|---|
| Liquidity sweep | A high or low was taken: orders *could* have been filled. Not confirmed yet. |
| Break of structure | Confirms orders were filled. The market structure has shifted. |
| Order block | The price range where orders were filled (the move that caused the sweep). |
| Fair value gap | The price range with no opposing liquidity (the big imbalance candle). |
| Equilibrium | The discount or premium of the swing (the 50% line). |

## The four entry models (he ranks them from most risky to safest)
1. **Sweep + BOS:** enter on the BOS. This is the top of the move, and **the riskiest**.
2. **Sweep + BOS + order block:** if the BOS entry's risk:reward is bad, wait for the retrace into the order block.
   Enter there, with the stop beyond the swept high or low.
3. **Sweep + BOS + FVG:** the retrace fills an FVG in the trend direction. Enter on the reaction, or simply when it's
   reached. These need not be simultaneous: if the order block was missed and price trends on, a later FVG works.
   He ranks 2 and 3 about equal.
4. **Sweep + BOS + (FVG or order block) + equilibrium (discount for longs, premium for shorts):** "ultimate
   confluence", **the safest**. "A foolproof plan to enter if you are a beginner."

Homework: write these into your trading plan and choose which model you'll trade.

## For the bots
- **Implement model 4 as the default** (the safest), with models 2 and 3 available. Model 1 (the raw BOS entry) only
  when risk:reward ≥ the minimum.
- **Each model is a named trigger,** so the edge tracker scores them separately: `sweep_bos`, `sweep_bos_ob`,
  `sweep_bos_fvg`, `sweep_bos_confluence`.
- **"A sweep happened" must come first:** no model fires without a prior sweep of a prominent level by the same leg.
