# Day 38: Stop Losses
Source: https://www.youtube.com/watch?v=1FunNCUw_jM (13 min). Read in full from the transcript (recorded live with his
Discord, right after a trade stopped out).

## Concepts
- **The default: the stop goes beyond the liquidity sweep** (above the swept high for shorts, below the swept low for
  longs). This holds whether you enter on the BOS, an order block or an FVG.
  - Reason: if the sweep was real, price has no reason to return beyond it. If it does, the sweep wasn't valid, the
    trade is invalidated, and you were wrong. **A stop is an invalidation point,** not a number of points or pips.
  - Don't put the stop just above the nearest minor high inside the move: price can poke it and still go your way.
- **Pad for spread:** set the stop a little beyond the level (he uses about 0.5 points on the S&P, or your broker's
  spread), so the bid/ask doesn't take you out at the exact level.
- **Exception (he dislikes it):** when the sweep is so far away that risk:reward is terrible, put the stop beyond a
  closer confluence (an order block or FVG) instead. That accepts a higher chance of being stopped out while the bias
  is still right.
- **His real loss:** he took a 5m sweep with a 1m BOS as the setup and put the stop under that 5m sweep plus about 4
  points. It was wicked out, and then price went his way. His daily bias was right; that execution's invalidation
  was hit. He accepts it as a lesson.
- **Higher-timeframe setups:** if the sweep and BOS are on the 15m, a stop under the 15m sweep is far away. You can
  scale down and use a closer swing low below the sweep if your risk tolerance allows.
- **Size by confidence:** a fixed standard size, cut to **half on high-impact news weeks** and the days around bank
  holidays. Don't trade US bank holidays at all.

## For the bots
- **Stops on the underlying:** the stop is the swept extreme plus a buffer (about 0.05–0.1 ATR, or the spread). The
  option exits when the *underlying* crosses that level, which replaces the fixed −10% premium stop for these models.
  Today `exits.measure: underlying` uses ATR multiples; the new mode is `stop: structure`.
- **Risk:reward check** using that stop (Days 26 and 37). If the sweep is too far away, the setup waits for an
  order-block or FVG retrace; it doesn't tighten the stop.
- **Bank holidays:** already skipped (market closed). Add the half-days and the day after a holiday to the reduced-size
  list.
- **News weeks:** half size (Day 19 calendar).
