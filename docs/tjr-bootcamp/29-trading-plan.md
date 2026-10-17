# Day 29: Trading Plan
Source: https://www.youtube.com/watch?v=065lMUrD_kg (23 min). Read in full from the transcript the owner pasted.
The first ~5 minutes are jokes (including a fake "today we teach support and resistance").

"A foolproof plan, so you can't mess up." Write the answers down, keep them in front of you every day, and follow them
"to the point where you're a robot".

## 1. Risk management: pre-designate your risk
- **Lot size:** a set lot size (his: three set sizes, high / regular / low risk, chosen per day; see Day 39), or a lot
  size calculated every trade from balance, risk % and stop distance. **Most of you should calculate it**, or "you
  won't know what you're risking."
- **The money you'll risk each day**, decided before the session, so a loss doesn't make you "cry like a baby".
- **The number of trades per day:**
  - He recommends **one trade a day**.
  - When he takes two, he **de-risks both so together they add up to one trade's risk**. The daily risk is fixed
    whether it's one trade or two.
  - "Don't say five." **"You guys should literally just stick to one for now."** Example plan line: "I am risking $100
    a day while taking one trade a day. Period."

## 2. When you trade
- **Designate your session like a job.** His: **the New York Stock Exchange open. He takes a trade within the first
  1½ hours, and if he can't find one, he doesn't trade.** That doesn't mean closing the trade at 1½ hours; it means
  being in one by then, "or else I'm done".
- Other sessions people trade: NY PM, London open, London close into NY. Asia is "a terrible session to trade if you ask
  me".
- **News:** never CPI, NFP, FOMC or PPI. For regular red or orange news, decide in advance whether you'll trade after
  it if it fits your bias, or avoid news entirely. Avoiding news "will keep your win rate very high" while learning.
  - Write down your rule for a news spike, e.g. "if news causes a 5-point spike within a 5-minute candle, I'm done for
    the day". He says the number is just an example: set your own.

## 3. What you trade
- **One instrument.** "Choose one and master it." Every added market adds lower probability, risk and hardship.
  - He traded only GBPJPY until profitable, and added gold, GBPUSD and the S&P only after.
  - Delete the watchlist of 34 forex pairs.

## 4. How you enter
- Choose your confluences (the building blocks), test them (e.g. two weeks of sweep + BOS) and journal the win rate and
  emotions.
- **His recommendation:** the "super risk-averse" version.
  - Only trades aligned with the daily bias: a sweep with the bias, and a BOS aligned with the bias and the overall
    trend.
  - An FVG or order-block entry after the sweep and BOS, unless the bare sweep + BOS already gives a good risk:reward.
- **His own plan:** "S&P daily is bullish, so we look for buys. No buy from a sweep + BOS + FVG/OB entry: no trade. Not
  in the first 1½ hours of the NY open: no trade. Not on the S&P: no trade. Don't know my risk for the day: no trade."
- **Leave when:** it doesn't follow the plan (FOMO), you already took your trade for the day, you've maxed out the
  day's risk, or it's a US bank holiday for your market.

## For the bots
- **Entry window:** options workers now trade **09:35–11:00 ET** only (the first 1½ hours after the 09:30 open). The
  existing `start_time` and `end_time` per worker enforce it. Positions opened by then keep running on their stop,
  target and time stop.
- **Trades per day: one for the account** (`risk.max_trades_per_day: 1`). "Stick to one for now" applies, since the
  bots have no proven record. The daily risk equals one trade's risk ($300, 1% of the $30k sim account), and the
  daily loss limit stays as a backstop.
- **One instrument:** the honest TJR answer is one ticker. The city keeps its towers for watching, but with the
  account cap of one trade a day, only the first qualifying setup of the day trades. Narrowing to one ticker is the
  next step once the backtests show which one, if any, has an edge.
- **News:** already enforced (blackout days, a wait after other releases). The owner's own "spike rule" isn't set
  (TJR says choose your own number). Candidate: skip the day if a 5m candle in the first 30 minutes is more than
  N ATR. Not implemented, because the number isn't specified.
- **Bank holidays:** the market is closed, so there are no trades.
