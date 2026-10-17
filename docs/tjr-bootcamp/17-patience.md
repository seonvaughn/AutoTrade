# Day 17: Patience
Source: https://www.youtube.com/watch?v=339amTioakE (15 min). Read in full from the transcript.

## Concepts
- Rushing into trades means losses without confirmation. Pressing buy gives a dopamine hit, like placing a bet, so
  think about what you could lose, not what you could make.
- **Fix 1: a written, step-by-step trading plan.** For example:
  1. Liquidity sweep.
  2. Break of structure.
  3. Wait for price to enter the FVG.
  4. Reaction.
  5. Enter.

  If a step is missing, there's no trade. That makes patience automatic.
- **Fix 2: come in wanting *not* to trade.** The market must give you a reason; never make one up. Don't force your
  bias on the market.
- Even when every step is met, sometimes don't trade, for example before news. Be open to no-trade days.
- Skip a setup if anything is off: "against the daily bias", "off a retracement", half the conditions met.
- Waiting one or two more candles for volume or volatility to show doesn't hurt.
- "I take one trade a day and call it good." You don't need 10 trades a day. It took him two years to become
  profitable.
- Trade alone, not with friends, because their bias differs from yours.
- Homework: 30 minutes of meditation in a dark room with the phone outside, to feel how short your attention span is.

## For the bots
- The checklist is the bots' design: each entry passes an ordered list of conditions (sweep, BOS, FVG/OB retest,
  reaction, HTF bias agreement, room to target, research evidence), and any miss is an `EntryVetoed` with its reason.
- Bias agreement: the daily bias must *agree*, not just "not oppose". Today the gate only blocks trades against the
  trend, so this needs to be tightened.
- Few trades: cap trades per day across the account (TJR: about one a day).
- News days: see Day 19.
