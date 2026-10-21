# SkyView Trading options course: what the bots learned
Playlist: https://youtube.com/playlist?list=PL7lc3p-Mb9_NJYQ2EnPgGuBrWSEqm15sY (studied 2026-10-20 at the owner's
request: "a deep study of this course … implement steps, rules, education, and everything valuable").

| # | Video | Notes |
|---|---|---|
| 1 | Options Explained | [01-options-explained.md](01-options-explained.md) |
| 2 | Options Trading Explained (the option chain) | [02-option-chain.md](02-option-chain.md) |
| 3 | Understanding Option Prices | [03-option-prices.md](03-option-prices.md) |
| 4 | Option Greeks Explained | [04-option-greeks.md](04-option-greeks.md) |
| 5 | How to Buy Options | [05-buying-options.md](05-buying-options.md) |
| 6 | How to Sell Options | [06-selling-options.md](06-selling-options.md) (from the transcript the owner pasted) |
| 7 | Options Trading for Beginners (4-hour course) | [q1](notes-4h-q1.md) · [q2](notes-4h-q2.md) · [q3](notes-4h-q3.md) · [q4](notes-4h-q4.md) |

Every transcript was read in full. The 4-hour course was split into four parts, each read by its own reader agent
and checked against the short videos. Caption errors (missing decimal points, mangled names) are fixed in the notes.

## The course in one paragraph
An option is the right to buy (call) or sell (put) 100 shares at a strike before expiration. Its price is set by
three things: where the stock is against the strike (intrinsic value), the time left, and implied volatility (the
rest, extrinsic value, which decays to zero by expiration). The Greeks measure each: **delta** (P&L per $1 of stock,
and roughly the chance of finishing in the money), **gamma** (how fast delta changes, largest near expiry),
**theta** (P&L per day from time passing) and **vega** (P&L per IV point). A bought option has a limited loss (the
premium), but it needs the stock to pass the break-even quickly, before decay eats it, and its chance of profit is
always under 50%. That is why the instructors **don't buy options to bet on direction**. They sell premium at
30–60 days in high IV, at strikes with a 65–85% chance of expiring worthless, using defined-risk spreads (verticals,
iron condors, butterflies), and they recommend a debit vertical spread over a single bought option for a
directional bet.

## What this means for Scalp City, honestly
The towers do the thing the course warns against: they buy 1-DTE calls and puts on a chart signal. The course gives
no evidence that its own approach is profitable either. Its "high probability" pitch rests on a few hand-picked
trades, and its one losing trade in the live demo was bigger than a winning one. Two lessons line up with this
repo's own backtests:
1. **A high win rate is not an edge.** Selling premium wins often and loses big; buying wins rarely and needs big
   wins. Report win rate *and* profit factor / expectancy (CLAUDE.md already requires this).
2. **A bought option needs speed.** Time decay is fastest close to expiry, so a short-dated buy only works if the
   move comes soon after entry.

## Rules turned into bot behaviour
| Course rule | Where it lives now |
|---|---|
| Cost = price × 100; never hard-code ×100 | `contract.multiplier` everywhere (unchanged) |
| Buys fill at the ask, sells at the bid; a backtest must cross the spread | `brokers/sim.py` fills at ask/bid (unchanged) |
| **Price at the mid with a limit order; if unfilled, step toward the ask** (q2 rule 8, q3 rule 8) | **new:** `execution` tries the mid first, then the ask (`broker.entry_mid_first`). The simulator never fills at the mid, so backtests stay conservative |
| Skip wide-spread contracts | `risk.max_spread_pct` (unchanged) |
| No far-OTM "lottery tickets"; ATM–ITM for buying | the contract scout only looks at deltas 0.30–0.95 (unchanged) |
| Break-even: the stock must clear strike + premium, and fast | the scout prices each contract at the plan's target and stop *after* half the expected hold, with decay and spread; it refuses the trade if no contract profits at the target (unchanged). **New:** the pick is explained with its break-even, delta (≈ chance ITM) and theta per hour, in the journal |
| **Position delta = share-equivalent exposure; keep it within your risk tolerance** (q2 rule 6) | **new:** `risk.max_delta_leverage`: the risk manager refuses an entry whose stock-equivalent exposure (\|delta\| × qty × 100 × price, all open positions together) would pass this many times account equity |
| Close ITM options before expiration (exercise fees, unwanted stock) | the 15:55 flatten closes everything (unchanged) |
| Risk per trade = premium + commissions | the sizer sizes from the chart stop; `costs.fees()` charges the commission (unchanged) |
| IV falls hurt long options (IV crush after earnings) | not automated: holds are intraday, so the overnight crush is never held; no earnings calendar source yet (see below) |

## Not adopted, and why
- **Selling premium (short puts/calls, credit spreads, iron condors, strangles):** a different business with large
  occasional losses, assignment risk and margin needs. The research gate, sizing and exits are all built for long
  options. That needs the owner's decision and its own tests; nothing here sells options.
- **Debit vertical spreads instead of single options** (the course's choice for a directional bet): it would halve
  time decay and vega but cap the payoff at the short strike. It needs multi-leg orders on Alpaca, a two-leg
  simulator and new exits, so it's a separate project. It also can't create an edge the setups don't have: the TJR
  setups are break-even on the stock itself (CLAUDE.md, "TJR first results").
- **30–60 days to expiration:** the course's rule is for sellers. For an intraday buyer, longer expiries cost more
  premium per unit of delta; the scout already compares the three nearest expiries.
- **IV rank / IV percentile:** the course mentions comparing IV with its history but defines no rule. The bots
  store no IV history yet. Worth adding as data first, a rule later, if a backtest shows it matters.

