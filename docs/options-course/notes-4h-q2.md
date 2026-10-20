# Options Trading For Beginners (4-hour course), second quarter: study notes

Source: "Options Trading For Beginners (Complete 4 Hour Course)", Sky View Trading,
https://www.youtube.com/watch?v=u847cbKEWu0. These notes cover the second quarter of the transcript
(auto-captions, file `7-part-01`, 270 lines): the end of the volatility chapter, **Option Greeks**,
**Long options (buying calls and puts)**, and the start of **Short options (selling calls and puts)**.
The quarter ends mid-sentence in the GDX short put example; the rest continues in the next part.

Caption fixes applied: captions drop decimal points and cents, so "delta of 65" is 0.65 ($65 per
contract), "264" is $2.64, "12191" is $121.91, "12464"/"12462" is $124.62, "$9935" is $99.35,
"$7263" is $72.63. "ThinkersW"/"Thinker Swim" = thinkorswim; "TDM Trade"/"TDMIR trade" = TD
Ameritrade; "S&P"/"SPX" = the S&P 500 index (SPX). Places where the spoken number itself looks
wrong are marked "(note: ...)".

---

## 1. Wrap-up of the volatility chapter (lines 1-5)

- Options are a more complex product: more affects their price than buyers and sellers of the stock.
  The instructor calls this "a huge advantage" and "the reason we trade options in the first place".
- Claim: time decay and volatility can "add massive consistency and profitability" that a strategy
  only predicting direction cannot.
- Claim: "90% of traders lose money", and those are the ones focused on predicting the next big move.
  Recommendation: learn "strategies that will pay you even when you're wrong about market direction".
  "It isn't about being right. It's about making money."
- Recap: option prices are driven daily by three factors: underlying stock price, time to expiration,
  implied volatility (IV) of the underlying.

## 2. Option Greeks (lines 5-66)

Purpose: Greeks measure an option price's **sensitivity** to each of the three factors (stock price,
time, IV). They answer: if the stock rises one point, how much does my call make; if 5 days pass,
how much do I lose to decay; if IV drops 10%, how much does the price change. They help **choose
strikes and expirations** and **understand risk**.

Four main Greeks: delta, gamma, theta, vega. On thinkorswim: option chain, Layout, "Delta, Gamma,
Theta, Vega".

### Delta
- Definition: how much the option's price changes if the underlying rises **one point ($1)**.
- Example: delta 0.65 means the option rises $0.65 if the stock rises $1.
- Calls have positive delta; puts have negative delta (a stock rise lowers put value).
- Real example (TLT chain): 123-strike call, delta 0.47. Stock +$1 means the option +$0.47, so one
  contract makes **$47**.
- Delta is not fixed; it changes as the stock moves, by the amount of gamma.
- The further **in the money**, the bigger the delta; further **out of the money**, the smaller.
  "Delta will grow bigger as an option gets more and more valuable."

### Gamma
- Definition: how much **delta** changes if the stock rises one point.
- Example: same option, gamma 0.05: stock +$1 moves delta from 0.47 to 0.52.
- Instructor: "We actually don't even look at gamma much when making trading decisions." Just know
  delta keeps changing.
- Delta and gamma together describe sensitivity to the stock price.

### Theta
- Definition: how much the option's price changes if **one day passes**.
- Example: theta -0.12 means the option loses $0.12 per day from time decay.
- It is ceteris paribus: the option will be $0.12 lower tomorrow only if the stock price and IV do not
  change; all three factors act every day.
- All long options have negative theta: "Time value is constantly being sucked out of all options. So
  any time you buy an option contract, you are going to be fighting this time decay."

### Vega
- Definition: how much the option's price changes if the underlying's **IV rises 1 percentage point**.
- Example: vega 0.10 means IV +1% raises the option price by $0.10.
- Vega is positive on all options, calls and puts: higher IV makes all options more expensive.

### Summary definitions (as the instructor restates them)
- Delta: price change per +1 point in the stock.
- Gamma: delta change per +1 point in the stock.
- Theta: price change per day passing.
- Vega: price change per +1 percentage point of IV.

### Position Greeks (example: SPX iron condor, 10 contracts)
- Greeks can be summed over a whole position. Example position: an iron condor on SPX (strategy taught
  later), currently up **$425**.
- **Position delta -8.98**: SPX +1 point means the P&L changes by -$8.98 (up ~$416 instead of $425);
  SPX -1 point means +$8.98.
- Sign of position delta = direction: **negative = short the market** (wants it down), **positive =
  long** (wants it up).
