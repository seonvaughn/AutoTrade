# "My strategy is boring": no-trading zone, 200 SMA, 15-minute ORB retest
Source: https://www.youtube.com/watch?v=tGPN_JMQhAg (about 25 min). Read in full from the transcript the owner
pasted on 2026-10-20.

The presenter claims over $500k in October and $100k days, and says himself that this is "not typical". No trade
log, win rate, sample size or costs are shown. The "backtest" in the video is three hand-replayed days (two shown),
both winners, picked "randomly" on camera. That is a demonstration, not evidence. The video ends by selling a paid
mentorship.

## The strategy in his one paragraph
"I only trade outside of the no trading zone. I trade in the direction of the trend using time frames and 200 simple
moving average. I enter using opening range breakouts with clean structure. I size in using bell curve and let my
runners run on trendy days."

## Rules, in the order he applies them
1. **Trade only the first 90 minutes.** "You do not need more than 90 minutes to day trade … after that, it gets
   choppy." (09:30–11:00 ET.)
2. **Mark levels before anything else, and use them to get *out*, not in.**
   - On the 1-hour chart with extended hours, switch to a line chart and draw a level at every bend (where price
     clearly turned or paused), two or three above and two or three below the current price.
   - Back on candles, nudge each level to touch the wicks.
   - "These levels simply become my profit taking areas … I'm scaling out … I'm not randomly guessing exits."
   - At all-time highs there are no levels above, so he uses round $1 steps or the pre-market high/low.
3. **No-trading zone (NTZ):** a box from the **pre-market high/low** and **yesterday's high/low**.
   - Inside it: "false breakouts, trap wicks, chop". No trade, or a very small one only for a very clean setup.
   - "The only time we can actually enter … is once we fully, completely break out of this range."
   - "Sitting on your hands is a position. Cash is a position."
4. **Timeframe by time of day:** 2-minute chart for 09:30–10:00, 5-minute for 10:00–11:00, 10-minute after 11:00.
5. **Direction ("truth filter"): the 200 simple moving average** on that chart. Above → calls; below → puts;
   chopping around it → no trade.
6. **Entry: the 15-minute opening range (09:30–09:45), break then retest.**
   - Mark the first 15-minute candle's high and low. Don't trade before 09:45.
   - "I don't chase breakouts. I wait for the retest." Break (a candle **closes** beyond the range), pull back to the
     broken edge, hold.
   - **"You do not jump at the retest. You jump a candle after the retest"**: enter when the candle after the retest
     candle opens.
   - "No retest simply means no trade."
   - The A+ trade is the retest **outside the NTZ, in the trend direction**.
   - Stop: "on the other side of the ORB". Target: the next hourly level.
7. **Confluence: never a trade on one reason.** Extra reasons he names: a Fibonacci pullback of the breakout move to
   0.236 ("on ultra strong days") or 0.382, the 8 EMA, an hourly level at the same price. He also re-enters on
   retests of the 200 SMA (and a 400 SMA) and of the NTZ edge after it breaks.
8. **News:** check the calendar (Fed speakers at 10:00, a 10:30 release) and be "a little bit extra careful".
9. **Bell-curve sizing:** "First trade of the day is always going to be with a small position size." Size up only
   if the market is clean and he is "in the rhythm"; if red or unsure, stay small or stop.
10. **Runners:** take partials at the levels; on clean trend days let the rest run.
11. **Backtest** with bar replay, one candle at a time, chart hidden so there's no bias, and **journal** every
    trade: "you can't really improve what you do not measure."

## For the bots (what is built, and how it differs)
- **New trigger `orb_ntz_retest` in `sig_orb_ntz` (bots/orb_bots.py):**
  - NTZ = from min(pre-market low, yesterday's low) to max(pre-market high, yesterday's high). Pre-market highs and
    lows come from Alpaca 5-minute bars, 04:00–09:30 ET (`data/premarket.py`, cached).
  - Chart by time: 2m until 10:00, 5m until 11:00, 10m after. The 200 SMA is computed on each of those charts from
    the minute candles, across days (so it's ready at the open).
  - A candle on the active chart **closes** beyond the 15-minute range (outside the NTZ, on the 200 SMA's side).
    Then a candle touches the broken edge and closes back outside it (the retest). The signal fires on the close of
    the **next** candle, if it closes in the trade's direction and still outside the NTZ. This is the bots'
    equivalent of "a candle after the retest".
  - Stop: the other side of the 15-minute range. Target: the nearest hourly level (bends of hourly closes over the
    last 10 sessions) at least `smc.min_rr` × risk away. If there is none, no trade. The video takes the very next
    level; that is often under 1R with the stop across the whole range, so the bots wait for a level that pays.
  - Window: the worker's `start_time`/`end_time` (09:45–11:00 for the first 90 minutes).
- **Same gates as every planned trade:** news calendar, morning study, research evidence (expectancy over the past
  60 sessions, pooled tickers), lessons book, reward:risk, risk manager. "No trade without evidence" still holds.
- **Not built:**
  - The "very small size inside the NTZ" exception. The bots don't trade inside it at all.
  - Fibonacci / 8 EMA confluence. Optional extras in the video; first test the core rule.
  - Partials and runners (exits are one stop and one target).
  - Re-entries on 200/400 SMA retests.
  - Bell-curve sizing: the account already takes at most 2 trades a day at a fixed $300 risk.
- **Data differences:** the hourly levels use regular-hours candles only (the video uses extended hours); the NTZ
  does use real pre-market data.
- **Tested before any tower trades it**, on the same discovery (Jun–Aug) / holdout (Sep–Oct) split as the other
  strategies (docs/research-log.md).
