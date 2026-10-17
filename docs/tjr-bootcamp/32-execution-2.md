# Day 32: Execution Pt 2 (sweep + BOS, sweep + BOS + order block)
Source: https://www.youtube.com/watch?v=SLhIA7vW9x8 (24 min). Read in full from the transcript.
(Day 33, Execution Pt 3, covers the FVG and equilibrium models. Its transcript wasn't available.)

## Concepts
- "This is just the bare-bones strategy. It will not make you profitable by itself." Daily bias, take profits and stop
  losses come next, and they matter as much.
- **Sweep + BOS:**
  1. Find liquidity (highs or lows).
  2. Price takes it.
  3. A body close breaks the most recent opposite structure.
  4. Execute.
  - It's the simplest but lowest-confluence model, and where **daily bias** matters most. Some sweeps don't lead to a
    BOS, so there's no trade.
  - A sweep with a BOS can still run into higher-timeframe liquidity on the other side. Watch where the
    higher-timeframe liquidity is.
- **Sweep + BOS + order block:**
  1. After the BOS, mark the candle or leg that swept the liquidity (where the orders were filled).
  2. **Don't execute on the BOS.**
  3. Execute when price comes back into the order block.
  - Sometimes the BOS candle's own wick is already in the order block: "execute on this down wick."
  - Sometimes the order block isn't touched at all, so there's no trade.
- Target the liquidity in the trend direction, or the top of an imbalance. More on targets in Days 37–38.
- Homework: on your one or two instruments, find **10 examples** of sweep + BOS and **10 examples** of sweep + BOS +
  order block, and note what price did afterwards. Do it until spotting them is automatic ("aimbot").

## For the bots
- `sweep_bos` and `sweep_bos_ob` triggers. When there's no sweep, or no BOS after the sweep, nothing fires. When the
  order block isn't reached before the setup expires, nothing fires.
- **Expiry:** a setup lapses at the next opposite BOS, or after N bars (to be measured, not guessed).
- **Measure what TJR asks students to check by hand:** for every sweep + BOS on history, record what price did next.
  This is the edge tracker's job, once per model. Report the numbers honestly per model.