- Size of position delta = directional exposure; check it fits your risk tolerance. With 100 contracts
  instead of 10, delta would be "around -80" (note: 10x of -8.98 is about -90; the instructor rounds
  loosely), so SPX +1 would lose ~$80. "Delta is a good way to measure risk ... not the only way."
- -8.98 is "almost insignificant", which is the nature of the iron condor: it earns from time decay and
  volatility and removes stock direction "as much as possible since predicting stock prices is very
  difficult."
- Is a delta big or small? Subjective; depends on risk tolerance and account size. Rule of thumb:
  **position delta = equivalent number of shares** long or short. -8.98 is like short ~8 shares of SPX
  (index not directly tradable, but the idea holds). Long 50 shares = delta +50; delta -10 = short 10
  shares.
- **Position gamma**: if SPX +1, delta goes from -8.98 to -10.57. "Don't get too hung up on gamma."
- **Position theta positive** (+$72.63/day): the position *benefits* from time decay. "All the
  strategies we use here at Sky View Trading benefit from time decay. Making sure you are on the right
  side of time decay is extremely important."
- **Position vega -176.78**: each +1 point of IV loses $176; each -1 point gains $176.

## 3. Long options: buying a call (lines 67-162)

### Why buy a call
- You think the stock will go up soon; the call makes the bullish bet "for much cheaper" than buying
  stock, so a much higher return on capital (leverage).

### Leverage demonstration: TLT, 31 days to expiration
- Stock $121.91, rounded to $122. Mark price = midpoint between bid and ask.
- Call marks: 121 strike $2.64, 122 strike $2.10, 123 strike $1.68, and so on.
- Scenario: stock 122 -> 130.
  - Stock: +$8/share / $122 = **6.6%** return.
  - 121 call: worth intrinsic value $9.00 at 130; bought 2.64, sold 9.00 = +$6.36 per share
    ($636 per contract); 6.36 / 2.64 = **240.9%**.
  - 125 call: **over 400%**: 1 contract $97 -> $500; 10 contracts $970 -> $5,000; 100 contracts
    $9,700 -> $50,000 "in just 31 days".
- Lesson 1: options give leverage: big profits with little capital.
- Lesson 2 (strike selection): cheaper OTM options gave bigger percentage returns; pricier ITM
  options gave smaller ones.

### The trade-off: probability of profit (POP) and break-even
- The further OTM, the lower the **probability of profit (POP)**.
- **Break-even** = stock price needed at expiration to at least break even.
  - Stock bought at 122: break-even 122.
  - **Long call break-even = strike + price paid.** 121 call: 121 + 2.64 = **123.64**.
- Further OTM strikes (bigger % return) had worse break-evens; a big required move means a poor POP.
  "The larger potential payout is accompanied by a poor probability of profit."
- Strike rule: further OTM = larger potential payout, very low POP; further ITM = smaller payout,
  higher POP.
- Warning: the big payout "suckers the little guy into buying out of the money options". Buying cheap
  OTM options is called a **"lottery trade"**: "the lowest probability option strategy that exists",
  "very little consistency".

