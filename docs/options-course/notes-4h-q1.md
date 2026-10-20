# Options Trading For Beginners (4-hour course): first quarter

Source: "Options Trading For Beginners (Complete 4 Hour Course)",
https://www.youtube.com/watch?v=u847cbKEWu0. These notes cover the first quarter of the auto-caption transcript
(chapters 1 to 3: what options are, the option chain, the three pricing factors, and a worked scenario with all
three factors together). Caption errors are fixed where the meaning is clear: prices the captions wrote without
decimal points ("228", "1809") are written as $2.28 and $18.09, and "Thinker Swim / TDMatrade" is written as
thinkorswim / TD Ameritrade. Corrections and context that are not the instructor's are marked "(note: ...)".

The instructors trade on thinkorswim (TD Ameritrade). The examples use 2016 prices (Apple, Twitter, EWZ, FXI).

---

## 1. What an option is

- **Option:** a contract you can buy that gives you the right to buy or sell stock at an agreed price on or before a
  particular date. You can also **sell** an option contract: you sell that right to someone and collect a
  **premium** for it.
- **Two types:**
  - **Call:** the holder has the right, *but not the obligation*, to **buy** shares at an agreed price on or before
    a particular date.
  - **Put:** the holder has the right, but not the obligation, to **sell** shares at an agreed price on or before a
    particular date.
- **Strike price** = the agreed price. **Expiration date** = the particular date.
- Plain-terms examples:
  - Long 120-strike call, 30 days to expiry: you can buy the stock at 120 at any time in the next 30 days, wherever
    the stock goes. If the stock rises to 135, you can still buy at 120.
  - Long 120-strike put, 30 days: you can sell the stock at 120 at any time in the next 30 days. If the stock falls
    to $100, you can still sell at 120.
  - (note: "any time on or before" describes American-style options, which is what US stock and ETF options such as
    SPY, QQQ and AAPL are. Cash-settled index options such as SPX are European-style and can be exercised only at
    expiration. The course does not draw this distinction here.)

## 2. Why options exist: insurance (buying a put)

- Analogy: you buy a Ferrari and insure it with Progressive. An option works the same way.
- **Example:** an investor buys 100 shares of XYZ at $125, which costs $12,500. A stock can go to zero, so the total
  risk is technically $12,500. To insure the position, the investor **buys a put** (the right to sell at an agreed
  price).
- **Who sells it?** Any trader willing to be paid to take on your risk, like an insurance company. The investor pays
  to hand off risk, and the seller is paid to take it on.
- Price paid (assumed for the example): **$500** for a put (125 strike) that gives full coverage for 30 days. The
  factors that set this price are covered in chapter 3.
  - **Scenario 1, stock rises $125 → $132:** +$7/share × 100 = **+$700** on the stock, less the $500 put, which now
    has no value to you = **net +$200**. The buyer feels ripped off. The seller says "thanks for the easy money" and
    keeps the $500.
  - **Scenario 2, stock falls to $113:** −$12/share × 100 = **−$1,200** on the stock. You exercise the put and sell
    at 125, so the stock costs you nothing. Your only loss is the **$500** premium, much better than −$1,200.
    - The seller was obligated to buy your shares at 125. They keep the $500 but sit on a $1,200 loss on the stock.
      They can hold and hope it recovers, or sell at 113 for a **net loss of $700** (1,200 − 500).
- Summary: buying a put is like buying insurance on a stock investment, and selling a put is like selling insurance.
- You **don't need to own stock** to trade options. You can trade the fluctuating option prices in a brokerage
  account just as you trade stock. The insurance framing matters because it explains how options are priced
  (chapter 3).

## 3. Why buy a call: leverage with less capital

- Use case: you like a stock but it is expensive. Instead of buying shares, you pay a small premium for the right to
  buy shares later if you are right and the price rises.
- **Example:** XYZ at $125. 100 shares cost $12,500. Instead, buy the **125-strike call with 30 days** to expiry for
  an assumed **$500**.
  - **Scenario 1, stock goes 125 → 137:** you **exercise** the call (use your right to buy at the lower price), so
    you own 100 shares at 125 and are up 12 points = **+$1,200**, less the $500 premium = **net +$700**. Buying the
    stock outright would have made more. True.
  - **Scenario 2, stock falls to $100:** you would never buy at 125 when the market price is 100, and you don't have
    to (right, not obligation). You lose only the **$500** premium. Had you bought the stock at 125 you would be
    down **$2,500**.
