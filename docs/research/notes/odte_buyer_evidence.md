# Evidence on BUYING 0DTE and short-dated options (SPX/SPY/QQQ and single stocks), and what it means for an intraday directional bot

Research notes, 2026-10-20. Method note: web fetches to most academic and exchange sites (SSRN, sec.gov, cboe.com, university PDFs) were blocked from this environment. The Vilkov paper was read in full from its GitHub repo; most other findings come from search-result abstracts and summaries and are marked as such. Treat any number marked "(summary)" as needing a check against the original paper.

## 1. Beckmeyer, Branger & Gayda, "Retail Traders Love 0DTE Options... But Should They?": how much retail loses and why

### Takeaway
Retail traders in SPX 0DTE lose money on aggregate (roughly $0.2-0.36M per day), even though they get *better* effective spreads than quoted thanks to price improvement. Most of the loss (about 50-60%) is trading costs, not wrong direction. The rest comes from single-leg debit trades, put buying and buying high-implied-volatility options.

### Cited Findings
- Paper: SSRN abstract 4404704 (first version March 2023, revised December 2023). Retail trades are identified through Cboe's Automated Price Improvement Mechanism (AIM). — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4404704); [ResearchGate](https://www.researchgate.net/publication/370012499_Retail_Traders_Love_0DTE_Options_But_Should_They)
- First version: average retail losses of $184,000 per day over the full sample. Since daily SPX expirations began on 16 May 2022, the average is $358,000 per day, or over $70M in total over about two years. — [Bloomberg via BNN](https://www.bnnbloomberg.ca/day-traders-lose-358-000-per-day-gambling-on-zero-day-options-1.1910634); [WealthManagement](https://www.wealthmanagement.com/equities/retail-investors-are-in-love-with-same-day-options)
- Revised version (Dec 2023, sample Feb 2021 to Sep 2023): $241,000 lost on an average day, rising to about $350,000 per day after the daily-expiry calendar. The losses come from single-leg trades, trades that need an upfront payment (debit trades) and trades in high-implied-volatility options. (summary) — [College Sidekick copy of SSRN PDF](https://www.collegesidekick.com/study-docs/2487577); [Medium summary](https://medium.com/@y125789/retail-traders-love-0dte-options-paper-summary-6da4a7ff7d72)
- Cost share: "more than $50 million" of the roughly $70M is transaction costs, per one summary. Another summary says about 60% of daily losses are transaction costs and the rest is tied to 0DTE put investments. (summary) — [Bonus.com](https://www.bonus.com/news/zero-days-to-expiration-options-investment-or-gambling/); [Neudata literature review](https://neudata.co/literature-reviews/zero-day-to-expiry-options-a-losing-bet-for-retail-traders)
- The authors' summary: retail traders have learned to account for how expensive options are, but "the hefty fees they pay outweigh these benefits and the price improvement they enjoy in the form of lower effective spreads." (summary) — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4404704)
- Beckmeyer called the work "a cautionary tale" and described the options as a one-or-zero bet. — [WealthManagement](https://www.wealthmanagement.com/equities/retail-investors-are-love-same-day-options)

### Inferences
- The split matters for a bot. Retail losses are mostly **cost-driven**: if you pay the spread and fees, a direction call that is right slightly more than half the time still loses. A directional edge must first clear costs.
- Debit, single-leg buying (what the bot does) is the losing category in this paper.

### Gaps
- I could not read the paper's tables, so I have no split of losses by moneyness, time of day or holding period, and no direct "timing vs. spread" decomposition beyond the 50-60% cost share.
- The $ figures cover SPX only (AIM-identified retail), not SPY/QQQ or single stocks.

## 2. The rest of the academic and exchange literature: Bandi-Fusari-Renò, Vilkov, Almeida-Freire-Hizmeri, Brogaard-Han-Won, Cboe, SEC DERA, other retail-options studies

### Takeaway
The academic picture is consistent. 0DTE options carry a positive but economically small variance risk premium, so buyers pay a small premium on average. Payoffs are extremely wide and skewed. Costs and tail risk swamp the mean. Retail option buyers lose modestly on average, and less than quoted spreads suggest *when they use limit orders*. 0DTE trades do worse than other option trades.

### Cited Findings
**Vilkov, "0DTE Trading Rules: Tail Risk, Implementation, and Tactical Timing" (SPXW, 09/2016 to 01/2026; entries 10:00 ET held to 16:00; earlier version SSRN 4641356). Read in full.** — [GitHub annotated paper](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- "A positive 0DTE variance risk premium exists, but at same-day horizons its economic magnitude is small."
- Median realized VRP from 10:00 ET to expiry is about 0.0011% of the underlying. Even if the index did not move at all, collecting roughly twice the average OTM time value implies only about 0.20% of spot. "These magnitudes are difficult to monetize after realistic trading frictions."
- Single options bought at 10:00 and held to expiry: "Individual option returns are highly volatile, especially for OTM contracts, and mean returns are often not statistically distinct from zero... PNL scaled by spot... shows that ATM-to-OTM calls and most puts lose on average." Selling slightly OTM calls and puts is profitable in up to 75% of observations. Deeper ITM contracts are much more volatile, with interquartile ranges of about 0.7-0.8% of spot.
- An earlier version says that, at the median, buying deep ITM calls can be statistically profitable (it does not address the S&P upward drift). (summary) — [search summary of the SSRN 4641356 version](https://www.collegesidekick.com/study-docs/2505840)
- Moving from mid-price to paying half the bid-ask spread "mechanically lowers mean PNLs and annualized Sharpe ratios for most strategies." The 1% expected shortfall is about 0.58-1.58% of the underlying per day. "Unconditional 0DTE exposure is difficult to justify as a standing allocation."
- Conditional (out-of-sample) timing works better as directional *classification* than as return prediction. The best result, put ratio spreads, reaches a Sharpe of 1.18 gross and 0.93 net. Net of costs, an unconditional straddle has a Sharpe of about -0.51 (summary of the 2026 version). — [GitHub](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md); [CXO summary](https://www.cxoadvisory.com/equity-options/0dte-strategy-outcomes/)
- Some favorable outcomes "may partly reflect the upward drift of the S&P 500 over our sample."

**Bandi, Fusari & Renò, "0DTE Option Pricing" (Journal of Finance, 2025; SSRN 4503344).** Proposes local-in-time (Edgeworth-type) pricing for ultra-short tenors that improves pricing and hedging versus standard models. Also estimates 0DTE-implied return and variance risk premia and finds "suggestive evidence of near-instantaneous predictability." (abstract) — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4503344); [ResearchGate](https://www.researchgate.net/publication/372407812_0DTE_Option_Pricing)

**Almeida, Freire & Hizmeri (0DTE asset pricing), via a secondary review:** a large positive 0DTE VRP whose returns are concentrated in upside moves, and which negatively predicts intraday market returns. About 70% of 0DTEs violate second-order stochastic dominance bounds. Annualized 0DTE VRP is about 1.5-2.95% depending on entry time, versus 0.55% at 1DTE. Unverified against the original. — [FirmTape review](https://firmtape.com/research/what-the-0dte-literature-claims)

**Brogaard, Han & Won (University of Utah), via press:** a one-standard-deviation increase in 0DTE volume is associated with an almost 14% rise in S&P 500 daily volatility. Brogaard: "I'm leaning in team Volmageddon." — [Bloomberg via BNN](https://www.bnnbloomberg.ca/zero-day-options-are-reordering-the-way-the-stock-market-behaves-1.1921930). Contradicted by other work that finds 0DTE activity is associated with *lower* realized volatility through market-maker hedging — [Quantpedia on Adams et al.](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/); [Adams, Fontaine et al. PDF](https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf). Cboe-hosted research by Amaya, Garcia-Ares, Pearson & Vasquez also asks "how large is their impact" — [Cboe PDF](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf). This debate concerns market impact, not buyer returns.

**SEC DERA working paper, Fu, Li, Musto & Pearson, "Hope at a Reasonable Price: Customer Use of Limit Orders in the 0DTE Market" (March 2025):** wide quoted spreads "would mean large wealth transfers to market makers if customers traded with marketable orders", but customers often use non-marketable limit orders. For actively traded slightly-OTM 0DTE options, customers are at the best bid or offer more than half the time in recent data, and their costs are low. The favorable result applies to active, slightly-OTM series. (abstract and summary) — [SEC DERA page](https://www.sec.gov/about/divisions-offices/division-economic-risk-analysis/staff-papers-analyses/hope-reasonable-price_customer-use-limit-orders-0dte-market); [PDF](https://www.sec.gov/files/dera-hope-reasonable-prc-2503.pdf)

**Bogousslavsky & Muravyev, "An Anatomy of Retail Option Trading" (about $15B of retail trades, 2020-2022):**
- A typical retail option trade is a short-term S&P 500 call or put held only a few hours.
- Option trades average a -0.9% return, below the typical 3.7% quoted spread, which suggests heavy limit-order use. Returns range from -4.5% to -0.5% across subsamples.
- **0DTE trades earn about 3% lower returns** than other trades (one snippet says -2.95% with all controls; the snippet was garbled).
- Little evidence of positive skewness in realized dollar profits.
- (abstract and snippets) — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4682388); [LSU-hosted PDF](https://www.lsu.edu/business/files/event-files/2025-finance-mardi-gras/retail_option_trading_v2.pdf)

**Bryzgalova, Pavlova & Sikorskaya (Journal of Finance 2023, Nov 2019 to Jun 2021):** half of retail option trades are in options expiring within a week, with an average quoted spread of 12.6%. OTM options average about 28.7% and micro trades (≤$250) about 23.5%. Retail trades lose on average. Secondary commentary attributes about $2.1B of losses mainly to costs (not verified in the paper). — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13285); [AEA abstract](https://www.aeaweb.org/conference/2023/program/paper/5N8FE6RZ); [Investing.com](https://www.investing.com/analysis/why-retail-traders-consistently-underperform-over-time-200684221)

**Counterpoint, Amaya, Garcia-Ares, Pearson & Vasquez (Cboe-hosted, April 2025):** using expiration values and Cboe trade-direction data, Cboe customer simple (single-leg) trades are on average *profitable*. They argue the BPS estimates depend on how trade direction is inferred. This is not 0DTE-specific, and the paper is hosted by the exchange that sells 0DTEs. — [Cboe PDF](https://cdn.cboe.com/resources/education/research_publications/Retail_Profitability.pdf)

**Cboe volume statistics (exchange marketing; reliable as volume data):**
- SPX 0DTE reached 61% of SPX volume in May 2025, with retail about 54% of SPX 0DTE volume. — [Cboe](https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-61-share-on-retail-resurgence)
- A record 62.4% in August (2025), with retail about 53%. — [Cboe](https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-record-62-share-in-august)
- Full-year 2025 averaged about 2.3M 0DTE contracts a day, about 59% of SPX volume (aggregator citing Cboe). — [Walnut](https://walnutinvest.com/stats/options-trading-statistics)
- Cboe reports that about 92% of SPX 0DTE trading is in defined-risk structures, and that flow is balanced between puts and calls. — [Concretum summary](https://concretumgroup.substack.com/p/the-rise-of-0dte-options); [SpotGamma copy of Cboe report](https://spotgamma.com/wp-content/uploads/2023/09/CBOEs-0DTE-Report.pdf)
- For most of 2022-2023, 0DTE was over 75% of retail SPX volume. — [Bonus.com](https://www.bonus.com/news/zero-days-to-expiration-options-investment-or-gambling/)

### Inferences
- No source finds that unconditionally *buying* ATM/OTM 0DTE options has positive expected value. The VRP means a buyer pays a small premium (about 0.001% of spot at the median from 10:00), so the pricing penalty is small. The real damage comes from costs and the payoff distribution: most long options lose, a few win big, and over a short sample the result is mostly noise.
- Retail does better (or less badly) when it uses limit orders. A bot that sends market orders on entry and on stop-loss exits gives up the main mitigation the DERA and Bogousslavsky-Muravyev papers identify.
- The exchange-sourced research (Cboe) leans favorable, and the independent academic work (Beckmeyer et al., BPS, Bogousslavsky-Muravyev on 0DTE) leans negative. Weight it accordingly.

### Gaps
- No paper found reports long 0DTE returns by *time of day of entry* for a buyer who exits intraday (Vilkov's appendix covers 13:00 and 15:00 entries held to close, but I could not see those tables).
- I found no Cboe report of aggregate customer P&L in 0DTE.
- The Brogaard-Han-Won paper itself was not reachable.

## 3. Average returns of buying ATM/OTM 0DTE calls and puts by moneyness and time of day (variance risk premium)

### Takeaway
On SPX, buying ATM-to-OTM 0DTE calls and most puts at 10:00 and holding to the close loses money on average in spot terms. Returns relative to premium are hugely skewed and usually not significantly different from zero. OTM puts are the most overpriced (the skew and the upside-concentrated VRP), while deep ITM calls look best, partly because of market drift.

### Cited Findings
- Long ATM-to-OTM calls and most puts lose on average (spot-scaled P&L, 10:00 to close, SPXW 2016-2026). Means are often statistically insignificant. ITM contracts have spot-scaled interquartile ranges of 0.7-0.8%. — [Vilkov 2026](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- The VRP is positive and statistically significant at every 30-minute bar to expiry, but economically small. — [Vilkov 2026](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- The 0DTE VRP is larger than the 1DTE VRP (about 1.5-2.95% annualized depending on entry time, versus 0.55%) and concentrated in upside moves, i.e. calls are also overpriced. Unverified secondary review. — [FirmTape](https://firmtape.com/research/what-the-0dte-literature-claims)
- Beckmeyer et al. attribute the non-cost part of retail losses to 0DTE put purchases and high-IV options. — [Neudata](https://neudata.co/literature-reviews/zero-day-to-expiry-options-a-losing-bet-for-retail-traders); [College Sidekick](https://www.collegesidekick.com/study-docs/2487577)
- Time-decay timing: Option Alpha's study (SPX 5-wide verticals, minute quotes, July-August 2024) finds 0DTE decay accelerates sharply after 3:30 PM ET, and early entries capture little more premium than late ones. This is a practitioner study from a vendor of 0DTE tools, with a short sample. — [Option Alpha](https://optionalpha.com/blog/0dte-options-time-decay)

### Inferences
- For a *buyer* with a directional signal, the VRP alone is a small drag. Over a 20-60 minute hold, the larger costs are (a) the spread paid twice, (b) theta that is real on *that* holding window (see section 4), and (c) the stop-loss mechanics that turn noise into realized losses.
- Puts look structurally more expensive than calls (skew), so the same signal accuracy should earn less on the put side.

### Gaps
- No source gives numerical average returns per moneyness bucket for intraday (not to-close) holds. The Vilkov figures exist but were not readable as text.
- I found no studies for QQQ or single-stock 0DTE buyer returns.

## 4. Spreads as a % of premium (SPY/QQQ 0DTE vs single-stock weeklies) and the hurdle a signal must clear

### Takeaway
Liquid SPY/QQQ near-ATM 0DTE spreads are about $0.01-0.05 (about 0.5-2.5% of a roughly $2 premium). Across all 0DTE options the average quoted spread is about 9%, and for short-dated retail-traded options overall about 12.6%, rising to about 29% for OTM. Single-stock weeklies are wider (no good measured source). With theta added, a near-ATM 0DTE buyer needs an underlying move of a few hundredths of a percent just to break even over 30 minutes, and much more late in the day.

### Cited Findings
- Doshi & Pederzoli: the average relative spread ranges from about 9% for 0DTE options to about 2% for 21-48 DTE options (S&P options). (abstract and snippet) — [Doshi & Pederzoli, "Risky Intraday Order Flow and Option Liquidity" (JFQA)](https://paolapederzoli.com/wp-content/uploads/2025/07/risky_order_flow_jfqa.pdf)
- Short-dated (under a week) retail-traded options: 12.6% average quoted spread; OTM 28.7%; micro trades 23.5%. — [Bryzgalova et al., Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13285)
- Typical retail option quoted spread is 3.7% (all maturities). — [Bogousslavsky & Muravyev](https://www.lsu.edu/business/files/event-files/2025-finance-mardi-gras/retail_option_trading_v2.pdf)
- SPY near-ATM 0DTE: about $0.01-0.05 wide, compared with $0.10-0.30 for SPX. Spreads can widen to $0.15-0.40 in the last 15 minutes. These are practitioner blogs, not measured studies. — [TradingBlock](https://www.tradingblock.com/blog/0dte-spy-vs-spx-options); [MarketXLS](https://marketxls.com/blog/how-to-trade-0dte-spy-options-expert-insights)
- Less liquid single-name options: the spread "can eat 10-20%" of the premium (anecdotal). Weeklies are less liquid than monthlies on some names. — [Longbridge](https://longbridge.com/en/academy/options/blog/comparative-analysis-0dte-vs-weekly-vs-monthly-options-which-is-right-for-you-100039); [Options Cafe](https://options.cafe/blog/spy-put-credit-spreads-strategy/)
- Option Alpha notes that Black-Scholes-based probability and EV estimates are less accurate for 0DTE. — [Option Alpha](https://optionalpha.com/blog/0dte-options)

### Inferences (my arithmetic; standard ATM approximation, value ≈ 0.4 × σ × S × √T; illustrative, not measured)
- **SPY at $580, IV 15%, ATM 0DTE call bought at 10:00 (6 trading hours left):** value ≈ 0.4 × 0.15 × 580 × √(6/6.5/252) ≈ **$2.11**, delta ≈ 0.5.
  - **Spread:** a $0.02 spread costs $0.02 round trip if you cross half each way (about 1% of premium). That is equivalent to a SPY move of $0.04 (0.007%). This is cheap on SPY/QQQ.
  - **Theta:** after 30 minutes the value with no move is ≈ $2.02, a loss of about $0.09 (about 4% of premium). Recovering it needs about a $0.18 SPY move (0.03%) in your favor. After 60 minutes the loss is about $0.19 (about 9%). **A -10% premium stop, as in config.yaml's shipped premium exits, is hit by theta alone in about an hour with SPY flat**, or by about a $0.42 (0.07%) adverse move at once.
  - **Late in the day:** with 1 hour left the ATM value is ≈ $0.86, and with 30 minutes left ≈ $0.61. The last half hour costs about $0.25 (about 29% of the 1-hour value). Combined with spreads widening to $0.15-0.40, late entries face a hurdle several times larger.
- **Single-stock weeklies:** with spreads of 5-20% of premium, the round-trip spread alone can exceed a typical 20-60 minute move times delta. A signal must then predict moves several times the spread/delta ratio. For an ATM option with a $2 premium and a 10% spread ($0.20), that is a $0.40 stock move just to pay costs.
- **Comparison, ATM 5DTE:** value ≈ 0.4 × 0.15 × 580 × √(5/252) ≈ $4.90. Theta per trading hour ≈ value / (2 × hours left) ≈ $0.075, against about $0.18 per hour for 0DTE at 10:00. Spreads in dollars are similar on SPY, so the percentage cost is lower. Delta per dollar of premium is lower (less leverage).
- These figures connect to the repo's own corrected baseline (CLAUDE.md): 92 stops at -10% of premium against 21 targets. They are consistent with premium-based stops being triggered by theta plus noise rather than by thesis failure.

### Gaps
- No measured, sourced table gives median percent-of-premium spreads for SPY/QQQ 0DTE by time of day, or for single-stock weeklies by name. This could be measured directly from the repo's own option-bar cache (`data/option_bars/`) or from Alpaca quotes.
- QQQ-specific spread figures were not found.

## 5. Underlying/futures vs ITM/high-delta options vs 1-7 DTE for intraday directional signals

### Takeaway
No rigorous study compares executing the same intraday directional signal through stock, ITM options or 1-7 DTE options. The indirect evidence points away from ATM/OTM 0DTE:
- Costs per unit of delta are lowest in the underlying or futures, then ITM and longer-dated options.
- ITM options attract retail because of their higher hit rate, but retail still underperforms with them when trading during volatility spikes.
- 0DTE retail trades do about 3% worse than other option trades.

### Cited Findings
- 0DTE trades earn about 3% lower returns than other retail option trades. — [Bogousslavsky & Muravyev](https://www.lsu.edu/business/files/event-files/2025-finance-mardi-gras/retail_option_trading_v2.pdf)
- Spreads fall from about 9% at 0DTE to about 2% at 21-48 DTE. — [Doshi & Pederzoli](https://paolapederzoli.com/wp-content/uploads/2025/07/risky_order_flow_jfqa.pdf)
- Lopez Avila, "In the Money? Low-Leverage Option Betting": ITM options take a larger share of dollar volume than expected, especially for small customers in large-cap, short-maturity contracts. Buyers seek higher hit rates and steadier returns. "ITM options investors often underperform by trading during periods of high stock volatility and elevated retail attention." (abstract) — [MIT Sloan PDF](https://mitsloan.mit.edu/sites/default/files/inline-files/Session3_Paper1_In%20the%20Money.pdf); [Harbourfront summary](https://harbourfrontquant.substack.com/p/examining-itm-options-among-retail)
- Vilkov: deep ITM 0DTE calls can be profitable at the median (consistent with market drift), and ITM legs give more symmetric distributions with means near zero. — [Vilkov](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- Beckmeyer et al.: the losses concentrate in single-leg debit and high-IV trades. — [College Sidekick](https://www.collegesidekick.com/study-docs/2487577)

### Inferences
- For a bot whose signal is a forecast about the *underlying* (as `edge_tracker` scores it), the cleanest test of the signal is the underlying itself (shares, or futures/micro futures). There is no theta, no VRP, no IV crush and a penny spread. If the signal does not make money on the underlying after costs, no option structure will rescue it. The repo's TJR record (PF about 0.91-0.97 on the underlying *before* option costs) already fails this test.
- If options are used:
  - Higher delta (about 0.6-0.8 ITM) reduces theta per unit of delta and the share of extrinsic value lost to spread.
  - 1-7 DTE reduces theta per hour by about 2-3x relative to 0DTE at 10:00 (arithmetic above) and narrows relative spreads.
  - Limit orders at or inside mid matter, per DERA and Bogousslavsky-Muravyev.
- Size and stops should then be set in *underlying* terms (the chart stop × delta), not as a percent of premium. The repo's `mode: risk` / `exits.measure: structure` already does this.

### Gaps
- I found no peer-reviewed or data-backed practitioner study that runs the same intraday signals through stock vs 0DTE vs weeklies. Tastytrade, SpotGamma and Option Alpha material found is about *selling* premium or market structure, not directional buying, and is partly marketing.
- This is a natural in-repo experiment: run the same `smc_retrace` signals through (a) shares, (b) 0.7-delta 0DTE, (c) ATM 3-5 DTE.

## 6. Pattern day trader (PDT) rule changes 2025-2026

### Takeaway
The SEC approved FINRA's amendment to Rule 4210 on 14 April 2026. It eliminates the "pattern day trader" designation and the $25,000 minimum, and replaces them with intraday margin standards (risk-based intraday buying power, with a $2,000 margin-account minimum). It took effect on 4 June 2026, but brokers have until 20 October 2027 to implement it, so whether a given account is still bound depends on the broker.

### Cited Findings
- SEC accelerated approval on 14 April 2026 eliminates the PDT designation and the $25k minimum and approves new intraday margin standards. — [Schwab](https://advisorservices.schwab.com/story/sec-approves-scrapping-25000-day-trader-minimum); [Schwab International](https://international.schwab.com/story/sec-approves-scrapping-25000-day-trader-minimum); [Whale Alert story](https://whale-alert.io/stories/fea501b3bfe2f7/SEC-grants-accelerated-approval-to-remove-Pattern-Day-Trader-rule-and-25000-minimum-approves-new-intraday-margin-standards)
- Effective 4 June 2026. Firms have up to 18 months (to 20 October 2027) to implement. Firms may monitor intraday margin in real time or with an end-of-day check. Schwab planned to stop counting day trades from 8 June 2026. Margin accounts above $2,000 get broker-set intraday buying power, and day trades are no longer counted. — [E*TRADE](https://us.etrade.com/knowledge/library/margin/pattern-day-trading-rule-change); [tastytrade](https://tastytrade.com/learn/markets/industry/pattern-day-trading/); [Gotrade blog](https://www.heygotrade.com/en/blog/the-pattern-day-trader-rule-is-gone-what-it-means-for-retail-us-stock-traders/)

### Inferences
- The repo's PDT guard (which blocked 790 entries in the corrected baseline once the sim account fell below $25k) models a rule that is being phased out. Whether to keep it depends on **when Alpaca implements** the new intraday margin standard. Until Alpaca confirms the change, keeping the guard is the safe default (CLAUDE.md: don't weaken safety rails).
- Removing the PDT limit does not remove the economics above. A small account trading more 0DTE contracts simply pays more spread and theta.

### Gaps
- I found no source for Alpaca's implementation date. Check Alpaca's announcements or support pages.
- I could not read the rule text from FINRA or the Federal Register directly. The dates above come from broker pages, which agree with each other.
