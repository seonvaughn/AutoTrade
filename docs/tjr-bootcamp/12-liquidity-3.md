# Day 12: Liquidity Pt 3 (using it for entries and targets)
Source: https://www.youtube.com/watch?v=KtC2SbemF6w (20 min). Read in full from the transcript.

The last of three liquidity lessons. Next come fair value gaps, then order blocks, then equilibrium.
He says liquidity is "a piece we plug into a strategy", not a strategy by itself.

## Concepts
- **Why liquidity:** market makers fill their orders where many people enter and exit at once. That happens at highs
  and lows, where entries and stop losses rest. Without a sweep the market is "chippy choppy".
- **Mark prominent highs and lows.** What counts as prominent depends on the timeframe. His examples:
  - The start of a big trend.
  - A double top.
  - A high or low that caused a break of structure on the daily.
  - Highs or lows that price has already pushed through no longer count.
- **Liquidity is a magnet.** Price is drawn toward the nearest untaken prominent high or low ("draw on liquidity").
- **A sweep is not an entry.** Never sell just because a high was hit, or buy just because a low was hit: "you would
  lose way more than you win". Not every high or low gets used to fill orders. The sequence is:
  1. A prominent high or low is taken (swept).
  2. Wait for confirmation that orders were filled: a break of structure (a body close beyond the most recent
     opposite swing), plus other confluence such as a fair value gap or order block retest.
  3. If price doesn't react, there's no trade.
- **Targets use liquidity too.** Market makers exit where others enter and exit, so they target the opposite
  prominent lows (for a short) or highs (for a long). Take profit at the previous prominent low or high. A whole
  lesson on take profits comes later.
- **Multi-timeframe.** It works the same on every timeframe, from daily and 4H down to 15m and 1m:
  - S&P daily: sweep, BOS, the target is the prior prominent low.
  - GBPUSD: a 4H high is swept, but the sweep is only visible on the 1H. The BOS candle comes next, then a retrace
    into an order block or imbalance. He scales down to the 5m to enter, and targets the prominent low.
  - Gold: lows are swept, a quick regain closes above, a dip into the imbalance gives the entry, and the target is
    the previous highs.
- Homework: find five liquidity sweeps on any timeframe and pair each with its confluence (sweep, then BOS, then a
  reaction off an imbalance or order block, then entry).

## For the bots
- Liquidity bot: track untaken prominent swing highs and lows per symbol and timeframe (15m, 1h, 4h, D). A level is
  removed once price trades through it, and it becomes a "sweep" when the next confirmation happens.
- Entry model (sweep → BOS): after a sweep of a prominent level, wait for a body-close BOS in the opposite direction
  on the trading timeframe. Enter on the retrace (fair value gap or order block, Days 14+). Never enter on the sweep
  alone.
- Target: the nearest untaken opposite liquidity level, used as the profit target and as the "room" check in the
  research gate (no trade if the draw is closer than the stop distance allows).
- "Prominent" can't be copied exactly, because TJR judges it by eye. The coded version uses swings that caused a BOS,
  the extremes of a leg, or equal highs/lows, and that approximation must be stated wherever it's shown.
