# Research log: what was tried, on what data, and what held up

Rule for this project: experiment only on the **discovery** period, choose before looking, then run the
**holdout** once. Count every variant tried, so nobody mistakes a lucky survivor for an edge.

## 2026-10-20: TJR model, exits and filters

Data: minute bars Jun 1 – Oct 15 2026 for the 10 enabled tickers. Every TJR setup was recorded with what was known at
that moment (`scratchpad` scripts `record_setups.py`, `sim_variants.py`, `explore.py`, `holdout.py`). Outcomes are on the
underlying, stop first when stop and target fall in the same minute, before option costs.

- **Discovery: Jun 1 – Aug 31.**
  - About **810 variants**: 2 entry models × 5 bias filters × 3 time windows × 9 targets × 3 holding times.
  - Best by average R: setups **against** the daily bias, 09:35–11:00, fixed targets (+0.09 to +0.13R, PF 1.2–1.35,
    n=141 retrace / 543 bos).
  - TJR's own "with the daily bias" filter was not among the best.
  - Every variant with a 65%+ win rate used a 0.5R target and made about zero (PF 0.98–1.14).
  - Sweeps on 15m and setups on 15m did worse than 5m.
- **Holdout: Sep 1 – Oct 15, run once,** three candidates chosen before looking:

  | Candidate | n | Win | Avg | PF |
  |---|---|---|---|---|
  | A: retrace, against daily bias, 09:35–11:00, 1R target, hold to close | 44 | 55% | +0.147R | 1.41 |
  | B: sweep + break, against daily bias, 3R, to close | 203 | 48% | +0.032R | 1.09 |
  | C: retrace, daily + 1h agree, 0.5R (the "high win rate" variant) | 35 | 66% | −0.006R | 0.98 |

- **Verdict:**
  - A is the only lead. Its combined sample (n ≈ 185, about +0.12R) has a t-statistic of about 1.6, which is
    **not statistically significant**, especially after ~810 tries (the deflated Sharpe would be far below 0.95).
  - It's shipped because it's the best-supported option, not because it's proven. Paper only. Re-test as data
    accumulates.
  - C shows why the bots don't chase a win-rate target: 66% wins, still losing.

## 2026-10-20: backtests of the shipped settings (real option bars, every agent on)

| Run | Trades | Win | Net | PF |
|---|---|---|---|---|
| Jun 1–Aug 31, 0.70 delta, 2 DTE | 16 | 43.8% | −$227 | 0.87 |
| Sep 1–Oct 15, 0.70 delta, 2 DTE | 4 | 50% | −$233 | 0.63 |
| Sep 1–Oct 15, contract scout (`strike: auto`) | 4 | 25% | −$529 | 0.25 |

- 20 trades over 4½ months: about −$460, PF about 0.83. The +0.12R edge on the stock doesn't survive option
  spread and time decay.
- The morning study stood down most days: 329 entries refused for lack of a proven 20-session record.
- Scout versus fixed delta: 4 vs 4 trades, no conclusion possible.

## 2026-10-20: look-back on the losing trades (trade reviewer)

- **Jun–Aug: 16 trades.** 7 wins, all reaching the full 1R target. 9 losses:
  - 3 stop too tight (the target printed after the stop)
  - 4 setup failed
  - 2 out of time
- **Tested on the setup record** (Jun–Aug; Sep–Oct checked once):

  | Proposed fix | Result |
  |---|---|
  | Wider stop buffers (0.5–3× 1-minute ATR) | No better than 0.1×. "Stop too tight" losses are the normal price of a stop. |
  | Skip "gap only" retraces (7 of 9 losses) | Gaps did best on 80 setups (+0.14R). The pattern was chance. |
  | Rolling 20-session "prove it" gate | Hurt in both periods: discovery +0.12 → +0.08R; holdout +0.15 → +0.04R. Replaced by a 60-session record. |
  | First setup of the day only | +0.21R in discovery, −0.15R in holdout (n=20). Noise; not adopted. |

- **Bug found:** the lessons book learned from untraded VWAP/EMA signals and blocked TJR trades with "avoid puts/calls".
  It's now scoped per traded strategy.
- **Crew:** focused on the options strategy; legacy trigger bots are built only when a tower trades them.

## Outside evidence (docs/research/evidence-based-intraday-strategies.md)

- No peer-reviewed or rigorous test shows an edge for ICT/smart-money concepts.
- Published intraday edges on the underlying (ORB, intraday momentum, VWAP) are thin and die at a few cents of
  slippage.
- No source shows buying 0DTE options has positive expected value. Spreads average about 9% of premium at 0DTE versus
  about 2% at 21–48 days, and theta alone can hit a −10% premium stop within an hour.
- Changes that came from this:
  - **0.70-delta, 2+ day options** instead of 0DTE at the money.
  - **Stops on the underlying**, not as a percent of premium.
  - A **20-session evidence window**, because 5 sessions is noise.

## Earlier results (CLAUDE.md "Status")

| Run | Net | Profit factor |
|---|---|---|
| Indicator triggers | −$5,620 | 0.43 |
| Aligned exits | −$5,444 | 0.53 |
| Six strategies plus gate | −$5,423 | 0.58 |
| TJR "with bias" Sep–Oct | −$412 | 0.15 (4 trades) |
