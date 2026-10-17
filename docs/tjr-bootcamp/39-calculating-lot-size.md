# Day 39: Calculating Lot Size (position sizing)
Source: https://www.youtube.com/watch?v=KSiWKfPOlh4 (15 min). Read in full from the transcript the owner pasted.
Recorded on the 4th of July: a bank holiday, so he made the video and took the day off.

## Three ways to size
1. **A set lot size** (what he uses, as a range of set sizes; see below).
2. **Calculate the size for every trade.**
3. **"Full port"** (everything in), which you never do.

## Calculating it each time
- Inputs: **account balance, risk % (1%), and the stop distance** (pips for Forex; points for the S&P). A calculator
  turns these into the lot size. He uses the app *Stinu* for Forex and gold, and a website calculator that includes
  the S&P. Not sponsors.
  - Example: a $1,000 account at 1% risk with a 30-pip stop gives about 0.03 lots ($10 at risk). Round to two
    decimals.
- **Finding the stop in pips:** the position tool on the chart shows it as you drag the stop.
- **Contract size per lot:** check your broker's instrument details (MetaTrader: Details, then "contract size"). On the
  S&P his broker uses **10 units per lot**. Most offshore brokers use 100, and many prop firms 10. Check every new
  account, because the wrong contract size wrecks the sizing. (That's why "100 lots" on his screen isn't what people
  think.)

## His set lot size
- Work out your **usual minimum stop** for the instrument: on the S&P, about **4 points** (400 "pips" in the
  calculator), usually 4–7 points. Size so that **this minimum stop risks 1%**: about 25 lots on a $100k example.
- Then keep that size. If a trade needs a wider stop, risk scales up with it: an 8-point stop is about 2%, and 12
  points about 3%. In practice it rarely reaches 3%.
- **The set size differs per instrument** (volatility and volume). Trade only one instrument while learning.

## His three risk levels (built on the set size)
| Level | Size | When |
|---|---|---|
| **Normal** | the set size (about 1%) | a day with no news, or news that won't move the market much |
| **De-risk** | **50% of normal** | high-impact news days (traded only after the release), bank holidays, or anything he expects to mess up the market. He used it the day before the 4th of July. |
| **Confident** | **2× normal** | no news, he loves the setup, all biases in line |

- **"You guys should never use the confident size."** It's for traders with proof of profitability. Beginners use
  normal or de-risk only.

## For the bots
- **Sizing for the TJR models** (`sizing.mode: risk`, `exits.measure: structure`): contracts are calculated so that
  hitting the chart stop loses about `sizing.risk` dollars. This is TJR's "calculate it every time" method, using the
  stop distance on the underlying × the option delta × the multiplier.
  - At the $30k sim account, 1% is $300.
  - Options are whole contracts, so the real risk is rounded down (never up), and a stop too wide for even one
    contract within budget means no trade.
- **De-risk:** half size on high-impact news days that aren't full blackouts, on the day before a market holiday, and on
  half days. A config list `news.derisk_days`, with half size applied by the sizer.
- **Confident (2×): not used by the bots.** TJR says it requires proven profitability, and the bots have none: every
  corrected backtest so far is negative.
- **Full port: never.** The existing caps already prevent it (max premium exposure, max open positions, daily loss
  limit).
