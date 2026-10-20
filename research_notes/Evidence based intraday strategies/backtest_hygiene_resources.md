# Backtest hygiene and systematic day-trading resources: what a trading-bot project should adopt

Research note, 2026-10-20. Method caveat: in this session WebFetch and curl could not reach any paper host (SSRN, davidhbailey.com, carmamaths.org, escholarship, Wikipedia, CRAN: DNS failure or proxy 403). Findings come from search-result abstracts and summaries of the primary papers. The formulas below are the standard published forms from Bailey & López de Prado. I checked them numerically against the papers' own worked examples (see Q1), but you should verify them against the PDFs before you hard-code them. Numbers marked "computed" are my arithmetic (Python, normal approximation), not quotes.

## Q1. Probability of Backtest Overfitting (CSCV), "Pseudo-Mathematics and Financial Charlatanism", and the Deflated Sharpe Ratio: formulas and how to apply them to a search over N variants

### Takeaway
Every variant you try raises the best backtest you should expect from pure noise. The bar a winner must clear therefore has to rise with N, the number of variants tried. Three tools set that bar. MinBTL says how long a backtest must be for a given N. DSR asks whether the winner's Sharpe beats the expected maximum of N noise strategies. PBO (via CSCV) measures how often the in-sample winner lands in the bottom half out of sample. A bot project should log every variant it ever ran so that N is honest.

### Cited Findings
- **Pseudo-Mathematics and Financial Charlatanism** (Bailey, Borwein, López de Prado, Zhu, *Notices of the AMS* 61(5), 2014, pp. 458–471; free PDF). The paper's claims:
  - With a fixed sample length, trying enough configurations will always produce a backtest with any desired performance, so a minimum backtest length (MinBTL) must be required for a given number of trials.
  - Example: with only 5 years of data, try no more than 45 independent configurations, or a strategy with in-sample annualized SR 1 is likely to have an expected out-of-sample SR of 0.
  - After only 7 configurations, a researcher is expected to find at least one 2-year backtest with annualized SR above 1 when the true out-of-sample SR is 0.
  - The bound assumes independent trials, which the authors call conservative.
  - Sources: [core.ac.uk record](https://core.ac.uk/display/24055290); [Carma PDF](https://carmamaths.org/jon/backtest.pdf); [AMSI release](https://amsi.org.au/?p=995)
- **MinBTL formula** (from the same paper). Computed check: N=45 gives about 5.0 years and N=7 gives about 1.9 years, which matches both of the paper's examples. ([Carma PDF](https://carmamaths.org/jon/backtest.pdf))
  - E[max SR_N] ≈ sqrt(V[SR]) · [ (1−γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e)) ], where γ ≈ 0.5772 is the Euler–Mascheroni constant.
  - MinBTL (years) ≈ ( (1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne)) )² / (E[max SR])², with an upper bound of 2·ln(N) / (E[max SR])².
