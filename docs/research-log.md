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

## 2026-10-20: 15-minute opening range video (docs/videos/15m-opening-range.md)

3,775 setups recorded Jun 1–Oct 15 on the 10 tickers, scored on the underlying (before option costs).

| Model, the video's rules | Discovery Jun–Aug | Holdout Sep–Oct (run once) |
|---|---|---|
| Breakout (1m gap), 1:2 | n=350, 33% win, −0.01R, PF 0.99 | not run |
| **Retest (his favourite), 1:2, until 11:30** | n=220, 37% win, +0.09R, PF 1.14 | **n=67, 33% win, −0.00R, PF 0.99** |
| Reversal, to the opposite high/low of day | n=296, 30% win, −0.16R, PF 0.76 | not run |

Verdict: no edge that survives out of sample. This matches the published ORB replications. The agent stays built and
untraded, and its setups keep being scored.

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

## 2026-10-20: TJR with every fix, and the "boring strategy" video (NTZ + 200 SMA + ORB retest)
- **TJR backtest, Jun 1 – Oct 15, real option bars, all agents on** (bias "against", 60-session evidence window,
  lessons book, contract scout, 2 trades a day): **−$151, 45 trades, 48.9% wins, profit factor 0.97**, max drawdown
  $1,402. Close to break-even; still not profitable.
- **`orb_ntz_retest`** (docs/videos/boring-orb-ntz.md), scored on the underlying at its own stop (other side of the
  range) and target (next hourly level ≥ 1R), held to the close at most, news days out:
  | Period | Window | n | Win | Avg R | PF |
  |---|---|---|---|---|---|
  | Discovery (May 15 – Aug 31) | 09:45–11:00 | 98 | 59% | +0.094 | 1.31 |
  | Discovery | 09:45–15:30 | 137 | 54% | +0.047 | 1.17 |
  | **Holdout (Sep 1 – Oct 15), run once** | 09:45–11:00 | 29 | 52% | **−0.022** | **0.93** |
  - The holdout did not confirm the discovery edge. 60- and 120-minute time limits looked better on the holdout
    (+0.11R, +0.07R), but they were picked after seeing it, so they don't count as evidence.
  - Before option costs; 29 holdout setups is a small sample either way.
- **Decision:** the towers paper-trade both `smc_retrace` and `orb_ntz_retest`, behind the research gate (each
  needs positive pooled expectancy over the past 60 sessions). Paper trading is the forward test; neither is
  proven.

## 2026-10-21: afternoon session, and what the losses have in common
- **Afternoon windows** (shipped TJR rule: against the daily bias, 1R, held to the close; NTZ: its own plan), on the
  underlying, news days out. Trial count +5 windows × 2 strategies.
  | Window | Strategy | Discovery (May 15 – Aug 31) | Holdout (Sep 1 – Oct 15) |
  |---|---|---|---|
  | 09:35–11:00 | TJR | n 284, 51%, +0.046R, PF 1.12 | n 44, 55%, +0.147R, PF 1.41 |
  | 11:00–13:00 | TJR | n 337, 50%, −0.005R, PF 0.99 | – |
  | 13:00–15:00 | TJR | n 406, 49%, −0.028R, PF 0.94 | n 103, 49%, −0.018R, PF 0.96 |
  | 13:00–15:00 | NTZ | n 10, 40%, −0.130R, PF 0.18 | n 5, 40%, −0.078R, PF 0.75 |
  The afternoon loses in both periods. At the owner's request the towers still get a 13:00–15:00 session, open only
  when the account took no morning trade, with its **own** track record (`EdgeTracker.stats(..., session="pm")`), so
  the gate vetoes afternoon trades until that record shows an edge.
- **Morning study fix:** it stood a ticker down if *any* of its strategies was unproven, so the new NTZ trigger's
  record could block TJR trades. Each strategy and session is now judged on its own; the tower stands down only when
  none is proven.
- **What the losing setups have in common (the r2 lessons book, Jun–Oct):** trade reviews were 37 setup failed, 26 out
  of time, 6 stop too tight. Across 54 feature tallies (ticker, weekday, hour, side, sweep timeframe, zone, bias),
  none separates losers from winners: the strongest is |t| 1.5 (NTZ on Tuesdays, n 18), far below the 2.5 a rule
  needs. The losses don't share a feature the bots can filter on yet; a rule from them would be fitted to noise (the
  first lessons book did exactly that and blocked every trade).
- **Backtest with everything as shipped on 2026-10-21** (Jun 1 – Oct 15, real option bars; TJR + NTZ in the morning,
  the afternoon session on its own record, all agents on): **−$274, 48 trades, 47.9% wins, profit factor 0.94**,
  15 green / 17 red days, max drawdown $1,464. 836 entries blocked by the research gate. Against r2 (−$151, 45
  trades, PF 0.97) the three extra trades lost a little more. Still not profitable.

## 2026-10-21: the futures city (MES, MNQ, MGC), first backtest on ETF stand-ins
- Jun 1 – Oct 15, `config.futures.yaml` as shipped (TJR + NTZ retest, paper exploration: no record required,
  2 trades a day, $300 risk, structure exits), `data.source: proxy` (SPY ×10 → MES, QQQ ×41 → MNQ, GLD ×10.85 → MGC,
  1-tick spread, $0.62/$0.82 fees per side):
  **−$1,286, 54 trades, 46.3% wins, profit factor 0.79**, 22 green / 28 red days, max drawdown $1,841.
  | Tower | Trades | Win | P&L |
  |---|---|---|---|
  | MES | 25 | 52% | +$117 |
  | MNQ | 9 | 56% | +$241 |
  | MGC | 20 | 35% | −$1,644 |
  19 MNQ/MGC setups were skipped because one contract would have risked more than $300.
- Not profitable. The MES/MNQ numbers are small samples (n 25 and 9) and near break-even. MGC lost, but GLD is the
  weakest stand-in for gold futures, so that result is the least reliable. No tower was dropped on this evidence.
