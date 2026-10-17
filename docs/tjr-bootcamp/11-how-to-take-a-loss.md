# Day 11: How to Take a Loss
Source: https://www.youtube.com/watch?v=_jLR3XcB5eQ. Read in full from the transcript.

A mindset lesson with no new chart rules.

## Concepts
- Losses are part of the game. No profitable trader has a 100% win rate, and "the market is built to beat you".
  The goal is to be profitable over many trades, not to never lose.
- After a loss:
  - Don't revenge trade, don't overtrade and don't raise size to "win it back".
  - Keep the same fixed risk per trade. He lost about $9k on GU on the day he recorded and still followed his rules.
- Review the loss by asking "why did the market move against me?", not "why did I take it?". Every setup is one of
  one, and trading is probabilities.
- His own lesson: he flipped $10K into $112K and lost it all the next day, which is how he learned risk management.
- Learn on demo first. Follow the trading plan robotically: "you are the algo / EA / trading bot".
- Judge results by yearly percentage returns, not day to day.
- Skip days around big news, or when you're emotionally compromised ("maybe I shouldn't trade before news").

## For the bots
- Already enforced: fixed risk per trade, daily loss limit, kill switch and cooldowns after losses, so the bots
  can't revenge trade or size up after a loss.
- Every loss is recorded with its trigger and exit reason (Trade log room), and the edge tracker scores each
  trigger forward. That is the bots' version of "study why the market moved against you".
- Candidate: a news blackout filter (no entries around scheduled high-impact releases). TJR's details are in Day 19.
- Honest note for the owner: this lesson says outright that a no-loss system doesn't exist. The bots are judged on
  profit factor and drawdown, not on avoiding every loss.