- **The Deflated Sharpe Ratio** (Bailey & López de Prado, *Journal of Portfolio Management* 40(5), 2014, pp. 94–107). DSR corrects for two sources of inflation: selection bias under multiple testing, and non-normal returns. ([SSRN 2460551](https://papers.ssrn.com/abstract=2460551))
  - Probabilistic Sharpe Ratio: PSR(SR*) = Φ( (SR̂ − SR*) · sqrt(T − 1) / sqrt(1 − γ̂₃·SR̂ + ((γ̂₄ − 1)/4)·SR̂²) ). Here T is the number of return observations, γ̂₃ the skew and γ̂₄ the (non-excess) kurtosis. All quantities are per observation, not annualized.
  - DSR is the PSR with the benchmark SR* set to E[max SR_N] from the formula above, using the variance of the Sharpe ratios across the N trials. Deflated, the Sharpe ratio becomes the probability that the true SR exceeds the expected maximum from N noise trials. ([MetricGate summary](https://metricgate.com/docs/deflated-johnson-sharpe-ratio/))
  - Minimum track record length, from the companion paper by Bailey & López de Prado, "The Sharpe Ratio Efficient Frontier" (2012): MinTRL = 1 + (1 − γ̂₃·SR̂ + ((γ̂₄−1)/4)·SR̂²) · (z_α / (SR̂ − SR*))².
- **Implementation pitfalls from library documentation:**
  - Pass the empirical variance of the trial Sharpe ratios. A placeholder variance of 1.0 overstates the benchmark. ([fynance docs](https://fynance.readthedocs.io/en/latest/generated/fynance.research.deflated_sharpe_ratio.html))
  - Convert annualized Sharpe ratios to per-observation values first, or the DSR saturates near 1. ([fynance docs](https://fynance.readthedocs.io/en/latest/generated/fynance.research.deflated_sharpe_ratio.html))
  - Off-the-shelf implementations exist: vectorbt's `approx_exp_max_sharpe` ([vectorbt](https://vectorbt.dev/api/returns/metrics)) and R quantstrat's `deflatedSharpe` ([rdocumentation](https://www.rdocumentation.org/packages/quantstrat/versions/0.16.7/topics/deflatedSharpe)).
- **The Probability of Backtest Overfitting** (Bailey, Borwein, López de Prado, Zhu, *Journal of Computational Finance* 20(4), 2017; SSRN drafts from 2013). It proposes combinatorially symmetric cross-validation (CSCV), a model-free, nonparametric way to estimate the probability that the selected strategy is overfit, and argues that standard hold-out validation is unreliable for investment backtests. An R package, `pbo`, implements it; any performance metric can replace the Sharpe ratio under the paper's assumptions. ([SSRN 2326253](https://papers.ssrn.com/abstract=2326253); [Risk.net](https://www.risk.net/journal-of-computational-finance/2471206/the-probability-of-backtest-overfitting); [pbo README](https://ftp.fau.de/cran/web/packages/pbo/readme/README.html))
- **CSCV algorithm** (standard description of the paper's method; I could not fetch the full text to quote it):
  1. Build a T×N matrix M of per-period returns, one column per variant.
  2. Split the rows into S equal contiguous blocks, with S even (the paper's examples use S=16).
  3. For every one of the C(S, S/2) ways to choose half the blocks as in-sample (IS), the complement is out-of-sample (OOS).
  4. Pick the variant n* with the best IS metric and find its relative rank ω in OOS, between 0 and 1.
  5. Compute the logit λ = ln(ω/(1−ω)).
  6. PBO = the share of combinations with λ ≤ 0, meaning the IS winner ranked at or below the OOS median.
  - The paper also reports a degradation regression (OOS metric on IS metric), the probability of an OOS loss, and stochastic dominance. ([SSRN 2326253](https://papers.ssrn.com/abstract=2326253))

### Inferences
- **Apply this to Scalp City.**
  - Keep a variants ledger: every config hash ever backtested, with its per-day return series on a common calendar. N is the count of distinct variants tried, and V is the variance of their Sharpe ratios.
  - With roughly 30–90 trading days per test window (Sep 1–Oct 15 is about 32 sessions; Jun 1–Oct 15 is about 95), MinBTL rules out claiming an SR≈1 edge after more than 1–2 variants. The computed MinBTL at SR 1 is 0.27 years for N=2 and 1.4 years for N=5. Daily returns over a few months cannot validate a selected strategy. They can only reject one.
  - The project has already tried many variants: six strategies, aligned exits, the TJR filters and per-ticker splits. Any future "winner" must clear DSR > 0.95 with N counting all of those variants, not only the last sweep.
  - Run CSCV with S=8–16 day-blocks on the M matrix of all variants, and report PBO alongside every headline result. PBO > 0.5 means selection is worse than random.

### Gaps
- I could not fetch the full DSR, PBO or Notices PDFs, so the exact equation numbering and the papers' recommended S are not quoted from source.

## Q2. Harvey, Liu & Zhu ("...and the Cross-Section of Expected Returns"): the t > 3 hurdle; Harvey & Liu "Backtesting": the Sharpe haircut

### Takeaway
After a lot of data mining, t ≈ 2 is not enough. A newly discovered effect should clear t > 3. Reported Sharpe ratios should be "haircut" for multiple testing, and the haircut is heavy for marginal strategies.

### Cited Findings
- Harvey, Liu & Zhu, *Review of Financial Studies* 29 (2016), pp. 5–68; NBER WP 20592 (2014).
  - "A newly discovered factor needs to clear a much higher hurdle, with a t-ratio greater than 3.0." Using the usual criteria after extensive data mining "does not make any economic or statistical sense."
  - The paper provides a time series of historical significance cutoffs from 1967 onward.
  - Sources: [NBER w20592](https://www.nber.org/papers/w20592); [SSRN 2513152](https://papers.ssrn.com/abstract=2513152)
- Counterpoint: Andrew Chen (2022) argues that at least 75% of published cross-sectional findings are true, and that HLZ's own estimates imply a similar false discovery rate. The t > 3 rule is conservative, not universally settled. ([arXiv 2206.15365](https://arxiv.org/pdf/2206.15365))
- Harvey & Liu, "Backtesting," *Journal of Portfolio Management* 41(1), 2015, pp. 13–28 (free PDF on Duke site).
  - "The 50% haircut is only a rule of thumb… it is a serious mistake to use the usual 50% haircut."
  - The paper gives a method that sets a haircut for any reported Sharpe ratio, plus a profit hurdle a strategy must clear to be significant. It uses Bonferroni, Holm and BHY (Benjamini–Hochberg–Yekutieli) adjustments.
  - The haircut is nonlinear: "the highest Sharpe ratios are only moderately penalized while the marginal Sharpe ratios are heavily penalized."
  - Sources: [Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF); [CME-hosted copy](https://www.cmegroup.com/content/dam/cmegroup/education/files/backtesting.pdf)
- Secondary summary of the haircut sizes: for an annualized SR below about 0.4 the haircut is almost always above 50%; above 1.0 it is at most 25%. ([CXO Advisory](https://www.cxoadvisory.com/big-ideas/navigating-the-data-snooping-icebergs/))
- R code for the haircut and profit hurdle is in quantstrat's sandbox (`Haircut_SR`, `profitHurdle`). ([rdrr.io](https://rdrr.io/github/braverock/quantstrat/man/profitHurdle.html))
- Related tests on trading rules: White's Reality Check, Hansen's SPA, and the Romano–Wolf stepwise versions.
  - Neuhierl & Schlusche (*Journal of Financial Econometrics*, 2011): market-timing rules that beat buy-and-hold in isolation "generally" lose significance after a data-snooping correction. ([RePEc](https://ideas.repec.org/a/oup/jfinec/v9y2011i3p550-587.html))
  - Hsu and Kuan found significant simple rules in "young" markets (NASDAQ Composite, Russell 2000) but not in the DJIA or S&P 500. ([HKU repository](https://repository.hku.hk/handle/10722/141768); [PDF mirror](https://c.mql5.com/forextsd/forum/211/Re-Examining%20the%20Profitability%20of%20Technical%20Analysis%20with%20Whitets%20Reality%20Check%20and%20Hansen9s%20SPA%20Tes.pdf))

### Inferences
- **Implementable rules.**
  - Require the mean per-trade R to have t ≥ 3, not 2, for any strategy that came out of a search (t = mean_R / (sd_R / √n)).
  - When several triggers or tickers are tested together, adjust p-values with Holm (controls the family-wise error rate) or BHY (controls the false discovery rate) before declaring any of them "proven."
  - The research gate's "past-5-session edge" is a per-ticker, per-trigger hypothesis test run many times a day. Without a multiplicity correction it will mostly select noise, which matches the observed ~39% forward win rate against the 45% requirement.

### Gaps
- I did not see the paper's exact haircut tables, so specific haircut percentages for given (SR, N) pairs are not quoted.

## Q3. López de Prado, *Advances in Financial Machine Learning* (Wiley, 2018): what matters for intraday rule-based bots

### Takeaway
The book's labeling and cross-validation tools fit an event-driven rule bot directly. Triple-barrier labels match "stop, target or time limit," which the bot's edge tracker already uses. Purging and embargo stop overlapping trades from leaking between train and test. Meta-labeling separates "which direction" from "take it or not, and how big."

### Cited Findings
- **Purged k-fold (Ch. 7).**
  - Remove training observations whose label windows overlap the test set.
  - Embargo: also drop a buffer of training observations right after each test block, to handle serial correlation.
  - Plain k-fold may be fine only when labels are contemporaneous and observations independent, not with overlapping forward labels.
  - Sources: [LuxAlgo explainer](https://www.luxalgo.com/library/concept/purged-cross-validation.md); [QuantT](https://www.quantt.co.uk/resources/purged-cross-validation)
- **Triple-barrier labeling.** Each event gets an upper barrier (profit), a lower barrier (loss) and a vertical time barrier. The label records which is touched first, so the label is path-dependent. ([LuxAlgo](https://www.luxalgo.com/library/concept/label-definition-and-prediction-horizon.md))
- **Labels use future prices by design.** Route them through a purged and embargoed split so that no training fold ends inside the [t_in, t_out] span of a validation label. ([fynance labels docs](https://fynance.readthedocs.io/en/latest/features.labels.html))
- **Meta-labeling.** A primary signal from any strategy proposes a side. A secondary model learns whether that signal would have been profitable, and so decides whether to act and how much to size, not which direction. ([LuxAlgo](https://www.luxalgo.com/library/concept/label-definition-and-prediction-horizon.md))
- The book also contains the DSR, PBO/CSCV, combinatorial purged cross-validation (CPCV) and backtest-statistics chapters. It is a paid book; the author's SSRN papers cover much of the same material for free. ([book listing](https://www.exlibris.ch/de/buecher-buch/english-books/marcos-lopez-de-prado/advances-in-financial-machine-learning/id/9781119482086/))

### Inferences
- **Mapping to Scalp City.**
  - `edge_tracker` already does triple-barrier scoring (stop_atr or chart stop, target, horizon_minutes).
  - The research gate's rolling "last 5 sessions" window is a form of walk-forward. For any parameter fitting, though, use purged CV (folds by day plus a 1-day embargo), so a trade opened on the last minute of a training day cannot leak.
  - Meta-labeling is the principled form of the "gate". Use it only after the primary trigger shows positive expectancy, since a filter cannot make an edge out of nothing.

### Gaps
- I did not read the book's text directly in this session. The chapter attributions come from secondary explainers.

## Q4. Practical books, courses and free resources: what each teaches, whether free, and how respected

### Takeaway
The respected core: Chan (bias catalogue and simple mean-reversion and momentum), Carver (position sizing, avoiding overfitting by not fitting at all, cost-aware rules), Davey (a staged development pipeline: walk-forward, Monte Carlo, incubation), and López de Prado / Bailey / Harvey (the statistics). The intraday ORB papers of Zarattini and Aziz are free and influential, but independent replications show the edge is fragile to costs.

### Cited Findings
- **Ernest Chan, *Quantitative Trading*** (2nd ed., Wiley 2021; paid). Covers look-ahead, survivorship and data-snooping bias, and "Common Backtesting Pitfalls to Avoid." His free slide deck defines all three biases and shows survivorship bias inflating a "buy the cheapest stocks" backtest to 388% in 2001. *Algorithmic Trading* (Wiley 2013, paid) covers mean reversion, momentum and intraday strategies with the same discipline. ([CMT-hosted Chan slides, free](https://cmtassociation.org/wp-content/uploads/2024/01/erniechan-020211-1.pdf); [book TOC](https://www.schweitzer-online.de/en/ebook/Chan/Quantitative-Trading/9781394428236/A75686985/))
- **Robert Carver** (*Systematic Trading*, *Advanced Futures Trading Strategies*; paid books; free blog "qoppac"). An independent systematic futures trader and visiting lecturer at Queen Mary, University of London. His talks include "Three Judases: Overfitting three different ways" and "The Myth of the Perfect Trading System." His workshops cover statistical significance, robustness and three types of overfitting. ([CMT Association bio](https://cmtassociation.org/?p=17000); [WBS training](https://www.wbstraining.com/?p=15809))
- **Kevin Davey, *Building Winning Algorithmic Trading Systems*** (Wiley 2014; paid).
  - Walk-forward: optimize on a slice, test on unseen data, roll forward.
  - A "one-shot" evaluation against predefined criteria (for example return/drawdown), with no tweaking after the result.
  - Monte Carlo reshuffles of trades, thousands of runs, to get drawdown and return distributions.
  - Incubation: monitor without real money for 6–12 months to expose slippage, commissions and data anomalies. Davey reports that 85–90% of students in a survey said incubation helped them avoid bad strategies or confirm good ones.
  - These figures come from secondary summaries. ([Algo Advantage podcast summary](https://algoadvantage.substack.com/p/036-kevin-davey-part-i-its-all-about); [IBKR repost](https://www.interactivebrokers.com/campus/ibkr-quant-news/algo-advantage-036-kevin-davey-part-i-its-all-about-process-in-algo-trading/); [FinancialWisdomTV summary](https://www.financialwisdomtv.com/post/building-winning-algorithmic-trading-systems-kevin-davey-s-complete-framework-for-trading-success))
- **Zarattini, Aziz (and Barbon): intraday ORB papers** (free on SSRN).
  - "Can Day Trading Really Be Profitable?" (2023, SSRN 4416622): a 5-minute ORB on QQQ. One commentary notes that it charges commissions but no spread or slippage, and has no out-of-sample period. ([CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy))
  - "A Profitable Day Trading Strategy for the U.S. Equity Market" (2024): an ORB on "Stocks in Play" (high relative volume).
    - A secondary report gives 1,637% total return 2016–2023 and Sharpe 2.81 ([letsdatascience](https://www.letsdatascience.com/news/traders-adopt-orb-strategy-for-stocks-in-play-19394da2)).
    - A QuantConnect recreation reported Sharpe 2.4 ([QuantConnect forum](https://quantconnect.com/forum/discussion/18444/Opening+Range+Breakout+for+Stocks+in+Play/p0/comment-37562)).
    - An independent replication titled "gross reproduced, net zero" found the edge disappeared after costs on five indices ([MQL5 blog](https://www.mql5.com/en/blogs/post/776235)).
- **Quantopian** ("All that Glitters Is Not Gold," 888 algorithms; free paper).
  - Commonly reported backtest metrics such as the Sharpe ratio "offer little value in predicting out of sample performance."
  - The more backtesting a quant did on a strategy, the larger the gap between backtest and out-of-sample results.
  - Sources: [Quantpedia summary](https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/); [PDF mirror](https://c.mql5.com/forextsd/forum/208/All%20that%20Glitters%20Is%20Not%20Gold%20%20%20Comparing%20Backtest%20and%20Out%20of%20Sample%20Performance%20on%20a%20Large%20Cohort%20o.pdf)
- **Free courses.**
  - Georgia Tech / Udacity "Machine Learning for Trading" (Tucker Balch): free, self-paced, three mini-courses (financial data in Python, computational investing, ML for trading). Mixed reviews: 3.1 out of 5 from 14 reviews on Class Central. ([Class Central](https://classcentral.com/course/udacity-machine-learning-for-trading-1026); [my-mooc listing](https://www.my-mooc.com/fr/mooc/machine-learning-for-trading--ud501))
  - Coursera "Trading Strategies in Emerging Markets": only aggregator pages found; price and partner unverified. ([staff.am mirror](https://staff.am/trainings/trading-strategies-in-emerging-markets-specialization))

### Inferences
- The best free reading list for this project: Bailey et al. (Notices 2014), Harvey & Liu "Backtesting" (Duke PDF), the Quantopian 888-algo paper, Chan's slide deck, the Zarattini ORB papers, and the MQL5 net-of-cost replication as a cautionary pair.
- Paid but worth it: Davey (process), Carver (sizing and robustness), López de Prado (statistics).
- Aziz's Bear Bull Traders material is discretionary education and marketing, not peer-reviewed evidence. Its ORB papers are the citable part.

### Gaps
- Not found: the free QuantConnect "Bootcamp/Learning Center" or the archived Quantopian lecture series content (search returned nothing primary). Carver's specific "years of data needed" guidance is unverified (only a Reddit attribution). The Coursera course price and partner are unverified.

## Q5. Sample-size rules of thumb: win rate within ±5%, and significance of expectancy (mean R)

### Takeaway
To know a win rate within ±5 percentage points (95% confidence) takes about 250–385 trades. Proving a small positive expectancy takes thousands. With 4 trades, or 208 setups at −0.04R, nothing can be concluded except "no detectable edge."

### Cited Findings
- **Binomial sample size** (computed: n = 1.96²·p(1−p)/h², normal approximation):
  - p=0.5: 385 trades for ±5pp, 97 for ±10pp.
  - p=0.4: 369 and 93.
  - p=0.3: 323 and 81.
  - p=0.2: 246 and 62.
- **Expectancy t-test** (computed: n = (t·sd_R / mean_R)²):
  - mean +0.3R, sd 1.5R: n=100 for t=2, 225 for t=3.
  - mean +0.2R, sd 1.5R: n=225 for t=2, 507 for t=3.
  - mean +0.1R, sd 1.2R: n=576 for t=2, 1,296 for t=3.
  - A 30%-win, +2.5R/−1R system (mean +0.05R, sd ≈1.6R): n≈4,100 for t=2 and about 9,300 for t=3.
- **Applied to the project's TJR record** (computed): 208 in-plan setups at −0.039R with an assumed sd of about 1.5R give a standard error ≈ 0.10R, so the 95% interval is roughly −0.24R to +0.17R. That is consistent with zero, and not evidence of a positive edge.
- The t > 3 hurdle applies once a strategy was selected from many. ([NBER w20592](https://www.nber.org/papers/w20592))
- Low-Sharpe (marginal) strategies get the biggest multiple-testing haircut. ([Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF))

### Inferences
- **Implementable rules.**
  - Report a Wilson interval for the win rate and a t-stat (or bootstrap CI) for mean R on every backtest.
  - Refuse to label any trigger "edge" below n≈100 scored setups.
  - Use t ≥ 3 after a search. Use profit factor and expectancy, not win rate, since the owner's 95% win-rate goal is not a meaningful target for a low-win-rate, high-R:R plan.
  - Treat trades on the same day across correlated tickers (SPY, QQQ, IWM) as clustered: compute the t-stat on daily R sums, or use a block bootstrap by day.

### Gaps
- No primary source gives a canonical "N trades" rule for retail systems. The numbers above are standard statistics, not quotes.

## Q6. Transaction-cost modeling and regime checks

### Takeaway
Costs and slippage are the most common reason a published intraday edge disappears in replication. Model spread, fees and slippage explicitly, and stress them. Check robustness across volatility regimes and sub-periods.

### Cited Findings
- **Costs.**
  - The QQQ ORB paper charged commissions but no spread or slippage. ([CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy))
  - An ORB replication reproduced the gross results, but net profit was zero. ([MQL5](https://www.mql5.com/en/blogs/post/776235))
  - Davey's incubation exists to expose slippage, commissions and data anomalies that the backtest missed. ([Algo Advantage](https://algoadvantage.substack.com/p/036-kevin-davey-part-i-its-all-about))
- **Regimes.** Trading-rule profitability found in "young" markets (NASDAQ, Russell 2000) was absent in mature ones (DJIA, S&P 500), and the evidence for growth and emerging indices weakened after ETFs were introduced. Edges are market- and era-dependent. ([HKU repository](https://hub.hku.hk/handle/10722/141771))

### Inferences
- **Implementable rules for 0DTE options.**
  - Fill at the ask to buy and the bid to sell, never the mid or last trade (the repo already found the stale-last-trade bug).
  - Run every backtest a second time with slippage doubled. A strategy that only works at zero slippage is rejected.
  - Split results by VIX tercile, trend versus range day, and month. Require a positive expectancy in at least 2 of 3 regimes, with no single month providing most of the profit.

### Gaps
- I found no primary study of 0DTE option bid/ask costs in this session.

## Q7. How professional and prop practice decides a strategy is ready for live: incubation and kill criteria

### Takeaway
The standard pipeline runs: idea, one-shot out-of-sample or walk-forward test against criteria fixed in advance, Monte Carlo of drawdowns, paper/incubation for 6–12 months, small live size, then scale. Kill rules are set before going live, from the Monte Carlo distribution.

### Cited Findings
- Davey's pipeline: walk-forward, a one-shot evaluation with no post-hoc tweaks against predefined criteria (for example return/drawdown), Monte Carlo trade reshuffling (thousands of runs) to set the expected drawdown range, then 6–12 months of incubation without real money. ([Algo Advantage](https://algoadvantage.substack.com/p/036-kevin-davey-part-i-its-all-about); [FinancialWisdomTV](https://www.financialwisdomtv.com/post/building-winning-algorithmic-trading-systems-kevin-davey-s-complete-framework-for-trading-success))
- The more a strategy was backtested, the worse its out-of-sample shortfall: evidence for freezing the strategy before incubation. ([Quantpedia/Quantopian](https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/))
- MinTRL (Q1) gives a statistical length for a live or paper track record before the Sharpe can be trusted. ([SSRN 2460551](https://papers.ssrn.com/abstract=2460551))

### Inferences
- **Implementable gate for Scalp City** (paper only; going live is the owner's decision):
  - **Stage 1, research.**
    - Log every variant, giving N.
    - Hold out the most recent 30–40% of days untouched.
    - Walk-forward with daily re-fit if any parameters are fitted.
    - Require PBO < 0.2, DSR > 0.95, and t(mean R) ≥ 3 on n ≥ 100 trades, with net-of-cost profit factor > 1.3 and positive results at 2× slippage.
  - **Stage 2, one-shot holdout.** Run once. Fail means reject; never re-tune and re-run on the same holdout.
  - **Stage 3, Monte Carlo.** Bootstrap the trades by day to get the 95th-percentile max drawdown and losing streak.
  - **Stage 4, paper incubation** for at least 3–6 months, or MinTRL, whichever is longer.
  - **Kill criteria, set in advance:**
    - drawdown beyond the Monte Carlo 95th percentile;
    - rolling 50-trade mean R below the backtest mean minus 2 standard errors;
    - live losing streak longer than the Monte Carlo 99th percentile.
- Most of the numeric thresholds above are judgment calls built on the cited methods, not published constants. Label them as such to the owner.

### Gaps
- I found no primary, citable description of how specific prop or quant firms (for example Jane Street, Two Sigma, or prop funds) set kill rules. Public material is mostly practitioner summaries (Davey). The 6–12 month incubation figure comes from secondary summaries of Davey, not his book text.
