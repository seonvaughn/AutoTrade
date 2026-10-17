# Day 42: How to Backtest
Source: https://www.youtube.com/watch?v=NPG_BZ_83fo (10 min). Read in full from the transcript.

## Concepts
- **He doesn't trust TradingView's bar replay:**
  - **Look-ahead:** replaying on the 15m and switching to the daily, 4H or 1H shows the *full* higher-timeframe candle,
    which the trader couldn't have seen at 09:45. That corrupts the daily bias.
  - Staying on one timeframe hides a higher-timeframe BOS that would change the bias.
  - Replay has no emotion: candles jump bar by bar instead of forming tick by tick.
- **What he does instead:**
  - "Target practice": scroll back, spot the building blocks and the entries on full charts, over and over.
  - Real testing is live on demo: "judge my trading ability purely off live markets". He expects a backtest win rate
    to be *worse* than live, because the bias is missing.
- **Weekend homework:** go through each day of the past week, find one or two trades you could have taken, and mark
  every building block.

## For the bots
- **The look-ahead problem is real and applies to the bots.** The rules they follow:
  - Higher-timeframe candles are only used once **closed**: `timeframes` emits `BarClosed`.
  - The daily study uses days **before** the session (`htf_levels` and `load_daily` only see prior days).
  - History is delivered candle by candle (see "History must be delivered candle by candle" in CLAUDE.md).
- Any new 4H or daily-bias logic must follow the same rules, with a test that the bias can't see the current day's
  daily candle.
- Paper trading is the bots' "live on demo". Backtests stay the honest screen, and his warning ("results that look
  better than live are suspect") matches the stale-price lesson.