### Walkthrough: buying a call on Facebook (thinkorswim)
- Premise: bullish, and IV is low and may rise.
- **Expiration choice** (compared 4 DTE vs 60 DTE):
  - 4 DTE: theta much higher (decay hurts more) but gamma also much higher ("you can make faster
    profits if things go in your favor"). High theta means "much less room for error if we don't time
    the entry perfectly".
  - Picked a "happy medium": **25 DTE**.
- **Strike choice**: deeper ITM costs more, smaller return, but less time decay to fight (more intrinsic,
  less extrinsic value). OTM is cheaper, bigger potential return, poor POP. Picked the **at-the-money
  122 strike**.
- Order: right-click option, "Buy single"; can set price and number of contracts. 1 contract at **$2.62**.
- Cost: $262 + $1 commission = **$263** total.
- **Risk of a long option = cost of the trade**: the option cannot go below zero. The broker's
  displayed max loss ($262) excludes commissions; real max loss is $263. Max loss/profit shown in the
  confirmation box do not include commissions.
- **Buying power effect (BPE)** = capital requirement; for a long option it is the cost, $263.
- Max profit shown "infinite"; instructor prefers **"undefined"** (no stock goes to infinity).
- Break-even 122 + 2.62 = **124.62**: above it at expiration you profit, below it you lose.

### Risk profile (P&L graph)
- x-axis: stock price; y-axis: profit/loss. Blue line = P&L at expiration (ignore the purple line,
  which is P&L today).
- Example: stock at 130 at expiration means profit just over $500 (130 - 122 - 2.62 = $5.38/share).
- Flat at max loss -$262 anywhere below the 122 strike; rises without cap above it. Where the blue line
  crosses zero is the break-even.

### Finding POP on thinkorswim (Analyze tab)
1. Right-click the order, "Analyze trade".
2. Probability mode at the top set to **ITM**.
3. Only this trade's box checked at the bottom.
4. Date at the top right = the option's expiration (here 16 Dec 2016); ignore the other date shown.
5. Button right of the plus sign: "Set slices", "Break even", click the (blue) expiration date.
- Result: probability above break-even **34.57%** = POP; probability of loss **65.43%**.
- "This poor probability of profit that you see is the exact reason we prefer not to buy options."
- Claim: "When buying an option, you will never have a probability of profit better than 50%."

### Long call recap
- Bullish. Time decay works against you, so you want a **fast** move. Benefits from rising IV.
- Max profit undefined; max loss = premium paid; break-even = strike + premium.
- Not recommended by the instructor ("we feel there are much better ways to trade options"). If you
  do: deeper ITM = better POP; further OTM = better potential % return.

## 4. Long options: buying a put (lines 163-169)

- Same as a long call but **bearish**: profit as the stock falls.
- Time decay still against you; still hoping for an IV increase.
- Risk profile reversed: more profit the lower the stock goes; if the stock is above the strike (put
  OTM) at expiration, you lose the whole premium.
- **Long put break-even = strike - price paid.** Below it you make money; above it you lose.

## 5. Expiration handling for long options (lines 169-186)

- If your long call or put is **in the money at expiration, close it before it expires** (sell it).
  Otherwise it is exercised into stock: ITM call -> long 100 shares; ITM put -> short 100 shares.
- Most traders avoid this: the stock position needs much more capital, and there is an **exercise fee**
  (varies by broker; $15 at TD Ameritrade in the video).
- "Especially as a new option trader, just close all your option trades before expiration."
- If you want the stock, two equivalent ways:
  1. Hold the ITM option through expiration and get assigned the stock.
  2. Sell the option and buy the stock at market.
- Example: XYZ at $130, you own the 120 call bought at $4.
  - Exercise: own stock at 120, up $10/share, minus $4 paid = **+6 points**.
  - Sell the call at its $10 intrinsic value (bought 4, +6 points) and buy stock at 130 (break-even on
    stock) = **+6 points**.
  - "The pricing is always going to be fair", so choose by fees: exercise $15 vs. $1.50 to sell the
    option + $7.95 to buy 100 shares (Sky View Trading Group commission rate). Know your own rates.
- OTM options at expiration: no need to close; they expire worthless and disappear (you lose the
  premium). Only ITM options turn into stock.

## 6. Short options: selling (lines 186-270, continues into the next part)

### Concept
- Sky View Trading's stated favorite: selling an option as an **opening** trade, hoping its price falls.
  Sell to open high, buy to close low.
- Put option definition (review): the right, not the obligation, to sell shares at the strike price on
  or before the expiration date. The seller sells that right, takes on the buyer's risk, and is paid
  for it; obligated to buy shares at the strike if exercised.
- Selling a put is like **providing insurance**: the seller hopes the stock does not crash; it wants
  the stock to stay **above the strike**.
- Selling a call: wants the stock to stay **below the strike**.
- Short put = **bullish to neutral**; short call = **bearish to neutral**.
- "Rather than betting where the stock will go, we are betting where the stock won't go, which is
  extremely powerful."

### Example: short 125 call on Facebook (stock just above $117, 46 DTE)
- Bet: stock won't go above 125 in about a month. All OTM options expire worthless.
- Sold 1 contract at **$1.02** = **$102** collected (note: the caption says "$12"; with the 100
  multiplier 1.02 is $102).
- Scenario 1: stock at $122 (or anywhere below 125) at expiration: option worthless, keep the full
  premium. **Max profit = premium received.**
- Scenario 2: stock at $128: option worth intrinsic $3.00; loss "298" per the caption (note: 3.00 -
  1.02 = 1.98, i.e. $198 per contract; the spoken/captioned figure looks wrong).
- Theoretical risk is **unlimited** for a short call (the stock has no upper cap).
- Instructor's argument: in exchange for taking risk and capping profit, you get "a very high
  probability of profit". Buying options (limited risk, unlimited profit) "looks too good to be true",
  which is "why we consider buying options to be a sucker's bet".
- Claim: "We believe that the theoretical risk is much higher than the actual risk. I've built my
  entire career off of this concept."
- Warning: "any trading strategy is dangerous if you are overleveraged and are sizing your positions
  too big" (position sizing promised for part two).
- Recommendation for a **first trade**: not a naked short option (undefined risk is hard for beginners
  to judge), and not a long option ("simply is not proven to be profitable over time"). Their favorite
  first trade is the **vertical spread** (sell options for high POP but with limited risk), next chapter.
- Long and short single options are "the building block of all other strategies".

### Live trade 1: short call on Caterpillar (CAT), stock just above $95
- Preferred expiration for this strategy: **30 to 60 DTE** (a January expiration with 39 DTE "is
  perfect"). For the demo they used the December expiration with **11 DTE** so the full cycle can be
  shown quickly.
- **Delta ~ probability in the money (ITM) at expiration.** The chain shows delta and "probability ITM"
  side by side and they are very similar. Example: 100-strike call, delta 0.12 -> ~12% chance CAT is
  above 100 in 11 days, so ~88% chance it is below. Platforms without a probability column: use delta.
- Probability OTM = 1 - probability ITM; the chain column can be switched to probability OTM (easier
  for new traders).
- Selling: further OTM = lower probability ITM = higher POP, but a cheaper option = smaller max profit.
  Example: selling the 101 call has very high POP but only **$15** per contract of profit potential,
  before commissions. Closer to the money = more profit potential, lower POP. "There really is no magic
  number when it comes to strike selection"; find a balance.
- Chosen: **99-strike call, ~84% probability OTM**. Right-click bid/ask, "Sell single". When selling,
  aim to be filled at the highest price ("buy low, sell high"): limit **$0.35**.
- Confirmation: **short call break-even = strike + premium = 99.35**; stay below it. Max profit $35
  (premium). Max loss shown "infinite"; instructor says "undefined".
- **Buying power effect for a short option is set by the broker** (its best guess at real risk): just
  over **$1,500** here. "Always check this number before selling an option." They consider it high,
  mostly because of the short time to expiration, "one of the reasons we usually choose to place our
  trades with somewhere between 30 and 60 days".
- Filled at $0.35 with CAT ~$95; best case CAT stays below 99 and they keep $35.

### Live trade 2 (starts): short put on GDX (gold miners ETF)
- Short put = bet the stock stays above the strike until expiration.
- Same rules: further OTM strike = higher POP, smaller profit potential.
- Chosen: **20-strike put** with "around a 67% chance of being out of the" money (the transcript part
  ends here).

---

## Rules a bot could use

These are rules taken from the video, with how a bot could check them. Scalp City *buys* 0DTE options;
several of these rules argue against that, and the notes say so rather than hide it.

1. **Delta as a P&L estimate per contract.** Expected option change per $1 underlying move = delta;
   per contract = delta x multiplier. Source: "if the stock goes up by one point, you should make $47"
   (delta 0.47). Check: option P&L projections and the `exits.measure`/`sizing: risk` logic should use
   `delta x underlying move x contract.multiplier`.
2. **Delta as a probability proxy.** |delta| ~ probability the option finishes ITM. Source: "delta can
   actually tell us the probability of our option being in the money at the expiration date" (0.12
   delta = ~12%). Check: log |delta| of each bought contract as its rough ITM probability.
3. **Long-option POP is below break-even probability, not 50/50.** Long call profits only above
   strike + premium; long put only below strike - premium. Source: "add the price you pay for the
   option to the strike price"; "subtracting your entry price from the strike price". Check: a bot can
   compute the break-even and the distance the underlying must travel before expiry; for 0DTE that
   move must happen the same day.
4. **Instructor's POP figure for an ATM 25-DTE long call: 34.57%.** Source: "your probability of profit
   is 34.57%". Claim: "When buying an option, you will never have a probability of profit better than
   50%." A bot should not expect a buy-only strategy to win more than about half its trades at
   expiration; any edge must come from payoff size or early exits.
5. **Avoid lottery tickets: far-OTM buys have the lowest POP.** Source: "buying cheap out-of-the-money
   options as a lottery trade ... the lowest probability option strategy that exists". Check: reject
   bought contracts below a minimum |delta| (the video gives no number; it picks ATM as the
   "happy medium").
6. **Strike for buying: ATM as the compromise; deeper ITM = higher POP and less time decay.** Source:
   "let's just meet in the middle and buy the at the money option"; "buying a further in the money will
   mean that you won't be fighting time decay as much". Check: contract selector targets |delta| near
   0.5 or higher, not lower.
7. **Short DTE = high theta and high gamma: less room for error.** Source: "the much higher theta means
   we are losing more money to time decay. So we would have much less room for error if we don't time
   the entry perfectly." The video's buy example used **25 DTE**, not 4. Check: for 0DTE buys, require
   a fast move after entry (time stop) since decay is fastest. (The video gives no time-stop number.)
8. **Long options need a fast move and benefit from rising IV.** Source: "we'd really be hoping for a
   fast move of the stock so time decay doesn't hurt us too much. And we'd also benefit from an
   increase in implied volatility." Check: prefer entries when IV is low and may rise (the FB example
   premise: "we also think that implied volatility is low"); avoid buying when IV is likely to drop
   (vega is positive on every long option).