- **Benefit of buying an option over stock:** much less capital, so much less risk, but you pay a premium for it.
- **Buying a put without owning stock** is a bet that the stock goes down. (If you exercised a right to sell stock
  you don't own, you would end up with a short stock position.)
- **Rule:** buy a call = bet the stock goes up. Buy a put = bet the stock goes down.
- **Warning:** "before you go out and start buying calls on every stock you think is going to go up and puts on
  every stock you think is going to go down, keep watching because there are **big negatives to buying options like
  this**." The course promises "much better ways to trade options."
- You don't have to exercise. You can buy an option and later **sell the option**, hopefully at a higher price.

(Sponsor break: the presenters work with traders "on a case-by-case basis" on automating and scaling trading; a link
is in the video description.)

## 4. The option chain (chapter 2)

- Option contracts are electronic. You can buy or sell one in milliseconds through a broker, like a stock.
- **Option chain:** the list of every option you can trade, with prices. It is available on your trading platform
  and on Google Finance, Yahoo Finance and similar sites. The instructors use thinkorswim (TD Ameritrade) and call it
  their favorite. (note: TD Ameritrade has since been absorbed into Charles Schwab, which still offers
  thinkorswim.)
- Type the ticker to see the chain. Most popular companies have options. If a stock has none, the platform says
  "this instrument has no options." Demo ticker: **AAPL**.
- **Reading the chain:**
  1. **Pick an expiration.** Each expiration shows its date and, in parentheses, the days left. Example: the
     18 Nov 2016 expiration showed **(36)**, meaning 36 days away. Which expiration to trade is covered later in the
     course ("there are pros and cons").
  2. **Calls on the left, puts on the right.**
  3. **Strikes run down the middle in ascending order**: higher strikes sit *lower* on the screen. The instructor
     finds this counterintuitive and says you get used to it.
  4. **Pick a strike.** Example: the 120-strike call, 36 days. Which strike to trade is covered later.
- **Bid / ask:** like stocks, options have a bid and an ask. **You buy at the ask** (where the sellers are) and
  **sell at the bid** (where the market will buy from you).
- **Contracts and the 100 multiplier:** stocks trade in shares, options in **contracts**. **One contract controls
  100 shares.** The right to buy 100 shares takes 1 contract. 200 shares takes 2 contracts.
  - Example: 120-strike call quoted **bid 2.28 / ask 2.33**. Buying costs the ask, **2.33 × 100 = $233 per
    contract**. Trick: drop the decimal point (2.33 → $233).
- **Trading the option itself (not the stock):** option prices move every day, like stock prices.
  - Buy 1 contract at 2.33 ($233). Over about a week the option rises to 3.00. Sell to close at 3.00 ($300) for a
    profit of **$67**.
  - Buy 2 contracts: 2 × $233 = **$466**. Sell both at 3.00 = $600, for a profit of **$134**.
- You must constantly decide when to sell: hold and hope for more, or take the profit.
- **Three factors move an option's price** (preview): (1) the underlying stock's price, (2) time to expiration,
  (3) volatility. On the first: a call typically gains value when the stock rises, and a put gains when it falls.
  The other two are "extremely important. So, don't go buying options yet."
- Chapter recap: the option chain lists the options and their quotes. Options have a bid and an ask. One contract =
  100 shares, hence the ×100 multiplier.

## 5. Factor 1: the underlying stock's price (chapter 3)

- Think of option prices as insurance on a stock investment. That is the best way to understand how they're
  priced.
- **The three factors that set an option's price:** (1) the price of the underlying stock, (2) time to expiration,
  (3) the volatility of the underlying stock.
- **Strike choice is like coverage level.** Twitter, 28 days to expiry; you own 100 shares bought at $18.
  - The **18-strike put** is "full coverage": it lets you sell at $18 however far the stock falls. It costs about
    **1.59 ($159 per contract)**.
  - The **16-strike put** costs about **$75**. It is cheaper because it insures only $16/share of the investment,
    not the full $18.
- **In the money (ITM):** you own the 120-strike call on XYZ (no stock) and XYZ is at 125. The option is worth **at
  least $5**, because exercising gives an immediate $5/share gain. It lets you buy at a discount to the market.
- **Out of the money (OTM):** the same 120 call with XYZ at 115, assuming no time left: the option is **worthless**,
  because nobody exercises a right to buy at 120 when the market price is 115.
- **Definitions:**
  - ITM call: strike **below** the stock price. OTM call: strike **above** the stock price.
  - Puts are the exact opposite (ITM put: strike above the stock price. OTM put: strike below).
  - On thinkorswim, ITM options have a bluish background and OTM options an empty or black one.
- **The deeper ITM an option is, the more it costs**, because it lets you buy at a bigger discount.
- **Direction rule (repeated as important):** a rising stock price raises its calls' value (they move further ITM).
  A falling stock price raises its puts' value.
- **Value at expiration = intrinsic value** = how far ITM it is (the difference between the stock price and the
  strike). OTM options expire worthless.
- **Expiring-today Twitter example (essentially no time left), stock at $18.09:**
  - 17-strike call quoted about **1.05 × 1.14**, so worth about **1.09**, the $1.09 discount to the stock price.
  - 16-strike call worth about **2.09** ($2.09 discount). The screen showed 2.15 because it is deep ITM and the
    **bid/ask spread is wide**.
  - Every OTM call and put on that expiry was worthless.
- Recap: at expiration, ITM options are worth the difference between strike and stock price, and every OTM option
  is worthless. Options that are *not* about to expire have value even when OTM, which leads to factor 2.

## 6. Factor 2: time to expiration

- Insurance is not a one-time payment. You pay month after month, and longer cover costs more.
- Example: 6 months of car insurance might cost $600 and 12 months $1,200. Likewise **an option with 60 days to
  expiration costs more than the same option with 30 days.**
- **Why OTM options have value before expiry:** stock prices move, and while time remains an OTM option may still
  become ITM. Like car insurance, you don't know in advance whether it will pay off.
  - Twitter options with **0 days** left (they expire after the close that evening): OTM options are at 0.
  - The same strikes with **28 days** left: OTM options still have value.
- **The further OTM, the cheaper,** because it is less likely to end up worth anything. Example: the stock is more
  likely to reach $20 in 28 days than $25, which needs an extremely large move, so the 25-strike call is cheap.
- **Intrinsic vs. extrinsic value:**
  - **Intrinsic value** = the in-the-money portion of the price.
  - **Extrinsic value** = the amount by which the price exceeds intrinsic value. It is also called **time value**.
  - At expiration there is no extrinsic value left.
- **Worked example (Twitter, 28 days, stock at $18.09):** the 17-strike call costs **2.20**.
  - It is $1.09 ITM, so **intrinsic = 1.09** and **extrinsic = 2.20 − 1.09 = 1.11**.
  - If Twitter trades **sideways for 28 days**, the option decays from 2.20 to 1.09. Bought at $220 and worth $109:
    a **loss of $111 even though the stock didn't move.**
  - **Break-even at expiration = strike + premium = 17 + 2.20 = $19.20.** From $18.09, the stock must rise to
    $19.20 just to break even.
- **Key warning:** options cost much less than shares, but **time decay works against the buyer.** The stock must
  move your way, and by a significant amount, just to break even. "Options are constantly decaying as time passes."
- **The instructors' stance:** "This is exactly why we don't trade options in this way. **We never buy options as a
  way to guess direction** of the underlying stock. We actually trade them in a way to take advantage of this time
  decay" (strategies come later in the course).
- **Clarification:** the decay is gradual. If you buy today and Twitter jumps to $19.20 **tomorrow** ("pretty
  unlikely"), you would have a decent profit, because time value remains. $19.20 is the break-even **at
  expiration** only. You can open and close at any time before expiry.
- Section recap:
  - Options have expiration dates for the same reason car insurance is paid monthly.
  - You don't have to hold to expiration: you can sell at any time at the current market price.
  - More time = more money (60 DTE costs more than 30 DTE).
  - Intrinsic = the ITM portion. Extrinsic (time value) = the rest. An option about to expire has no time value and
    is worth only its intrinsic value.
  - Option prices always decay with time, so **a buyer is always fighting decay.** The instructor recommends
    finishing the course before your first trade, to learn strategies that profit from decay ("extremely
    powerful").

## 7. Factor 3: volatility (implied volatility)

- The instructor says most option traders learn only the first two factors, ignore volatility, "and then they wonder
  why they can't figure out how to make any money trading options." Volatility is "equally as important as the
  other two factors, if not more important."
- **Volatility** = the magnitude of a stock's price swings. High volatility = large swings. Low volatility = small
  swings.
- For a stock investor, volatility measures risk: bigger swings mean bigger possible losses. **More risk, so more
  expensive options.** The option seller demands more for taking on more risk.
- Analogy: life insurance for an overweight smoker with a serious medical condition versus a healthy person who
  exercises. The risky one pays far more. High-volatility stock = expensive options. Low-volatility stock = cheap
  options.
- **Real example (28 days to expiry; the two underlyings were only 6 cents apart in price):**
  - **EWZ** implied volatility (expected move) over 28 days: **±$2.44**. **FXI**: **±$1.89**. So EWZ is expected
    to move more.
  - The **37-strike put**: EWZ about **0.85**, FXI about **0.54**.
  - Calls and puts at **every** strike were more expensive on EWZ.
  - Same underlying price and same time to expiry, but different IV, so different prices. **High IV = expensive
    options. Low IV = cheap options.**
- **IV changes over time.** IV up makes both calls and puts more expensive. IV down makes both cheaper.
- **IV comes from option prices**, not the reverse: the market prices of the options "spit out" the IV number, which
  is the market's expected move.
- **What moves IV:** supply and demand for options. Many option buyers push prices (and IV) up. Many sellers push
  them down.
- **What drives demand:** fear of the unknown. Scared investors buy options to protect their portfolios, which
  raises prices and IV. **"Implied volatility is kind of like a fear gauge for the market."**
- Practical takeaway: IV rising = options getting more expensive. IV falling = options getting cheaper.
- **The instructor's claim:** "a huge part of our trading strategy because **implied volatility is actually very
  predictable whereas stock prices aren't that predictable**." The course covers how to predict IV in part two.
- **Finding IV on thinkorswim:** daily chart → Studies → Edit studies → search "ImpVolatility" → double-click to add.
  It shows current IV against its history. Example reading: **0.455 = 45.5% expected volatility, annualized** ("over
  the next year"). What matters is whether the number rises (options get pricier) or falls (options get cheaper).

## 8. All three factors together (Theo tool scenarios)

- Setup: Twitter, 28 days to expiry, **19-strike call** (bullish bet) bought at **1.28 = $128** per contract.
  thinkorswim's "Theo" tool estimates option prices under changed stock price, date and IV.
- **One factor at a time:**

| Scenario | Stock | Time | IV | Option price | P/L |
|---|---|---|---|---|---|
| Only time passes, to expiry | flat | to 0 DTE | flat | decays to 0 | **−$128** (all of it) |
| Stock +1 instantly | +1.00 | none | flat | 1.79 | +$51 |
| Stock +2 instantly | +2.00 | none | flat | 2.38 | **+$110** |
| IV jumps "by 25%" | flat | none | +25% | 1.79 | **+$51** |

  - Why the option gained $110 when the stock rose $2: explained later in the Greeks chapter.
  - (note: the captions say IV "jumps up by 25%" and later "goes down by 10%". They don't say whether these are
    percentage points of IV or a relative change.)
- **Combined scenarios** ("there will rarely ever be a time when only one of these factors changes"):

| Scenario | Stock | Time passed | IV | Option price | P/L | Lesson |
|---|---|---|---|---|---|---|
| A | +1.50 | 1 week | flat | 1.84 | **+$56** | A fast move beats decay |
| B | +1.50 | 3 weeks | flat | 1.23 | **−$5** | The right move, too slow: decay ate it |
| C | +0.50 | 1 week | −10% | 1.12 | **−$16** | The IV drop plus a little decay outweighed the favorable move |
| D | flat | a little over 3 weeks (4 days left) | +25% | 0.53 | **−$75** | Decay outweighed a huge IV spike |

- In most scenarios the buyer **lost money even though the stock moved their way.** The instructors repeat that
  buying options is "our least favorite way to trade options. In fact, we don't ever trade options in this way."
- "There are two sides to every trade and you can take either side." All three factors change constantly and all
  affect the price. (The transcript part ends mid-sentence: "So options are a little bit more of a gray area...")

---

## Rules a bot could use

Each rule cites the transcript. Lines tagged *(mapping)* relate the rule to Scalp City and are not the instructor's
words.

**Pricing and fills**
1. **Contract cost = quoted price × 100 per contract** (stocks/ETFs). "one option contract controls 100 shares ...
   option prices will have a multiplier of 100." Example: 2.33 → $233. *(mapping: already `contract.multiplier`.
   Never hard-code ×100.)*
2. **Buys fill at the ask, sells at the bid.** "If you want to buy ... at the ask price ... sell it at the bid
   price." A backtest that fills at mid or last overstates results. *(mapping: the sim's fills should cross the
   spread.)*
3. **Wide spreads on deep ITM strikes distort the quoted price.** The 16 call showed 2.15 against about 2.09 fair
   "because it's so deep in the money and the bid ask spread is kind of wide." A checkable rule: compute
   (ask − bid) / mid and skip contracts above a threshold. The instructor gives no number.
4. **Check that the ticker has options** ("this instrument has no options") before trading.

**Value and break-even**
5. **Intrinsic = max(0, S − K) for calls, max(0, K − S) for puts. Extrinsic = price − intrinsic.** "Extrinsic value
   refers to the amount by which an option's price is greater than the intrinsic value." Log the extrinsic paid at
   entry: it is what decays away.
6. **Break-even at expiration for a long call = strike + premium (put: strike − premium).** "17 + 2.20 ... 19.20."
   Possible entry filter: require the expected move (target) to clear break-even plus costs.
7. **OTM options expire worthless.** At expiry an option is worth its intrinsic value only ("all out of the money
   options will be worthless"). *(mapping: a 0DTE OTM contract held to the close goes to 0. The flatten time
   matters.)*

**Time decay (factor 2)**
8. **A long option loses value if nothing happens.** Sideways for 28 days turned the 2.20 call into 1.09 (−$111)
   "and the stock didn't even move."
9. **Speed matters more than direction alone (time stop).** The same +$1.50 move made +$56 in 1 week but lost $5 over
   3 weeks: "it took too much time to go up." Checkable: exit a long option if the expected move hasn't happened
   within N bars or minutes. The instructor gives no N.
10. **The further OTM, the cheaper and the less likely to pay** ("the likelihood of it being of any value is less").
    Cheap OTM strikes need large moves.

**Implied volatility (factor 3)**
11. **IV falls → calls and puts both lose value**, even when the stock moves your way: +$0.50 with IV −10% in a week
    = −$16. Rule: avoid buying when IV is likely to fall. Earnings or other known events, after which IV usually
    drops, are not discussed in this quarter (note: this IV-crush rule is an inference, not stated here).
12. **High IV = expensive options. Compare IV, not just price.** EWZ's 37 put cost 0.85 against FXI's 0.54 at the
    same price and DTE. Checkable: record IV at entry and compare it with the ticker's own IV history ("where
    implied volatility is now versus where it has been"). IV rank and percentile are not defined in this quarter.
13. **IV rises with fear/demand** ("a fear gauge"). A spike lifts long-option prices (+25% IV → +$51) but cannot save
    a position against heavy decay (scenario D: −$75).

**Strategy stance**
14. **The instructors do not buy options to bet on direction:** "We never buy options as a way to guess direction"
    and "this is our least favorite way to trade options." They prefer strategies that collect time decay (taught
    later). *(mapping: Scalp City only buys calls/puts on chart direction, which is exactly what this course warns
    against. Weigh that against the backtests in CLAUDE.md, which so far lose money.)*
15. **You don't need to hold to expiration.** Close at any time at market. Profit-taking is a decision: "we
    constantly have to make decisions about when to sell." No specific profit-target or stop-loss percentages are
    given in this quarter.

**Not covered in this quarter:** delta ranges, choice of days to expiration, open interest or volume thresholds,
IV rank/percentile, position sizing, and specific profit/stop percentages. The course says strike and expiration
choice "you're going to learn ... later," and the Greeks get their own chapter.

---

## Claims to verify

- **"Implied volatility is actually very predictable whereas stock prices aren't that predictable."** A central
  claim behind the course's strategy, offered without evidence in this part. Check it against how IV actually
  behaves before relying on it.
- **"We never buy options as a way to guess direction ... we don't ever trade options in this way."** A statement
  of their own practice and preference. It implies (without showing data) that selling or decay-capturing
  strategies do better.
- **"Most option traders ... completely ignore this third factor and then they wonder why they can't figure out how
  to make any money."** Opinion; no data.
- **Volatility is "equally as important as the other two factors, if not more important."** Opinion.
- **Options exist because they are "simply insurance for an investor."** A teaching simplification. Speculation is
  also a large share of option volume, which the instructors acknowledge in practice.
- **"It's extremely powerful once you learn how to do this"** (profiting from time decay). A promotional claim; no
  results are shown.
- **The presenters sell a service** ("we actually work with traders on a case-by-case basis" on automating
  trading). Weigh their opinions with that in mind.
- **The Theo-tool scenario figures** are model estimates from thinkorswim, not real trades. They show directions of
  effect, not realized P/L.
- **The insurance price examples** ($500 put, $500 call) are assumed numbers, not market quotes.
