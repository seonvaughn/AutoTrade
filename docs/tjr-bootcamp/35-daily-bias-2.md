# Day 35: Daily Bias Pt 2 (live pre-market analysis with his Discord)
Source: https://www.youtube.com/watch?v=UPA9LQW7phk (15 min). Read in full from the transcript the owner pasted.
Recorded live about 17 minutes before the New York open, on a day with news 30 minutes into the open.

## The routine
1. **Weekly: overall direction** (a line chart is fine). S&P: bullish, and about to break monthly structure up.
2. **Daily: the bias.** "We base our trades off daily candles." Read the daily market structure (the last daily BOS).
   - **Don't force your opinion on the market.** He thinks the S&P fundamentals look bearish, but the daily closed
     back above structure, so the daily is bullish. "We take a trade based off what the market gives us."
   - His own mistake the day before: he shorted after a **daily liquidity sweep** without **lower-timeframe
     confirmation**. "That's where I messed up."
3. **Trade the extension, not the retracement.** In an uptrend the extensions are much larger than the pullbacks, so in a
   daily uptrend catch longs, not shorts on the retrace.
4. **When the weekly and daily disagree, the daily rules.** GBPUSD: weekly bullish (a weekly order block after a sweep),
   but the daily is bearish. "Until we flip bullish on the daily", he stays bearish. The weekly is only an overview.

## From the higher timeframes down to the sniper entry
- **GBPUSD (daily bearish, the daily retracing up; the 4H has probably broken up):** "prime time to catch a short".
  1. On the higher timeframe, mark the building blocks in line with the bias: a bearish FVG, and the order block from
     the sweep and the big BOS down.
  2. When price gets there, scale down: a **15m sweep, then a 15m BOS, then a 15m order-block entry**.
  3. Scale down to the **5m and take the BOS there**: "that's our sniper entry".
  4. Target the higher-timeframe take profits. The building block on the higher timeframe is the price zone, and the
     lower timeframe's building blocks give the entry inside it.
  - **Because the 1H and 4H are still bullish while the daily is bearish, he wants at least a 15m BOS** before
    shorting, not just a 5m one. That needs more time to develop.
- **Gold (weekly and daily bearish, the daily retracing):**
  1. Retracement tools: FVG and equilibrium. Draw equilibrium on the daily leg: price isn't in the right half yet.
  2. An FVG sits in the right half.
  3. Lower timeframe: an imbalance, and liquidity resting above highs. Expect price to draw up to those highs and fill
     the imbalance.
  4. When those are hit, scale down further and wait for the sweep and imbalance fill, then a **15m sweep + BOS**.
  - That's "an hourly or 4-hour type of trade with a good entry".
- **GBPJPY:** skipped, "trading pretty sloppily" (Day 44: don't trade messy price action).
- **S&P (weekly, daily, 4H, 1H and 15m all uptrends): "longs will be money".**
  - Mark every high-confluence area below that price might reach: 1H lows (liquidity), the 15m order block (the move
    that swept liquidity and caused a rally), an imbalance, and a deeper order block and imbalance.
  - "**It doesn't matter where the market goes, we just need to adapt to it.**" At whichever area price reaches:
    sweep, BOS up, order block or FVG entry. For example, the imbalance, then a 5m BOS, then an order-block entry
    with a 1m BOS, then long.
  - "Everything above the 50% mark" is discussed with equilibrium. He uses "discount" loosely in this video; the rule
    is Day 26's.
- **Execution timeframes:** Forex 15m and 5m; **S&P 5m and 1m**.
- **News:** don't trade until the release is out (30 minutes after the open here).

## For the bots
- **Daily bias decides direction; the weekly is context only.** This is already the gate rule (`daily_bias`).
- **New rule: when the 1H or 4H trend opposes the daily bias, a 5m setup isn't enough.** The setup must come from the
  15m (a 15m sweep and BOS), with the entry on a 5m BOS. When everything agrees, a 5m setup with a 1m BOS entry is
  fine.
  - The bots read setups on both 5m and 15m, each entered one timeframe lower: 15m with a 5m break, 5m with a 1m
    break.
- **Several areas of interest at once:** each setup timeframe keeps its own setup and the latest order block and
  gaps. Whichever area price reaches can arm a setup.
- **A sweep alone is never an entry:** lower-timeframe confirmation is always required. That's the `smc_retrace` order.
