# Day 46: Journaling Trades
Source: https://www.youtube.com/watch?v=CZRs2NuLQIw (12 min). Read in full from the transcript.

## Concepts
- **Journal columns:**
  - Pair: trade **one** instrument until profitable, and delete the rest from the watchlist.
  - Session: New York or London, not Asia, because that's when volume and volatility are.
  - Risk: 1–3%, ideally 1%. More than that is wrong.
  - Confluences, written out in full: the entry model (sweep + BOS, + order block, + FVG), what the daily, 4H, 1H and
    15m structure said, and which building blocks on which timeframe.
  - Did you follow the plan? If not, what did you skip?
  - Emotions, and why you felt them.
  - How to improve, for wins as well as losses.
- **Review the journal weekly to find patterns.** For example: "I took sweep + BOS while only the 1H was bullish and
  the higher timeframes were bearish, and lost every one."
- **His own result, said on camera:** "Last week I was only taking **liquidity sweep + break of structure** and we
  **lost literally every single trade**. This week I waited for sweep + BOS + **order block or FVG entry** for more
  confirmation. That avoided a loss today and made money."

## For the bots
- **The trade log already records:** symbol, time, trigger, entry and exit, P&L, exit reason, and the research
  evidence.
- **To add:** the daily, 4H and 1H bias at entry, the entry model name, the building blocks used, the planned stop and
  targets, and R multiple. That makes the weekly "pattern review" a query (P&L by model × bias alignment × time of
  day).
- **TJR's own experience backs the default:** the retrace model (order block or FVG after sweep + BOS) is the
  default, and the bare sweep + BOS is off unless the evidence supports it.
