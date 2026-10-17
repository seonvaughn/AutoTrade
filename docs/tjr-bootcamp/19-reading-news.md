# Day 19: How to Read News Data
Source: https://www.youtube.com/watch?v=w5sUCqFH3Lg (25 min). Read in full from the transcript. Recorded on a CPI day.

## Concepts
- **Source:** forexfactory.com calendar. It shows times in your own time zone.
  - Filter out yellow folders (low impact). Keep grey (bank holidays, non-trading days).
  - Keep only the currencies you trade. **S&P 500 news is listed under USD.**
- **Red folders (and orange):** always wait until the release is out.
  - Let price develop 15–30 minutes. If the news moved the market a lot (huge wicks, large moves), **don't trade
    that day**.
  - If it barely moved the market, you may trade, but defensively: lower probability, less risk, only an excellent
    setup.
- **Never trade these four:** **CPI, PPI, FOMC, NFP** (anything "non-farm"). "Just call it quits, sleep in."
- **Heavy news days:**
  - With many red or orange folders on your currency, it's a low-probability day: de-risk, or trade only pairs
    without that currency.
  - With news at 10:00 (30 minutes after the 09:30 open), sit out until 10:00, and still wait until about 10:30.
- **Reading a release:** compare actual with forecast and check the "usual effect" (e.g. actual > forecast is good for
  the currency).
  - Good for USD means DXY up, which is **bad** for SPX, gold, GBPUSD, EURUSD and BTC/USD (anything XXX/USD).
  - Pairs: news for the currency on top of the slash moves the pair the same way; news for the bottom currency moves
    it the opposite way.
- **News bias is not a trading bias. Price action rules.** On this CPI day the number was bad for USD and DXY dumped
  at release, then rallied and ate the whole drop. That's why you wait.
- Check the calendar every morning before trading, so a release doesn't stop you out five minutes after entry.

## For the bots
- **NewsCalendarBot (new):**
  - Holds the scheduled high-impact USD events, emits a `NewsBlackout` state, and the research gate vetoes entries
    while it's active.
  - Rules:
    - CPI, PPI, FOMC and NFP days: no new entries all day.
    - Any other red-folder USD event: no entries from its release until 30 minutes after.
    - Heavy news days: the gate requires more evidence, or risk is halved.
  - It applies to the options workers (all USD underlyings). Crypto (BTC/USD) is affected by USD news too, so the same
    blackout list applies there.
- **Data:**
  - Forex Factory has no official API. Its public weekly JSON feed only covers the current week, so it can't be used
    for backtests.
  - The bots will instead read an explicit date list in config (`news.blackout_days`, plus times for other events),
    filled from the published BLS (CPI, PPI, NFP) and Federal Reserve (FOMC) calendars.
  - For paper trading, the owner can add the week's events. Be honest that a missing date means no blackout.
