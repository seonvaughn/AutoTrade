# Day 25: Overconfidence
Source: https://www.youtube.com/watch?v=4moWbfm6smw (19 min). Read in full from the transcript.

## Concepts
- **After a big win, don't go looking for another trade to grow it.** That is greed or overconfidence.
- **Price and time theory:** the highest-probability trade comes at the **market open**. New money arrives, a
  liquidity sweep usually happens, and orders get filled.
  - After that, volume dies out. Later trades are retracements with lower risk:reward that take longer to play out.
  - Hence "one to two trades a day, one is best".
- No single trade will dig you out of a hole. Chasing one is worse than gambling.
- Confidence sits on a thin line between overconfidence and fear:
  - Overconfidence leads to over-risking, over-leveraging and overtrading.
  - Fear leads to missed entries and hesitation.
- **On a win streak, expect a loss.** Don't change what made you profitable. His own story: he was profitable on
  demo, then raised leverage on live money and got wrecked.
- A new strategy video isn't the Holy Grail (he says ICT rebrands the FVG, e.g. "Silver Bullet"). Mentors take
  one or two trades a day.
- **Don't trade Fed chair speeches** (Powell) or the day after. Winning on news by luck is worse, because it builds
  false confidence.

## For the bots
- Time-of-day priority: the best window is right after the open. Measure it: the edge tracker should score entries
  by time bucket (first 30/60/90 minutes versus later), and the gate should require more evidence later in the day.
- Trade cap: one to two trades per day per account (or per underlying). Don't raise size after wins.
- News: add Fed chair speeches / FOMC press conferences to the blackout list (Day 19).
