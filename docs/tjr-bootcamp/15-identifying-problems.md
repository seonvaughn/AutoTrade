# Day 15: Identifying Problems
Source: https://www.youtube.com/watch?v=T4xVS7iV5d8 (18 min). Read in full from the transcript.

A psychology lesson with no chart content.

## Concepts
- **Root-cause method:**
  1. Write down your three biggest trading problems. They must not be strategy problems.
  2. For each one, ask why you do it.
  3. Find the emotion driving it: greed, fear, overconfidence, FOMO, revenge.
  4. Solve that emotion, not the symptom.
- **Example: too many trades.** The cause is wanting more money, from greed or need. The fix is income outside trading
  and focusing on learning. A revenge trade after a loss is "probably not going to hit take profit".
- **Example: exiting before stop or target.** The cause is fear, low confidence, confusion, no bias or lack of
  knowledge. The fix is to know your risk, size down, or go back to demo.
- Every loss is your responsibility, not the market's.
- Once a mistake is identified, never repeat it.
- He feels greed when floating $20k in profit but doesn't act on it: he keeps the planned take profit.

## For the bots
- Bots don't have emotions, but the same failure modes can be built into code: overtrading, revenge entries right
  after a loss, and exits that skip the plan. The guards against them are:
  - Trade caps, cooldowns, daily loss limits.
  - Exits only by the planned stop, target or rule, and they are logged with a reason.
- The trade journal's "why it lost" review is the equivalent of the root-cause page. Per-trigger stats in the
  Research room show which setup keeps losing, so it can be switched off rather than repeated.
