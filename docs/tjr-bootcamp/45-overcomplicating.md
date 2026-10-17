# Day 45: Overcomplicating
Source: https://www.youtube.com/watch?v=LG_IbfjbaOo (23 min). Read from the transcript; the second half repeats the
same points.

## Concepts
- **The trading plan removes ways to mess up.** You know how many trades, when, why and how. Only the market itself
  can beat you.
- **Losing early is a lack of market experience, not a missing piece of strategy.** "There's no missing link: the
  missing link is time." Most people need about a year of following the plan.
- **One strategy, one bias.** Clear out the other strategies. Running 20 strategies with conflicting biases "burns
  your brain alive". Don't take your bias from mentors or signal groups once you can find it yourself.
- **Learn *about* your strategy rather than adding to it.** Keep a journal of skipped and taken trades, then review
  what the market did. For example: "Skipped: daily bullish, 4H bullish, 1H bearish, so the timeframes disagree."
- **Example of market experience:** an order block late in the session may not react, because volume is low. Take
  trades near the open.

## For the bots
- **This argues against piling on triggers.** The bots now run six chart triggers per tower, and every corrected
  backtest lost. The TJR-faithful approach is one model (sweep → BOS → order block/FVG in discount or premium,
  daily-bias aligned) as the primary strategy, with the old triggers off by default, rather than a seventh trigger.
- **Journal of skips:** `EntryVetoed` events already record every skip with its reason. A daily review compares skips
  with what price did afterwards; the edge tracker does this for taken and untaken signals.
- **Time of day:** prefer entries in the first part of the NY session, and measure whether late-session entries do
  worse.
