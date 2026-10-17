# Day 26: Equilibrium Pt 1 (what it is)
Source: https://www.youtube.com/watch?v=j1pVK897oZQ (18 min). Read in full from the transcript.

## Concepts
- **Equilibrium is the 50% level of a swing**, from swing high to swing low or swing low to swing high. It splits the
  range into premium (above 50%) and discount (below 50%). It's a retracement tool showing where big money is likely
  to add again.
  - Buyers want a discount and sellers want a premium (his "bag of Doritos" analogy).
  - **Uptrend:** measure from swing low to swing high. A retrace **below 50%** is in discount, where longs are
    attractive.
  - **Downtrend:** measure from swing high to swing low. A retrace **above 50%** is in premium, where shorts are
    attractive. In the video he says "discount to go short" for this case, but he means the price is good (high) for
    a short.
- **It's never an entry alone.** It's a gauge for where to look. Inside discount or premium, he wants another reason:
  an order block, an FVG, or "even just a break of structure while in a discount".
- **The full toolkit, in order:**
  1. The liquidity sweep is the inducement.
  2. The **BOS is the primary entry.**
  3. If that's missed, the retracement entries:
     - The order block (the move that caused the sweep). Price taps it and reacts, or enters it.
     - The FVG: price fills the imbalance and reacts.
     - Equilibrium. "**FVG inside discount/premium + reaction**" is his ideal retracement combination.
- From his last live trade: he skipped the BOS entry because of **bad risk:reward** and waited for the order block (or
  an FVG reaction).

## For the bots
- Premium/discount filter: for the current trading leg (from the last BOS swing), longs only below 50% of the leg and
  shorts only above 50%. This applies to retracement entries (order block or FVG). The BOS entry itself is exempt.
- Risk:reward check at entry: (distance to the nearest liquidity target) ÷ (distance to the stop) ≥ a minimum,
  e.g. 2. If the BOS entry fails it, wait for the retracement entry instead.
