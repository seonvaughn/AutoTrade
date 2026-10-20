# Empirical evidence for ICT / Smart Money Concepts and related price-action ideas

Method note: researched 2026-10-20. WebFetch and curl were blocked in this session (DNS failure / proxy 403 on every domain tried: arxiv.org, newyorkfed.org, statoasis.com, thortradecopier.com). All findings below come from search-engine summaries of the cited pages, not from reading the full documents. Numbers quoted are what those summaries reported. Treat exact figures as "to verify against the primary source" before relying on them in code or reports.

## 1. Are there peer-reviewed or SSRN/arXiv studies testing ICT/SMC concepts (FVG fill rates, order block reactions, liquidity-sweep reversals)?

### Takeaway
No peer-reviewed or SSRN/arXiv study of ICT/SMC concepts (FVG, order block, liquidity sweep, BOS/MSS, Silver Bullet) turned up. Every number found comes from practitioner, vendor or blog sources. The closest academic work tests the ideas underneath ICT (stop clustering, round numbers, support/resistance), not ICT's rules themselves.

### Cited Findings
- Searches for "fair value gap" on SSRN/arXiv returned no academic study. A blog (Thortradecopier) states it found no peer-reviewed test of ICT/SMC and cites an *unreviewed 2026 preprint* reporting that liquidity sweeps signal **continuation**, the opposite of the ICT reversal thesis. The preprint was not identified or verified. — [Thortradecopier, "Does ICT smart money concepts work"](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work)
- The same blog's own random-walk simulation found that bullish FVGs were revisited within 20 bars at about the same rate as **random price levels (83.4% vs 83.5%)**. That suggests a high "FVG fill rate" is what random-walk geometry produces, not evidence of an edge. It is a blog simulation, not peer-reviewed. — [Thortradecopier](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work)
- A broker FAQ (Libertex, German) states FVG usefulness as a standalone signal is "not generally recognized or empirically supported." — [Libertex FAQ](https://libertex.com/de/faq/fair-value-gap-in-marktanalyse)
- Vendor definitions (LuxAlgo): an FVG is a three-candle imbalance, the gap between candle 1's high and candle 3's low in an up move. A sweep is when price trades beyond a level and then **closes back inside** the prior range. These pages give no validation data. — [LuxAlgo FVG](https://www.luxalgo.com/library/concept/fair-value-gap/); [LuxAlgo liquidity sweep](https://www.luxalgo.com/library/concept/liquidity-sweep/)
- A further search for a 2026 liquidity-sweep preprint returned only blogs and vendor pages, with no arXiv or SSRN paper. — [search results incl. BuildAlpha](https://www.buildalpha.com/backtest-ict-and-smc/)

### Inferences
- "FVGs get filled X% of the time" claims carry no information unless they are compared with a random-level baseline. Under a random walk, nearby price levels get revisited very often.
- The absence of any academic test of ICT rules is itself informative. The concepts are popular but not formalized enough, or not interesting enough, to attract published tests.

### Gaps
- The unnamed 2026 "sweeps signal continuation" preprint could not be located or verified.
- No academic FVG-fill or order-block reaction-rate study was found. If one exists, it is not indexed under these terms.

## 2. Rigorous practitioner and statistical studies: FVG fills and FVG retrace trading, prior-day/session high-low sweeps, Judas swing, Silver Bullet (10:00–11:00 ET)

### Takeaway
The most systematic practitioner test found (StatOasis, 648 backtests on SPY/QQQ/DIA/IWM, daily bars) shows **no statistically significant edge** for order blocks, FVGs, liquidity sweeps or OTE, and **0 of 648 beat buy-and-hold**. The one public mechanical Silver Bullet backtest on NQ/ES lost money on a tiny sample. Gap-fill statistics (opening gaps, not FVGs) show that high fill rates do not turn into a reliable edge after costs. Edgeful-style "probability" stats measure whether a level gets touched, not whether a trade makes money.

### Cited Findings
**StatOasis "I Backtested ICT / Smart Money Concepts: What Survives" (Sept 3, 2026, self-published):**
- Design: four ICT entries (order blocks, FVGs, liquidity sweeps, Optimal Trade Entry) plus three simple textbook entries, with parameter variants and three time exits. Tested on SPY, QQQ, DIA and IWM against a seeded coin flip and buy-and-hold, for **648 backtests** in total. Uses **daily bars**, so it does not address intraday trading. — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
- None of the four ICT entries showed a statistically significant forward-return edge. Best: **order blocks on SPY, about +0.121% over 5 days across 736 events, t = +1.22** (below the usual bar of 2). — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
- Nearly every variant was "profitable" in absolute terms, but **0 of 648 beat buy-and-hold**. In other words, the profit came from riding the index's upward drift. ICT entries were not worse than the simple entries. On SPY, 81.5% of order-block variants beat the random baseline. — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
- Caveats: a single self-published study with no independent replication. The exact rule code was not visible in the search summaries.

**Silver Bullet (10–11 ET FVG entry), public GitHub mechanical backtest (cjosh4toyotas-stack/silver-bullet-backtest):**
- NQ, all windows, roughly June–Sept 2026: **27 trades, 25.9% wins, PF 0.51, −$5,895 net** after $10/trade costs. The 10–11 window had only **3 trades, 0 wins, −$695**. ES: 37 trades, 32.4% wins, PF 0.87 in R. Base spec across 72 trades: total **−19.87R**. The best restricted variant (ES only) was **negative out of sample**. — [GitHub silver-bullet-backtest](https://github.com/cjosh4toyotas-stack/silver-bullet-backtest)
- Promotional sources claim 55–80% win rates for Silver Bullet / ICT models without methodology or sample sizes. — [Lune blog](https://lunefi.com/blog/ict-trading-strategy-2026-65-75-win-rates-prop-firm); [FundingPips](https://fundingpips.com/blog/ict-silver-bullet-strategy-explained); [Medium "Top 30 SMC strategies"](https://medium.com/@smcTradingStrategies/top-30-smart-money-trading-strategies-for-2026-29b51e372284) (55–70% win rate, RR >1:2.5, no methodology)
- An FXNX blog reports **58.2% directional follow-through** after liquidity sweeps compared with blind limit orders. No sample definition or significance test was found. — [FXNX](https://fxnx.com/en/blog/smart-money-concepts-work-backtest-evidence)

**Gap-fill statistics (opening/overnight gaps, a proxy rather than ICT FVGs):**
- ES and NQ, last ten years: overnight gap filled same RTH session **60% (ES) / 61% (NQ)**. For "meaningful size" gaps, fill rates were **40.6% ES, 42.5% NQ, 44.8% RTY, 33.1% gold**. — [Beyond Candlesticks](https://beyondcandlesticks.substack.com/p/who-is-willing-to-trade-in-the-gap)
- NQ, 2,791 days (2015–2025): baseline **60.3%** of gaps fully fill by the close. Tiny gaps 77.8%, small 42.0%, medium 25.6%, large **8.2%**. — [TradingStats](https://tradingstats.net/gap-fill-strategy/)
- Vendor ES/NQ 1-min: gaps of 0.25–0.5% fill 84% same day (48% within first hour). Gaps >1% fill 55% same day (22% first hour). — [TradingView indicator by btcLeft](https://www.tradingview.com/script/32pGGSWx-Gap-Fill-Probability-Statistics-ES-NQ/)
- Multi-market study: large gaps often persist short term and mostly fill within about 10 sessions. **Eight strategy implementations built on gap behaviour produced no statistically reliable edge after costs.** — [MPM Markets](https://mpmmarkets.com/research/gaps-always-fill-myth-futures-markets)

**Prior-day high/low "sweeps" (Edgeful-type statistics):**
- No Edgeful statistic was found that measures *sweep-of-PDH/PDL-then-reverse* on ES/NQ. Related stats: ES takes the prior-day low after NQ has, **68% (6 mo) / 72% (1 yr)**. A critic argues this win rate ignores stop placement and tail risk, so it is not an edge. — [Kieran Duff, "68% isn't an edge"](https://kieranduff.substack.com/p/68-percent-isnt-an-edge)
- Edgeful (marketing posts, 6-month to 1-year lookbacks): inside-day setups reach the prior-day high or low **81–88%** of the time across ES, NQ, TSLA and NVDA. NQ opening inside the prior range tests PDH or PDL about **75%** of the time. ES weekly: broke only the previous week's high 53.85%, only the low 15.38% (6 months, NY session). — [Edgeful inside day](https://www.edgeful.com/blog/posts/inside-day-in-trading-breakout-data); [Edgeful previous day's range](https://www.edgeful.com/blog/posts/previous-days-range-trading-mistake); [Edgeful weekly range](https://www.edgeful.com/blog/posts/previous-weeks-range-tradingview-indicator)
- Outside days (open outside yesterday's range): returned to yesterday's high 81% (bullish) / yesterday's low 62% (bearish), over 6 months on ES. — [Edgeful continuation vs reversal](https://www.edgeful.com/blog/posts/continuation-vs-reversal-trading-reports)
- Judas swing: only descriptive and educational pages were found, with no statistics. — [Young Money Investments](https://youngmoneyinvestments.com/blog/ict-judas-swing-futures-trading-guide)

**Testable definitions offered by practitioners:**
- BuildAlpha frames a sweep as a mechanical rule: a low is taken out and then reclaimed. — [BuildAlpha](https://www.buildalpha.com/backtest-ict-and-smc/)
- Backtrex says 50–100+ trades is the minimum for a reliable expectancy estimate, and sets a viability bar of PF > 1.3 with positive expectancy. It publishes no results of its own. — [Backtrex](https://backtrex.com/en/blog/smart-money-concept-beginners); [Backtrex OB/FVG](https://backtrex.com/en/blog/order-block-fair-value-gap-smc-confluence)

### Inferences
- "Price reaches PDH/PDL 75–88% of the time" is a touch probability. Touches are common because intraday ranges usually overlap the prior day's range. A touch statistic says nothing about the payoff of a trade with a stop and a target.
- Results from the owner's own repo agree with the outside evidence. The CLAUDE.md status records 2,090 TJR setups on 10 tickers, Jun–Oct 2026: 22% wins, −0.011R, PF 0.97. The plan-filtered 208 setups made −0.039R, PF 0.91. The filters did not improve the record, the same pattern StatOasis found.
- Small samples dominate the practitioner record (the Silver Bullet backtest's 3 trades in the window, n=15–31 per-ticker splits in this repo). Any claimed edge below a few hundred trades is noise.

### Gaps
- No rigorous intraday (1–5 min) SPY/ES test of FVG-retrace entries with costs and a random baseline was found.
- No quantified "Judas swing" (opening false move then reversal) study was found.
- Full StatOasis rule definitions and code were not readable (fetch blocked).

## 3. Academic evidence on stop-loss clustering, round numbers and support/resistance

### Takeaway
This is the only part of the ICT story with real academic support. In FX, stop-loss orders cluster just beyond round numbers and take-profit orders cluster at them, and stop-loss execution produces self-reinforcing "price cascades" (Osler). Equities show buy/sell imbalances around round prices (Bhattacharya-Holden-Jacobsen). Statistically detected S/R levels produce more bounces than chance, and repeated bounces increase further bounces (Garzarelli et al.; Chung & Bellotti; Osler 2000). The effects are real but small, short-lived and not shown to survive costs as a standalone strategy.

### Cited Findings
- **Osler, "Stop-loss orders and price cascades in currency markets" (NY Fed Staff Report 150, 2002/2005):** stop-loss orders produce positive-feedback trading and rapid self-reinforcing moves ("price cascades"). The market's response to stop-losses is larger and lasts longer than its response to take-profits, which produce negative feedback. Data: the complete Royal Bank of Scotland order book, Aug 1999–Apr 2000, **9,655 orders, >$55bn** face value in USD/JPY, GBP/USD and EUR/USD. — [NY Fed SR150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf); [Osler draft](https://icmaif.soc.uoc.gr/Year/8conf/docs/Osler-Price%20Cascades-03-03.doc)
- **Osler (2003), "Currency orders and exchange-rate dynamics" (NY Fed Staff Report 125 / J. Finance):** take-profit orders cluster strongly **at** round numbers, which explains trend reversals there. Stop-loss orders cluster **just beyond** round numbers, which explains trends speeding up after a round number is crossed. By value, **9.9% of executed take-profits ended in exactly "00", versus 3.8% of stop-losses and 1% under a uniform distribution.** — [NY Fed SR125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf); [summary via search](https://fedinprint.org/item/fednsr/12305)
- **Osler (2000), "Support for resistance: technical analysis and intraday exchange rates" (FRBNY Economic Policy Review):** tested S/R levels published daily by **six firms, Jan 1996–Mar 1998**, for DEM, JPY and GBP against USD, using 1-minute quotes 9am–4pm NY. Strong evidence that the levels predict intraday trend interruptions. Predictive power varies by firm and currency and lasts at least about 5 business days. — [FRBNY EPR 2000](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf); [RePEc](https://ideas.repec.org/a/fip/fednep/y2000ijulp53-68nv.6no.2.html)
- **Bhattacharya, Holden & Jacobsen (2012), "Penny Wise, Dollar Foolish," Management Science 58(2):413–431:** across **>100 million US stock trades**, there is net buying just below round prices and net selling just above. The effect is strongest at whole dollars and weaker at half-dollars. Buying is much stronger when price *falls to* an integer than when it crosses one. Estimated cost to liquidity demanders is about **$1bn/yr**. — [Management Science](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.1110.1364); [SSRN 1569922](https://papers.ssrn.com/ab_id=1569922); [Holden PDF](https://host.kelley.iu.edu/cholden/Bhattacharya%20Holden%20and%20Jacobsen%20(2012).pdf)
- **Garzarelli, Cristelli, Pompa, Zaccaria & Pietronero (arXiv 1110.5197, Scientific Reports 2014), "Memory effects in stock price dynamics: evidences of technical trading":** built a criterion to detect candidate S/R levels and found that prices **bounce off these levels more often than they cross them**. The authors read this as quantitative evidence of a self-fulfilling prophecy. (Markets, timescales and effect sizes were not visible in the summary. The paper used high-frequency LSE stocks, from memory, unverified.) — [arXiv 1110.5197](https://www.arxiv.org/abs/1110.5197); [LIMS PDF](https://lims.ac.uk/wp-content/uploads/garzarelli2014memory.pdf)
- **Chung & Bellotti (arXiv 2101.07410, 2021), "Evidence and Behaviour of Support and Resistance Levels in Financial Time Series":** a heuristic algorithm finds intraday S/R levels that reverse price trends **statistically significantly**. Levels already bounced off several times attract more bounces, and bounce probability decays over time. The effect is not explained by AR(1) dynamics. — [arXiv 2101.07410](https://web3.arxiv.org/pdf/2101.07410); [RePEc](https://ideas.repec.org/p/arx/papers/2101.07410.html)
- Follow-up: Martyushev et al. (2025) model S/R zones with stochastic and volume-weighted methods and report precision/recall gains of 10–16 percentage points over extremum-based detection. — [WiserPub](https://ojs.wiserpub.com/index.php/CM/article/view/8482)
- Secondary sources (ATAS, LuxAlgo) restate Osler but stretch it, for example claiming stops "sit inside the pool and get swept." Osler documents clustering and cascades, not a deliberate "smart money hunting stops" mechanism. — [ATAS round numbers](https://atas.net/blog/the-magic-of-round-numbers/); [LuxAlgo stop placement](https://www.luxalgo.com/library/concept/stop-placement-vs-liquidity-pools.md)

### Inferences
- Osler's two predictions point in opposite directions. **Reversal AT the level** comes from take-profits. **Acceleration THROUGH the level once crossed** comes from stop cascades. That fits the unverified "sweeps signal continuation" claim at least as well as the ICT reversal story. A naive "sweep then reverse" rule bets against the cascade.
- Academic S/R effects are measured as bounce *probabilities* relative to a null, over short horizons. None of these papers reports a cost-adjusted trading P&L.
- Osler's evidence is FX (2000-era bank order book). Its transfer to modern SPY/ES with HFT market-making is plausible (Bhattacharya et al. found round-number imbalances in US stocks) but has not been shown for the sweep-and-reverse pattern.

### Gaps
- Exact bounce-vs-cross probabilities from Garzarelli and Chung & Bellotti could not be extracted (fetch blocked).
- No academic study was found specifically on prior-day high/low as stop-cluster levels in US index futures or ETFs.

## 4. Intraday mean reversion vs momentum after sweeps of the prior-day high/low in SPY/ES

### Takeaway
No direct study of "sweep PDH/PDL then reverse" in SPY/ES was found. The strongest published intraday evidence on SPY points to **momentum and trend continuation** rather than reversal: the first half-hour predicts the last half-hour (Gao et al., JFE 2018), and breakouts beyond a volatility "noise area" are traded trend-following (Zarattini-Aziz-Barbon 2024). This sits uneasily with reversal-only ICT entries.

### Cited Findings
- **Gao, Han, Li & Zhou (2018), "Market intraday momentum," JFE:** the SPY first half-hour return (from the prior close) predicts the last half-hour return, 1993–2013. The effect is stronger on volatile, high-volume, recession and macro-news days, and holds in 10 other ETFs. The working paper (SPY 1999–2012) reported **R² ≈ 0.02** (0.035 combining the 1st and 12th half-hours). CXO notes those tests ignored frictions. A QuantConnect replication says it stays significant after fees. — [WUSTL profile](https://profiles.wustl.edu/en/publications/market-intraday-momentum/); [CXO Advisory](https://cxoadvisory.com/calendar-effects/first-and-last-half-hours-of-trading-linked); [QuantConnect](https://www.quantconnect.com/learning/articles/investment-strategy-library/intraday-etf-momentum); [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- **Zarattini, Aziz & Barbon (2024), "Beat the Market: An Effective Intraday Momentum Strategy for SPY," SFI WP 24-97:** opens trend-following positions when price leaves a noise boundary that signals an abnormal supply/demand imbalance, with dynamic trailing stops. Reported 2007–early 2024: **1,985% total, 19.6% annualized, Sharpe 1.33, net of commissions and slippage**. Robustness checks cover volatility regimes, day of week and dealer gamma. Placed 4th in the Quantpedia Awards 2025. — [SFI](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy); [Concretum](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/); [FSI-HSG news](https://fsi.unisg.ch/de/newsdetail/news/quantpedia-awards-2025-fsis-barbon-and-team-secure-4th-place-with-intraday-momentum-strategy/)
- Edgeful outside-day stats (a reversion back to the prior range 62–81%) are touch probabilities over 6 months, not a P&L. — [Edgeful](https://www.edgeful.com/blog/posts/continuation-vs-reversal-trading-reports)

### Inferences
- If a sweep of PDH/PDL means anything, the cautious reading of Osler, Gao et al. and Zarattini et al. is that it continues when it breaks with strength and fades only at levels where take-profits concentrate. Testing **both** directions after a sweep is the honest experiment.
- Zarattini et al.'s published returns are the authors' own backtest, and the authors run a commercial research firm (Concretum). They are better documented than ICT claims but still need out-of-sample checks.

### Gaps
- No public dataset or study gives a conditional return after a PDH/PDL sweep-and-reclaim in SPY/ES with a defined stop and target.

## 5. What critics and replicators conclude about ICT/SMC

### Takeaway
Replicators who coded the rules found no edge beyond index drift. The criticism found is mostly informal: win-rate statistics that ignore payoff, vendor marketing, and no falsifiable rules. No formal academic critique of ICT was found.

### Cited Findings
- StatOasis: ICT entries "have some structure; they just don't have enough to beat doing nothing" (0/648 beat buy-and-hold, best t = 1.22). — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
- Critic of Edgeful-style stats: a 68% "probability" is not an edge without payoff and stop analysis. — [Kieran Duff](https://kieranduff.substack.com/p/68-percent-isnt-an-edge)
- Thortradecopier: ICT/SMC have no demonstrated edge as trading rules, and FVG revisits match random levels. — [Thortradecopier](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work)
- Vendors warn their own S/R or pivot tools **repaint** (levels change after first appearing), which inflates backtests. — [TradingView Intraday Auto S/R](https://www.tradingview.com/script/GDIls3JP-Intraday-Auto-Support-Resistance-Levels)
- Anonymous "71% win rate" reviews (arxum.com) and vendor 5,400-gap studies (AlgoTraderPro, crypto 1h) are unverified. — [arxum](https://arxum.com/ict-trading/); [AlgoTraderPro](https://algotraderpro.io/blog/how-to-trade-fvgs-that-hold/)
- A generic "critics say it's oversold" page found by search appears auto-generated and syndicated, so it carries no weight. — [example](https://discourse.weareopen.coop/news/smc-and-ict-in-trading)

### Inferences
- Standard critiques that apply, but were not found in a citable formal source here:
  - **Hindsight labeling.** Which swing is "the" order block, or which sweep "counts," is decided after the outcome is known.
  - **Degrees of freedom.** Multiple timeframes, killzones, bias rules and PD arrays give many forks, so some combination always fits past charts.
  - **Survivorship.** Successful students are showcased.
  - **Unfalsifiability.** A failed setup gets reclassified, for example "it was a breaker, not an OB."
- The replication pattern (raw setups near break-even, filters don't help) matches this repo's own TJR results.

### Gaps
- No r/algotrading threads with posted ICT backtests surfaced in search. No academic paper explicitly critiquing ICT was found.

## 6. Which parts could a bot formalize and test, and with which parameters?

### Takeaway
The pieces with academic grounding are round numbers, stop clustering beyond prior extremes, S/R bounces that strengthen with repeated touches, and intraday momentum. These can all be coded without look-ahead. The ICT-specific labels (OB, FVG, MSS, killzones) can also be coded, but so far tests show no edge beyond baseline. Any test must use a random-entry or random-level null, cost-inclusive P&L in R, and out-of-sample splits.

### Cited Findings (parameters and definitions with a source)
- FVG: three-candle gap (candle1 high < candle3 low for bullish). — [LuxAlgo](https://www.luxalgo.com/library/concept/fair-value-gap/)
- Sweep: trade beyond a prior high or low, then **close back inside** within the same or the next bar ("taken out and reclaimed"). — [LuxAlgo](https://www.luxalgo.com/library/concept/liquidity-sweep/); [BuildAlpha](https://www.buildalpha.com/backtest-ict-and-smc/)
- Round-number zones: whole dollars are strongest and half dollars weaker. Take-profit clustering sits **at** the round number, stop clustering **just beyond** it. — [Bhattacharya et al.](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.1110.1364); [Osler SR125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf)
- S/R strength rises with the number of prior bounces and decays with time. — [Chung & Bellotti](https://ideas.repec.org/p/arx/papers/2101.07410.html)
- Intraday momentum: first-30-min return as a predictor of the last 30 min; noise-boundary breakout with a trailing stop. — [Gao et al.](https://profiles.wustl.edu/en/publications/market-intraday-momentum/); [Zarattini et al.](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)
- Sample size: at least 50–100 trades for expectancy (practitioner rule of thumb). Judge on PF and expectancy, not win rate. — [Backtrex](https://backtrex.com/en/blog/smart-money-concept-beginners)
- Null: compare against a seeded coin flip, buy-and-hold, and random levels. — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives); [Thortradecopier](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work)

### Inferences (suggested bot experiments for this repo)
1. **Sweep direction test.** At PDH/PDL and the overnight high/low on SPY/QQQ 1-min, define a sweep as a print ≥ k ticks beyond the level (k ∈ {1, 0.05×ATR}) and a close back inside within N ∈ {1, 3, 5} bars. Score **both** fade and continuation at fixed R (stop beyond the sweep extreme, targets 1R/2R, 60–120 min time stop). Compare against the same rule at random levels of matched distance. This tests the Osler and unnamed-preprint "continuation" claim directly.
2. **Round-number fade vs breakout.** Use SPY whole-dollar and $5 levels. Test fades on first touch and breakouts after a close beyond, following Osler's two predictions, and condition on whether price arrives falling or rising (Bhattacharya et al.'s path dependence).
3. **Touch-count S/R.** Weight levels by prior bounce count with time decay (Chung & Bellotti) instead of ICT's discretionary OB selection.
4. **Momentum baseline.** Implement the Gao et al. first/last half-hour signal and the Zarattini noise-band breakout as **control strategies**. If an ICT variant can't beat them after costs on the same days, drop it.
5. **FVG baseline.** Before using FVGs as entries, measure FVG revisit rates against random-level revisit rates at the same distance and horizon. If the rates are equal (as in the blog simulation), FVG zones carry no information.
- In every test, report trades, win%, avg R, PF, max drawdown and t-stat of mean R. Use walk-forward or out-of-sample periods and do not cherry-pick tickers. This repo's TJR record (PF 0.91–0.97 on n ≈ 200–2,000) suggests looking for a structural change (direction, level type), not more filters.

### Gaps
- No published parameter set for ICT entries has shown out-of-sample profitability after costs, so none can be recommended as evidence-backed.
- Option-specific costs (0DTE spreads, theta) are not covered by any of the cited studies. The underlying-level edge would also have to exceed the option friction.