9. **Theta/vega accounting.** Position P&L per day of decay = position theta; per IV point = position
   vega. Source: "theta is the amount by which an option's price will change if one day passes";
   "if implied volatility goes up by 1%. Then the options price will increase by" vega. Check: dashboard
   could show position delta, theta and vega for each open position.
10. **Position delta = share-equivalent exposure; keep it within risk tolerance.** Source: "Your delta
    basically tells you the equivalent number of shares you are long or short"; "make sure that that
    number is in line with our risk tolerance". Check: cap total |position delta x underlying price| per
    account.
11. **Max loss of a long option = premium + commissions; broker's max-loss number omits commissions.**
    Source: "we will actually lose $263, not the $262 that is displayed". Check: risk sizing should add
    `costs.fees()` to premium when computing per-trade risk.
12. **Close ITM options before expiration.** Source: "if your call or put option that you own is in the
    money, then you're definitely going to want to close the option position before it expires"; "just
    close all your option trades before expiration". Check: flatten time must fire before the close on
    expiry day (Scalp City already flattens; keep it). Avoid the exercise fee ($15 at TD Ameritrade).
13. **Price with the mark (mid) and use limit orders; sell at the highest price you can, buy low.**
    Source: "the mark price ... is simply just the mid price between the bid and the ask"; "we want this
    order to get filled at the highest price possible". Check: limit orders near mid, not market orders.
