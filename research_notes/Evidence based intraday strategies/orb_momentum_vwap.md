# Evidence-based intraday strategies for US stocks/ETFs: ORB, intraday momentum, VWAP trend

Research date: 2026-10-20. Method note: the proxy for this session blocked SSRN, Concretum, QuantConnect, CXO Advisory,
MQL5 and the University of St. Gallen PDF server, so the primary PDFs could not be opened directly. Figures below come
from web-search extracts of those pages and from GitHub replications that could be fetched. Where a figure appears only
in a secondary summary, it is flagged. Anything a bot implements should be checked against the original PDF first.

## Q1. Zarattini & Aziz (2023), "Can Day Trading Really Be Profitable?" (QQQ 5-minute ORB, SSRN 4416622)

### Takeaway
Rules are simple and fully specified; headline results (about 31-33% CAGR, Sharpe about 1.1, max DD about 22%, 2016 to
Feb 2023) assume zero slippage. An independent replication matches the paper gross but finds the edge disappears at
about 2.2 cents/share of entry slippage, and about 75% of trades end at the stop. No out-of-sample period exists in the paper.

### Cited Findings
- Paper: SSRN 4416622, April 2023, Zarattini (Concretum) and Aziz (Bear Bull Traders); tests a 5-minute ORB on QQQ, long or short based on the direction of the first 5-minute bar. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622); [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)
- Exact rules as replicated: QQQ 5-min bars, Jan 2016 to Feb 2023, $25,000 start. First bar 09:30-09:35 ET. Bullish bar: long at the 09:35 open, stop at that bar's low. Bearish bar: short, stop at bar's high. Doji: no trade. Exits: stop (-1R), target +10R, or flat at the session close. Size = min(1% of equity / R per share, 4 x equity / entry price) (4x day-trading leverage cap). — [giovannibrusco replication, GitHub](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- Cost assumptions: $25,000 start, max 4x leverage, $0.0005/share commission, no bid-ask spread, no slippage. The paper is quoted: "we assumed no slippage in fills". — [search extract of CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy/); [GitHub replication](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- Paper vs replication: trades 1,795 vs 1,775; Sharpe 1.12 vs 1.06; max drawdown 22% vs 22%; CAGR 31-33% vs 30.4%; final equity $192,806 vs about $164k. — [GitHub replication](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- Paper reportedly states about 675% total return in 7 years net of commissions on QQQ (consistent with $25k to about $192.8k); a TQQQ version reports 1,484% for 2016-2023 vs 169% for buy-and-hold QQQ. — [Concretum page via search](https://concretumgroup.com/can-day-trading-really-be-profitable/); [The Robust Trader summary](https://therobusttrader.com/can-day-trading-really-be-profitable-rules-backtest-statistics-performance-analysis/)
- Per-trade stats (secondary): 24% hit rate, about +0.13R per trade, about 33%/yr with 4x leverage. — [MQL5 replication blog (search extract), Sep 2026](https://www.mql5.com/en/blogs/post/776235)
- Exit mix in replication: about 75% of trades stop out, about 22% flat at close, +10R target hit only about 2-3% of the time. — [GitHub replication](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- Cost sensitivity: net PnL $138,639 at 0 slippage, $4,860 at 2c/share; zero at about 2.2c/share entry slippage (stop slippage 2x). QQQ spread is about 1c. — [GitHub replication](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- Regime concentration: an NQ pre-open confirmation filter was significant per trade (t=2.05) but 76% of its PnL is from 2022; bootstrap 95% Sharpe CIs overlap buy-and-hold (filter [0.05, 1.41] vs B&H [-0.03, 1.47]); a sharp 2023 drawdown hints at decay; an ES futures run Mar-Sep 2026 found no edge before costs. — [GitHub replication](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- Replication on index CFDs (NQ, SPX, Dow, DAX, FTSE): gross edge reproduced on NQ (+0.131R), but no market distinguishable from zero after costs; notes the paper has no out-of-sample period. — [MQL5 blog (search extract)](https://www.mql5.com/en/blogs/post/776235)
- A separate QQQ ORB study (15-min OR, 2R target, entry on 5-min close beyond OR, 12:00 cutoff, exit 15:00) after a 120-config sweep on 2017-2022: out-of-sample Jan 2023-Sep 2026 pre-cost 928 trades, 46.7% wins, +0.070R avg, PF 1.156, max DD 25.5R; per year +20.8R (2023), +18.9R (2024), +35.3R (2025), -7.7R (2026 to Sep). At $0.04 round-trip cost, avg R +0.054 and bootstrap 95% CI includes zero. — [mericck QQQ ORB, GitHub](https://github.com/mericck/QQQ-Opening-Range-Breakout)
- Note: a "Sharpe 2.4" figure that circulates belongs to the QuantConnect Stocks-in-Play recreation (Q2), not to the QQQ paper. — [QuantConnect research 18444](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)

### Inferences
- The QQQ ORB edge is thin per trade (about 0.1R gross) with a 24% hit rate; with a 1c-wide market, realistic stop-order slippage consumes most of it. A bot should model stop fills at worse than the stop price.
- The +10R target is almost decorative; the strategy is in practice "stop or hold to close". For 0DTE options this is a problem: options decay into the close, so the hold-to-close leg (where the profits come from) does not translate directly to option premium.
- Results are concentrated in high-volatility years (2022). Expect long flat/losing stretches.

### Gaps
- Could not open the PDF to confirm the paper's own hit rate, profit factor, and exact Sharpe/drawdown table (the 1.12/22% are as reported by the replicator).
- No peer-reviewed post-publication (2023-2026) test of the exact QQQ rule found.

## Q2. Zarattini, Barbon & Aziz (2024), "A Profitable Day Trading Strategy For The U.S. Equity Market" (Stocks in Play ORB, SSRN 4729284)

### Takeaway
Top-20 "Stocks in Play" (highest opening relative volume) 5-min ORB with an ATR-based stop reports >1,600% net, Sharpe
2.81, 36% annual alpha over 2016-2023 with commission-only costs. A QuantConnect recreation got Sharpe about 2.4 on a
smaller universe. No independent post-2023 test of the filtered version was found, and the cost model omits spread/slippage
on small, volatile, gapping names where those costs are largest.

### Cited Findings
- Paper: SSRN 4729284, first circulated Feb 2024 (revised Nov 2024); >7,000 US stocks, 2016-2023; adds a "Stocks in Play" relative-volume filter; compares 5/15/30/60-minute ranges and finds 5-minute best. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284); [ResearchGate](https://www.researchgate.net/publication/379003745_A_Profitable_Day_Trading_Strategy_For_The_US_Equity_Market)
- Rules (secondary summary): universe = open > $5, 14-day average volume >= 1,000,000 shares, ATR(14) > $0.50; rank by opening-range relative volume (first 5-min volume vs the average of the same window over the prior 14 days), keep top 20 with relative volume >= 100%; direction from the first 5-min candle; stop-order entry at the opening-range high (long) or low (short); stop = 10% of ATR(14) from entry; exit at close if not stopped; risk 1% of capital per trade, 4x leverage cap. — [CXO Advisory summary (search extract)](https://www.cxoadvisory.com/individual-investing/intraday-trading-of-overactive-stocks-via-opening-range-breakout/); relative-volume definition from [QuantConnect research 18444](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
- Results: top-20 portfolio total net return over 1,600% (1,637% in secondary write-ups; 41.6% annualized IRR), Sharpe 2.81, annualized alpha 36%, vs S&P 500 about 198%. — [Concretum page (search extract)](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/); [Tradoki blog](https://blog.tradoki.com/posts/opening-range-breakout-stocks-in-play-research)
- Max drawdown 12% (filtered) vs 13% (base ORB) vs 34% (S&P 500): from a secondary table, unverified against the paper. — [Tradoki blog (search extract)](https://blog.tradoki.com/posts/opening-range-breakout-stocks-in-play-research)
- Costs: $25,000 starting NAV, $0.0035/share commission; cost model is commission-only; no clearly separated out-of-sample period. — [Tradoki](https://blog.tradoki.com/posts/opening-range-breakout-stocks-in-play-research); [danfin.net review (search extract)](https://danfin.net/opening-range-breakout-research)
- QuantConnect recreation: 1,000 most liquid US equities > $5 with ATR > $0.50, otherwise the authors' parameters: Sharpe about 2.4, beta near zero. — [QuantConnect research 18444](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)

### Inferences
- This is the strongest headline in the set, but also the most exposed to unmodelled costs: a stop 10% of ATR away (for a $0.50 ATR stock that is 5c) means a 1-2c spread plus slippage is a large fraction of 1R. A tight-stop, stop-order-entry rule on gapping news stocks is the textbook case where backtests overstate fills.
- Not directly usable for 0DTE options: most Stocks in Play do not have daily expiries, and option spreads on them are wide.

### Gaps
- Could not confirm the stop rule (10% ATR) and the per-timeframe results table from the paper itself.
- No independent post-2023 out-of-sample result for the top-20 filtered version was found.

## Q3. Zarattini, Aziz & Barbon (2024), "Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)"

### Takeaway
Noise-area breakout checked at :00/:30, VWAP-based trailing stop, volatility-targeted leverage (cap 4x). Paper: 1,985%
net, 19.6%/yr, Sharpe 1.33, max DD 25%, 2007 to early 2024. Independent replications get Sharpe about 1.0-1.1 in-sample,
about 0.72-0.75 out of sample 2022-2026 (roughly equal to buy-and-hold SPY at the same volatility), one reports near-zero
Sharpe since 2025, and break-even extra slippage is only about 2 bps per trade.

### Cited Findings
- Paper: Swiss Finance Institute Research Paper 24-97 (version dated Feb 3, 2025); tests on SPY, checks day-of-week and daily patterns, includes commissions and slippage. — [IDEAS/RePEc](https://ideas.repec.org/p/chf/rpseri/rp2497.html); [Concretum](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)
- Noise area: for each time-of-day t, sigma_t = average over the previous 14 days of |close_t / open - 1|. Upper band = max(Open, prior Close) x (1 + sigma_t); lower band = min(Open, prior Close) x (1 - sigma_t) (the max/min of open and prior close is the gap adjustment). Volatility multiplier 1. — [svettelnova replication, GitHub](https://github.com/svettelnova/intraday-momentum-spy); [TradingView Concretum Bands description](https://it.tradingview.com/script/CUpWCZhe-Concretum-Bands)
- Entry: check only at HH:00 and HH:30 from 10:00 to 15:30; long if price above upper band (and above VWAP in some implementations), short if below lower band; fill at the close of the bar ending at the check time; all positions closed at 16:00, nothing overnight. — [svettelnova](https://github.com/svettelnova/intraday-momentum-spy); [nikolaosntinas18 replication](https://github.com/nikolaosntinas18/spy-intraday-momentum)
- Stop: trailing stop = max(VWAP, upper band) for longs, min(VWAP, lower band) for shorts. — [Concretum/search extract](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)
- Sizing: leverage = min(4, 0.02 / sigma_SPY), where sigma_SPY is the std dev of the last 14 daily returns (target 2% daily vol); average leverage about 2.66. — [svettelnova](https://github.com/svettelnova/intraday-momentum-spy); [nikolaosntinas18](https://github.com/nikolaosntinas18/spy-intraday-momentum)
- Costs: $0.0035/share commission + $0.001/share slippage. A QuantConnect forum thread notes fills use bar-close trade prices, ignoring bid/ask, and suggests $0.005/share as more conservative. — [svettelnova](https://github.com/svettelnova/intraday-momentum-spy); [QuantConnect forum 17091](https://www.quantconnect.com/forum/discussion/17091/beat-the-market-an-effective-intraday-momentum-strategy-for-s-amp-p500-etf-spy/)
- Paper results: 1,985% total net, 19.6% annualized, Sharpe 1.33, max DD 25% (2007 to early 2024) vs SPY 227%, about 7.2%/yr, vol 20.2%, Sharpe 0.45. A commentary notes the tighter (VWAP) stop raised Sharpe 0.61 -> 1.24 and vol targeting only to 1.33; the big total return comes from leverage. — [Concretum substack/search extract](https://concretumgroup.substack.com/p/beat-the-market-with-intraday-momentum)
- Replication (nikolaosntinas18): vol-sized train 2016-2021 16.0%/yr, vol 14.9%, Sharpe 1.07; test 2022-Sep 2026 10.3%/yr, vol 14.6%, Sharpe 0.75; SPY B&H 0.98 train, 0.67 test. Unlevered base: 0.72 test. Sharpe uncertainty about +/-0.4-0.5; test Sharpe ranged 0.55-1.19 across design variants; VWAP condition helped in both periods. Conclusion: roughly keeps pace with B&H SPY at similar vol, does not clearly beat it. — [GitHub](https://github.com/nikolaosntinas18/spy-intraday-momentum)
- Replication (codecat-ops, search extract only, repo page 404 when fetched): full-sample Sharpe 1.11 matching trade-level behavior, but "edge compressed since 2025, recent Sharpe about 0 on both instruments (SPY, ES)" and "walk-forward destroys value". — [search result: codecat-ops/zarattini-2024-momentum-spy](https://github.com/codecat-ops/zarattini-2024-momentum-spy)
- Cost analysis (francesco-nicolo, 58 backtests of blackswan-quants variants on SPY, 8 years): Sharpe about 0.84-1.08 at 0 bps extra slippage (spread included); break-even at about 2.1-2.4 bps extra slippage per trade; strategy return 196-271% vs leveraged B&H about 350%, but DD 9% vs 40% and beta -0.05. Deflated Sharpe still distinguishable from zero across 16 configs. QuantConnect's PSR definition changed (about 41 points lower now). — [GitHub](https://github.com/francesco-nicolo/intraday-momentum-replication)

### Inferences
- The strategy's value is mostly diversification (near-zero beta, low DD), not alpha over SPY on a vol-matched basis.
- The only post-2024 evidence found (one repo) suggests it has stopped working since 2025; treat as unproven.
- For 0DTE options it is a better fit than ORB in one respect (frequent decisions on SPY, which has daily expiries), but the 2 bps break-even means option spreads (often several % of premium) would almost certainly swamp it.

### Gaps
- Exact paper tables (hit rate, profit factor, per-year returns) not seen directly.
- Post-publication (June 2024 onward) out-of-sample Sharpe is reported only by unreviewed GitHub projects.

## Q4. Gao, Han, Li & Zhou (2018, JFE 129, 394-414), "Market Intraday Momentum"

### Takeaway
On SPY 1993-2013 the first half-hour return (measured from the prior close) predicts the last half-hour return with
R^2 about 1.6% (higher on volatile, high-volume, news and recession days). The paper's sample ends in 2013; one
practitioner study on 1,085 SPX sessions in the 0DTE era finds the unconditional effect gone, and the related Concretum
replications also show decay. Evidence of persistence after publication is weak.

### Cited Findings
- First half-hour return (since prior day's close) predicts the last half-hour return on SPY 1993-2013; stronger on volatile, high-volume, recession and macro-news days; R^2 1.6%, rising to 3.3% with the 12th half-hour return when first-half-hour volatility is high; holds out of sample in their tests. Timing strategy: take the sign of r1 (optionally combined with r12) and hold SPY over the last half hour. — [SSRN 2440866](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351)
- Global evidence: significant first-to-last half-hour predictability in 12 of 16 markets. — [Univ. of Reading, Li et al.](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf)
- Extensions: also found in US sector/EM ETFs and commodity futures. — [ResearchGate (search extract)](https://www.researchgate.net/publication/325364670_Market_Intraday_Momentum)
- Post-2014 check (practitioner, non-peer-reviewed, SPX not SPY): 1,085 sessions of the 0DTE era, unconditional effect flat overall and in each year. — [DEV Community / firmtape](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0)

### Inferences
- With R^2 about 1.6% and one trade per day of 30 minutes, the economic edge is small and costs matter a lot. Do not trade it without a fresh test on 2014-2026 data with costs.

### Gaps
- Exact strategy Sharpe/returns from the JFE paper not retrieved.
- No peer-reviewed study of the SPY effect on 2014-2026 data found.

## Q5. Zarattini & Aziz (2023), "VWAP: The Holy Grail for Day Trading Systems" (QQQ/TQQQ, SSRN 4631351)

### Takeaway
Long when price is above VWAP, short when below, on QQQ 1-minute bars, Jan 2018-Sep 2023: 671% net of commissions, Sharpe
2.1, max DD 9.4% (TQQQ 8,242%). The paper assumed no slippage; an independent reproduction says the edge per trade is
smaller than one tick of slippage.

### Cited Findings
- Results: $25,000 -> $192,656 (671%) net of commissions, max DD 9.4%, Sharpe 2.1 vs QQQ B&H 126%, DD 37%, Sharpe 0.7; TQQQ version 8,242% total (116%/yr). Period Jan 2, 2018 to Sep 28, 2023. — [SSRN 4631351 (search extract)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4631351); [Concretum](https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/)
- Assumptions: "Since we initiated our system with a small account of only $25,000, we assumed no slippage in our order fills." — [Telonics Trading review](https://telonicstrading.com/research-vwap.html)
- Reproduction on 6 years of 1-minute data: edge smaller than a single tick once one tick of slippage added. — [Telonics Trading](https://telonicstrading.com/research-vwap.html)
- Blog test over 8 years: about 77% of profit from 35% of the period; full-period Sharpe 0.76 vs paper 2.1 (unverified blog). — [Medium, techacademies](https://medium.com/@techacademies/i-tested-the-holy-grail-vwap-strategy-on-8-years-of-data-it-worked-for-three-of-them-601d1d61b535)

### Inferences
- The VWAP-cross rule trades very often (every cross on 1-min bars), so per-trade costs dominate; it is a cost-sensitivity trap rather than a robust edge. The final-equity figure ($192,656) is near-identical to the QQQ ORB paper's ($192,806), which may be coincidence; worth checking in the PDFs.

### Gaps
- Exact rule details (bar size confirmation, trade count, hit rate, commission per share) not retrieved from the paper.

## Q6. Independent replications/critiques, out-of-sample and cost sensitivity

### Takeaway
Every replication found reproduces the gross numbers roughly, and every one finds the edge highly cost-sensitive (break-even
about 2c/share for QQQ ORB, about 2 bps for SPY momentum, under one tick for VWAP). Out-of-sample (2022/2023-2026)
results are weaker than the papers and several show decay in 2025-2026.

### Cited Findings
- QQQ ORB: break-even about 2.2c/share; edge concentrated in 2022. — [giovannibrusco](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- ORB on 5 index CFDs: gross reproduced, net zero everywhere. — [MQL5 blog](https://www.mql5.com/en/blogs/post/776235)
- QQQ 15-min ORB out of sample 2023-Sep 2026: PF about 1.15 pre-cost, CI includes zero after $0.04 costs, negative in 2026. — [mericck](https://github.com/mericck/QQQ-Opening-Range-Breakout)
- SPY intraday momentum: OOS Sharpe 0.72-0.75 (2022-2026); recent Sharpe about 0 since 2025 (one repo); break-even about 2 bps. — [nikolaosntinas18](https://github.com/nikolaosntinas18/spy-intraday-momentum); [codecat-ops (search extract)](https://github.com/codecat-ops/zarattini-2024-momentum-spy); [francesco-nicolo](https://github.com/francesco-nicolo/intraday-momentum-replication)
- QuantConnect caveat: Sharpe and drawdown computed on end-of-day values ignore intraday volatility. — [QuantConnect forum 17091 (search extract)](https://www.quantconnect.com/forum/discussion/17091/beat-the-market-an-effective-intraday-momentum-strategy-for-s-amp-p500-etf-spy/)
- Earlier academic ORB: Holmberg, Lönnbark & Lundström (2013, Finance Research Letters 10(1):27-33) test ORB success rate/profitability on futures; Lundström's follow-up finds ORB returns depend heavily on the volatility state (about 150 bp/day difference between highest and lowest vol states for S&P 500 futures). — [IDEAS](https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html); [SWoPEc](https://swopec.hhs.se/umnees/abs/umnees0974.htm)

### Inferences
- Common pattern: authors (Concretum, with a commercial interest via Bear Bull Traders) assume no or minimal slippage; independent work with costs and post-publication data finds Sharpe roughly halved or gone. Treat paper Sharpe ratios as upper bounds.
- All three strategies trade the underlying with stops; none was tested on 0DTE options. Converting them to options adds spread, theta and gamma effects the papers do not model.

### Gaps
- Quantitativo, Robot Wealth and the QuantConnect forum threads could not be opened; no specific numbers from them are included.

## Q7. Prior-day high/low breakouts, gap fills, first-hour reversals

### Takeaway
No rigorous published backtest of prior-day high/low breakouts or first-hour reversals on SPY/QQQ was found. Gap-fill
statistics exist from practitioner sites and show small gaps fill often, large gaps rarely, and fill rates fell after 2013.

### Cited Findings
- SPY 1993 onward: up gaps of 0.1-0.25% fill same day about 78%; 1-2% gaps about 26%; 1%+ gaps fill under a third. — [Kai Yasuda, "Gap-Fill Teardown"](https://kaiyasuda.substack.com/p/the-gap-fill-teardown)
- 0.25%+ up gaps filled same day 58.1% in 2001-2013 vs 43.1% in 2014-2026; less often when prior close above 200-day average. — [Trade That Swing](https://tradethatswing.com/sp-500-spy-es-gap-fill-strategy-and-statistics/)
- Rolling 6-month SPY gap stats swing widely (59%/69% up/down fills in Mar 2026 vs 50%/46% in Oct 2026). — [thetrading.tools](https://www.thetrading.tools/gap-analysis)
- A fill-rate statistic is not a strategy return: fill probability does not account for the loss when a gap does not fill. QuantifiedStrategies' early gap-long backtest (2010-2012, 98 of 110 winners) dropped to 89 fills when tested intraday; author warns backtests are only indicative. — [QuantifiedStrategies](https://www.quantifiedstrategies.com/gap-trading-strategies/)

### Inferences
- Gap-fill, prior-day-level and first-hour reversal ideas are practitioner statistics, not peer-reviewed strategies with costs; a bot would need to test them itself on minute data with realistic costs.

### Gaps
- No published, cost-inclusive backtest of prior-day high/low breakouts or first-hour reversals on SPY/QQQ found.
