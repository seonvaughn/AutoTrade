# Day 36: Daily Bias Pt 3 (recap on charts)
Source: https://www.youtube.com/watch?v=Y1lqifylC4s (22 min). Read in full from the transcript the owner pasted.

## Concepts
- **Why look at the weekly at all:** if the daily breaks structure down while the weekly is in an uptrend, it's
  probably a **weekly retrace**. Use the retracement tools (weekly equilibrium, a weekly FVG) to judge how far it can
  go. "Higher timeframes hold higher power", on every timeframe.
  - His S&P monthly and weekly view (expecting the COVID-era lows to be swept, a quarterly order block, bad economic
    data) is explicitly "just how I feel", his opinion and not a rule. He keeps the daily bias bullish anyway, because
    the daily structure says so.
- **The chain:**
  1. Daily bias (the daily market structure) says buys.
  2. The 4H agrees, which is "even better".
  3. The 1H agrees, also even better.
  4. On the 1H and 4H, mark the high-confluence areas: liquidity under the 1H lows, imbalances, the order block (the
     candle that swept lows and caused a rally).
  5. When price reaches one, map the 15m/5m confluences inside it.
  6. A lower-timeframe sweep, then a 5m BOS: long. All of daily, weekly, 4H, 1H and 15m confirm.
  - The S&P that Friday had little to work with, so he didn't trade it.
- **Breaks nest:** "A 15m BOS is a 1H retrace. A 1H BOS is a 4H retrace. A 4H BOS is a daily retrace. A daily BOS is a
  weekly retrace." Don't get "trapped into the low-timeframe bias": a 1m BOS can just be a 5m retrace.
- **Take the extension, not the retracement**, every day. A trade against the daily bias gets the small leg at best:
  "when price is not in line with your daily bias, you're screwed."
- **No reaction, no trade:** if price comes into a marked area and doesn't react, "it was never there"; forget it.
- **GBPUSD (weekly up, daily down):** short with the daily, but expect the down-move to be limited, since the weekly is
  up and hasn't even reached its discount (the minimum he wants for a retracement).
  - His actual short: the **4H had broken up**, but that only means a daily retrace.
    1. Price was in the daily's upper half (shorting territory; he says "discount" here, but means the premium half
       of the daily leg).
    2. It entered a **4H order block** (a sweep of liquidity, then an extension down) and tapped a **1H order block**.
    3. It reacted on the **15m and 5m**, and the **1H broke down**: "that's kind of all I need".
  - Targets, from a 5m execution: TP1 is the most recent low (the next liquidity in a downtrend), then the daily
    discount/equilibrium level, then more liquidity, then the order block (TP1–TP4).
  - He didn't hold over the weekend.
  - The daily bias flips back to bullish only on a **daily BOS up**, which signals the weekly retrace is over and the
    weekly's next leg up has started.
- **Gold (weekly down, daily down, 4H up = a daily retrace):**
  1. Price is in the daily's upper half (again called "discount"; for a short it means premium), has filled an
     imbalance, and is inside a 1H order block (it took out highs, then capitulated lower).
  2. **Wait for a 15m BOS down** (not there yet, so no execution). Perhaps price first goes into the 15m order block
     inside the 1H order block. There's also a 15m imbalance.
  3. Targets: daily liquidity, daily order blocks. TP1 would have been about **1:4.79**, and holding to the last
     target about **1:13.5**.
  4. **He takes partials** and doesn't hold for days.
- Discipline and risk management should be "damn near robotic" by now; if not, go back to demo.

## For the bots
- **Gate rule (refines Day 35):** when the 4H (or 1H) trend opposes the daily bias, the trade is a daily-retrace fade
  back into the daily trend. It's allowed only when:
  - price is in the daily leg's premium (shorts) or discount (longs): **daily equilibrium**,
  - **and** the setup is on the 15m or higher (Day 35).
- **Daily equilibrium:** computed from daily candles before today: the swing that started the current daily leg, to the
  extreme since then.
- **No holds overnight:** already true (flatten before the close).
- **Several take profits:** the first target is the nearest resting liquidity at least 1R away. Partial exits need
  qty ≥ 2 (options are whole contracts). Keep as a later experiment, measured by backtest.
- **"No reaction, no trade":** a setup that is never armed (no retrace into an order block or gap with the
  lower-timeframe break) never fires, and it expires.