14. **Check buying power effect before selling (not applicable to buy-only bots).** Source: "Always check
    this number before selling an option". Scalp City does not sell options; noted for completeness.
15. **Selling preferences (for reference only; Scalp City does not sell):** 30-60 DTE ("we like to trade
    this strategy with 30 to 60 days to expiration"); strike by probability OTM (example 84% and 67%);
    vertical spreads preferred over naked short options for limited risk.
16. **Position sizing: avoid over-leverage.** Source: "any trading strategy is dangerous if you are
    overleveraged and are sizing your positions too big". No numbers given in this part (promised in
    part two).

Not in this part of the video (so no rule): liquidity/open interest/volume/bid-ask spread thresholds,
IV rank or IV percentile, specific profit-taking or stop-loss percentages, earnings/IV crush.

## Claims to verify

- "90% of traders lose money." No source given.
- Time decay and volatility strategies "add massive consistency and profitability ... that you just
  simply cannot find" in directional trading. Opinion/marketing; no data shown.
- "All the strategies we use here at Sky View Trading benefit from time decay." Statement about their
  own practice, not evidence that it works.
- "When buying an option, you will never have a probability of profit better than 50%." (note: under
  the platform's model this is approximately true because break-even sits beyond the current price by
  the premium paid, but it is a model-based probability at expiration, not a guarantee, and does not
  account for closing early.)
- Delta ~ probability of finishing ITM. (note: this is an approximation; the video itself shows the two
  columns as "very similar", not equal.)
- Buying options is "a sucker's bet" and "simply is not proven to be profitable over time". Opinion; no
  backtest or statistics shown.
- Short options: "the theoretical risk is much higher than the actual risk. I've built my entire career
  off of this concept." Opinion and personal anecdote; tail risk on naked short calls is real.
- Selling options gives "a very high probability of profit". POP figures shown (84%, 67%) are the
  platform's model probabilities, not realized results; high POP does not mean positive expectancy.
- Vertical spreads as the best first trade: preference, not shown with results.
- TLT example returns (240.9%, over 400% on the 125 call, $9,700 -> $50,000 in 31 days) are a
  hypothetical 122 -> 130 move chosen for illustration, not an actual trade.
- Short call loss "298" at stock 128 conflicts with the arithmetic (3.00 - 1.02 = 1.98, $198); and the
  "$12" premium is a caption error for $102.
- 100-contract iron condor delta "around -80": 10x of -8.98 is about -90.
- Fees quoted ($1 commission, $1.50 per option, $7.95 per 100 shares, $15 exercise) are the video's
  broker and their group rate at the time, not current market rates.
