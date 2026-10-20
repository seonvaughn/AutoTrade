# 15-minute opening range: breakout, retest, reversal
Source: https://www.youtube.com/watch?v=bITIVwysCzM (about 15 min). Read in full from the transcript the owner pasted
on 2026-10-20. The presenter shows a $65k P&L for one month (June 15 – July 15). That's a screenshot, not a tested
record, and the video gives no win rate, sample size or costs.

## Claims made in the video (his words, not evidence)
- "Simple, mechanical, repeatable", "sets up every single day", and needs **no daily bias** and no indicators.
- He trades it within the first 2 hours after the New York open.

## The setup
- **Why the first candle matters:** big ranges are hard to trade, so he focuses on the first candle of the new session.
  Its high and low are the **opening range**: "the opening range of a new market session has a lot of liquidity."
- **Session:** New York, opening at 09:30 ET, because it has the most volatility and liquidity. London and Asia work too,
  but New York is his go-to.
- **Opening range timeframe:** 1m, 5m or 15m. Anything above 15m makes the range too big. **Beginners: use the 15m**
  ("the most liquidity", and it uses every timeframe together, "the highest probability").

## The three steps
1. **Mark the high and low of the first 15-minute candle** of the NY session (09:30–09:45 ET).
2. **Wait for a 5-minute candle to close** above the 15m range high (longs) or below the range low (shorts).
3. **Go to the 1-minute chart and look for a continuation entry** in the direction of the break.

## The three entry models (on the 1-minute chart, after the 5m close beyond the range)
1. **Breakout (opening range break):**
   - Price breaks out with **displacement**, shown by a **bullish gap** (a fair value gap) on the 1m. "Whenever price
     leaves behind a bullish gap, this is a strong signal that price is going to continue."
   - **Entry:** on the close of the candle that completes the gap.
   - **Stop:** "at the break below your second candle that formed the gap", i.e. below the low of the middle
     (displacement) candle of the three-candle gap. Mirrored for shorts.
   - **Target:** a **fixed 1:2 risk:reward**.
   - Use it when the move is strong and might not come back for a retest (e.g. a higher-timeframe draw above).
2. **Retest (his personal favourite, used consistently):**
   - After the break, price comes back to the range edge (the 15m high for longs), holds it, and buyers step in.
   - **Entry:** on the retest holding with "strong price action".
   - **Stop:** at the **break of structure low** (the 1m swing low that held).
   - **Target:** fixed 1:2.
   - Use it when there's **no bullish gap** on the break.
3. **Reversal (mean reversion):**
   - The breakout fails: price breaks back through the range to the other side.
   - Common on **range days**, especially on the major indices when the higher timeframes have no clear trend.
   - **Entry:** wait for a **break of structure back** with displacement (price closes above the last lower high).
     Mark the **order block** (that candle's high down to its body), and enter long on the retrace into it with a
     confirmation candle.
   - **Stop:** just below the order block / swing low.
   - **Target:** back to the **high of day**.
   - He prefers continuation; reversals for indices and forex.

## His examples
| Ticker | Context | Model | Result |
|---|---|---|---|
| TSLA | Above the previous day's high ("fairly bullish") | 5m close above the 15m high, 1m bullish gap, long on the gap candle's close, stop below the middle candle, 1:2 | Hit the target |
| NVDA | Break above the 15m high but no bullish gap | Retest: price held the range high, buyers stepped in; stop at the 1m BOS low, 1:2 | Worked |
| QQQ | Price went from the top of the range to the bottom: "most likely a range day", so no continuation trades | Reversal: break back above a lower high with displacement, order block, confirmation candle, long, stop below the swing low | Took a while but hit the high of day |

## For the bots
- **This is a close relative of the opening-range breakout studied in the research report**
  (docs/research/evidence-based-intraday-strategies.md):
  - In its own paper, the QQQ 5-minute ORB showed about +0.13R per trade at a 24% win rate (2016–2023), with the
    stop at the other side of the range and a 10R target.
  - Independent replications found the edge disappears at about 2 cents per share of slippage.
  - The 15-minute version with a 1:2 target and retest entries is not in the papers. It has to be tested, not trusted.
- **Implemented as triggers in `sig_orb15` (bots/orb_bots.py):**
  - `orb15_breakout` (model 1), `orb15_retest` (model 2) and `orb15_reversal` (model 3, simplified).
  - All use the 15m range from 09:30–09:45, need a 5m close beyond it, enter on the 1m, and carry a stop and a 1:2
    target. They pass through the same research gate, morning study and lessons book as everything else.
- **Tested on the same discovery/holdout split** before any tower trades them (docs/research-log.md).
- **What can't be coded exactly:**
  - "Strong price action" and "buyers stepping in" on the retest are coded as a 1m candle closing back in the trade
    direction after touching the level, then a 1m break of structure.
  - "Range day" is coded as both range edges being taken before 11:00.
