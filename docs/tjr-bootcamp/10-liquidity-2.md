# Day 10: Liquidity Pt. 2: where it rests
Source: https://www.youtube.com/watch?v=rdz6vnXb8wE (17 min). Read in full from the transcript.

## Where liquidity rests
- **Above highs (especially in an uptrend):** retail traders see higher highs and higher lows and place **buy stops just
  above the high** to join the trend on the break. Traders shorting the pullback put their **stop-losses just above that
  same high**. When the high is taken out, both trigger: a pool of orders.
- **Below lows (especially in a downtrend):** **sell stops** from trend sellers and the **stop-losses of longs** sit just
  under the low.
- When price takes that pool ("sweeps" it), institutions can fill large orders and **reverse** the market. The breakout
  buyers and the stopped-out shorts both lose; price then moves the other way.
- Hence his entries come at the **start** of a new move ("catch the top of a downtrend or the bottom of an uptrend").
- The move that causes the liquidation and lets orders fill is essentially an **order block** (taught later).

## The pattern to see on the chart
- **Uptrend → a sweep of the highs → collapse.** **Downtrend → a sweep of the lows → rally.** It "jumps off the page".
- It happens on **every timeframe**: monthly, weekly, daily, 4H, 15m, 1m. His examples: S&P daily highs swept then
  big sell-offs; GBP/USD in the Asian session: lows taken, then a bullish break of structure, price higher; a monthly low
  sweep followed by a weekly bullish BOS and a rally.
- Liquidity alone is not a trade: "you need to know a lot more than just liquidity and break of structure to form a
  bias and take a high-probability trade."

## Homework (his)
- Find 5 liquidity sweeps on each of 3 timeframes.

## For the bots
- **New bot `liquidity`:** keep the resting pools for each timeframe: the most recent highs (buy-side liquidity)
  and lows (sell-side liquidity), plus the prior day, week and month highs and lows (`htf_levels` already has those).
  Detect a **sweep**: a candle trades through the pool level (wick beyond it) and then fails, i.e. closes back inside,
  or later price breaks structure the other way.
