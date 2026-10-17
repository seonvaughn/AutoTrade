# Day 13: Risk Management
Source: https://www.youtube.com/watch?v=RkMBoqbeUq8 (17 min). Read in full from the transcript.

## Concepts
- "Risk management" means how much you risk and how often. The hard part is the discipline to stick to it, so he
  ranks discipline above risk management.
- Expect to lose money while learning, even after being profitable on demo. Treat it as tuition.
- **Risk 1–3% of the account per trade.** At 1%, it takes about 100 straight losses to blow the account, and even a
  trader who loses 80% of the time keeps most of the account for the year.
- **The simplest rule: 1–3% risk per day in total.** That allows, for example:
  - one trade at 3%
  - two trades at 1.5%
  - three trades at 1%
  Some days have no setup and risk nothing. Risk more only when all biases line up (covered later).
- If a 1% risk is spread across 100 trades in a day, the account can still be gone in a day. So cap the number of
  trades as well as the size.
- Treat a small account as if it were $200k. Don't risk 20–30% per trade, and don't take 10 trades a day.
- Overleveraging to dig out of a hole digs it deeper (he went into debt this way).
- "Live to trade another day": there will always be setups tomorrow. Learn the skill first and the money follows.
- Homework: learn to calculate position size for your instrument (stop distance to size). For options, that is the
  premium at risk to the stop.

## For the bots
- Where the bots stand today (`config.yaml`, $30,000 sim account):
  - The account-wide `risk.max_daily_loss` is $1,200, which is 4% a day, above TJR's 1–3%.
  - Each worker may lose $500 and take up to 10 trades a day, across 12 workers. That is far more trades than TJR's
    one to three setups a day.
- Change to make: daily account risk of 2–3% (about $600–900 on $30k) and a per-day cap on trades across the whole
  account. Size each position from the stop distance (premium × stop % × multiplier ≈ 0.5–1% of the account),
  not from a fixed premium budget.
- This doesn't weaken any safety rail: it tightens them.
