# Options Trading For Beginners (4-hour course): final quarter

Source: "Options Trading For Beginners (Complete 4 Hour Course)", https://www.youtube.com/watch?v=u847cbKEWu0
(SkyView Trading; the instructor names the firm when describing their back ratio habit). These notes cover the
last quarter of the auto-captions (`7-part-03`, read in full). Caption errors are fixed silently where the meaning is
obvious, e.g. "450" means $4.50, "3:15" means $3.15, "Thinker Swim" means thinkorswim, "stringle" means strangle,
"9085" means 90.85. Anything I add is marked "(note: ...)".

**What this quarter covers:** neutral and premium-selling spreads: the end of the iron condor, then the
butterfly, short strangle, short straddle and the "back ratio" spread. None of them is a single long call or put, which
is what Scalp City buys. The bot-relevant parts are the general habits the instructor states: choosing strikes by
probability ITM or delta, DTE preferences, liquidity, checking the risk box before sending, and how IV affects spreads.
These notes keep them.

One option contract = 100 shares, so 1 point = $100 per contract in every example below.

---

## 1. Iron condor (end of the lesson)

### Worked example (XYZ around $75; the start of the example is in the previous quarter)
Legs: **short 85 call at 2**, **long 90 call at 1**, **short 65 put at 2**, **long 60 put at 1**. Net credit = 2.00 ($200).

- **Stock stays in range at expiration:** every option expires worthless. +$200 on the short 85 call and +$200 on
  the short 65 put = +$400; −$100 on the long 90 call and −$100 on the long 60 put = −$200. **Net +$200.**
- You are betting the stock stays in a range, and you treat the four legs as **one trade**. Losing money on the long
  wings is intended: "It's kind of like we pay for car insurance, but we don't actually want to crash our car."
- **Stock runs to $96 at expiration:**
  - Puts: both worthless: +$200 short put, −$100 long put = +$100.
  - 85 call is 11 points ITM (worth 11): sold at 2 → −9 points = **−$900**.
  - 90 call is 6 points ITM (worth 6): bought at 1 → +5 = **+$500**.
  - Total: **−$300**. That is the **maximum loss**, whatever the price (104, 25, 0, "infinity"). Max loss happens when
    the stock is beyond the long strikes at expiration.

### Monitoring
- You usually watch the **net price of the whole condor**, not each leg. Platform example (a condor on Facebook):
  sold at **1.12**, now trading **0.82**, profit **$30**.

### Formulas
- **Max profit** = net credit received (2.00 → $200).
- **Max loss** = width between short and long strikes − net credit (5 − 2 = 3 → $300).
- The max loss is also the **capital requirement**. Why the instructor calls the condor "so powerful": you sell premium
  "with very little risk and also without the large capital requirement".
- **Break-evens:** upper = short call strike + credit; lower = short put strike − credit. Example: 87 and 63 (the
  thinkorswim box shows max profit $200, max loss $300, range 63–87).
- Above the range at expiration you lose; inside it you make money.
- Recommendation: **check the platform's confirmation pop-up (max profit, max loss, break-evens) before sending.**

### Placing one in thinkorswim (Tesla, neutral)
- Goal: collect time decay on TSLA with no directional view, so pick strikes for a neutral stance.
- Add the **"probability ITM" column** to the option chain; **if your platform lacks it, use delta instead.**
- Expiration in the example: **30 days**. "We prefer to initiate our trades with **30 to 60 days to expiration**."
- Short call at **~13% probability ITM** → the 260 call. Right-click the bid → "sell iron condor". The default width,
  **5 points**, is kept: sell 260 call, buy 265 call.
- Neutral means **choosing the put with the same probability ITM as the call** (~13%) → the 187.50 put; long put 5
  points further OTM → 182.50.
- Result: max profit **$101**, max loss **$399**, profit range **186.49 to 261.01** (the captions also garble it as
  "$11"). Very high probability of success but a **poor risk-to-reward** (101 vs 399).
- Trade-off: **move the short strikes closer** (10 points in on both sides) → the credit rises to **1.70** (from 1.01).
  Lower probability (narrower range), better risk-to-reward.
- What the same condor would cost **2 days before expiration** with the stock and IV unchanged (the July weekly
  expiring in 2 days): **0.01**. Two choices: **close it at 0.01 for the profit**, or let it expire worthless if the
  stock stays put. "The choice is yours."

---

## 2. Butterfly

### Premise
- You want the stock to **pin at an exact strike** at expiration (an iron condor wants a range instead). If it
  finishes at or near that price, "you're going to hit a home run".

### Construction (long call butterfly, XYZ at $75, target $80)
- Buy 1 **75 call at 4.50**, sell 2 **80 calls at 3.15**, buy 1 **85 call at 2.00**. Net debit = 4.50 − 6.30 + 2.00 =
  **0.20** ($20).
- The middle strike is the **body**; the outer strikes are the **wings**. Mnemonic: **"sell the body and buy the
  wings."**

### Scenarios at expiration
- **Stock at 80 (the body), best case:** 75 call worth 5 (+0.50), two 80 calls worth 0 (+3.15 × 2 = +6.30), 85 call
  worth 0 (−2.00). Net **+4.80 = $480**. As a whole: bought the butterfly at 0.20, sold at 5.00.
- As with any spread, only the net price matters: buy the butterfly at one price and sell it higher. It rises when
  the stock moves toward the body as time passes. The per-leg math is only there to show how it works.
- Hitting max profit needs exactly 80 at expiration: "a long shot", a very low probability, which is why it pays $480
  per $20 risked.
- **Stock at 76:** the 80 and 85 calls are worthless (+6.30, −2.00); the 75 call is worth 1 (−3.50). Butterfly worth
  1.00, bought at 0.20 → **+0.80 ($80)**: "turn a tiny $20 investment into $100" with the stock 4 points from the body.
- **Stock at 70 (outside the wings):** everything is worthless → you lose the **0.20** paid. **Max loss = the debit**,
  since a butterfly can't go below zero.
- **Warning:** that is true only when the **wings are equidistant from the body**. Moving the 85 wing to 90 "would
  just throw everything off and you could actually lose more than the amount you pay". That skewed version is the
  **broken wing butterfly**, a different strategy. Learn the regular one first; "don't get fancy with the strike
  selection".
- The payoff is **symmetrical**: max profit at 80, max loss above 85 or below 75, linear in between.
- Exercise: stock at **90** at expiration; fill in the P/L. The answer appears on screen, not in the captions.
  (note: by the same math: 75 call +10.50, two 80 calls −6.85 × 2 = −13.70, 85 call +3.00 → **−0.20**, the max
  loss.)

### Widening the strikes to raise the probability of profit
- 10-wide: long **70 call at 8.15**, short 2 × **80 call at 3.15**, long **90 call at 1.00** → net debit **2.85**.
  The most it can be worth is 10, so **max profit = 7.15**.
- Risk-to-reward: 5-wide = risk 0.20 to make 4.80 = **1:24**; 10-wide ≈ **1:2.5**. Worse ratio, but a **higher
  probability of profit**, because the profitable range is much wider.

### In thinkorswim; calls vs puts
- Right-click the option you want as the **body** → "buy butterfly"; adjust strikes and price; confirm and send.
- Demo: a put butterfly with the body at 115 vs a call butterfly at the same strikes: **identical** max loss, max
  profit and break-evens. (note: true for European-style payoff at expiration with equal strikes; it follows from
  put-call parity.)
- **Recommendation:** choose the side that puts the **body out of the money** when you open it, because **OTM options
  are more liquid than deep ITM ones** ("we simply choose to go wherever the liquidity is"). Example: expecting Apple
  to rise to 125 → call butterfly (the 125 call is OTM); expecting a drop to 115 → put butterfly.

### Recap and formulas
- Sell 2 calls or puts (the body); buy 1 lower-strike and 1 higher-strike wing, **all strikes equidistant**.
- **Max loss** = the price paid (stock outside the long strikes at expiration).
- **Max profit** = strike width − entry price (at the body at expiration). Example: 70/75/80 bought at 0.20 → max
  profit 5 − 0.20 = **4.80 ($480)**, max loss 0.20.
- **Break-evens** = body ± max profit (two of them; profit only in between). (note: equivalent to lower wing + debit
  and upper wing − debit; for 70/75/80 at 0.20: 70.20 and 79.80.)
- **Direction:** bullish, bearish or neutral depending on where the body sits relative to the stock; you need the
  stock to move toward the body.
- **Time decay depends on placement:** a butterfly far OTM has decay against you; one at the current price has decay
  in your favor. Rule of thumb: **stock between the break-evens at entry → decay helps; outside them → decay hurts.**
- **Implied volatility:** you want IV to **fall** after entry, since the butterfly then gains. Reason: a stock pins
  more easily when IV is low; with high IV "the stock is going to be all over the place", so **butterflies are cheap
  when IV is high**.
- **Tip 1:** open butterflies when IV is high (cheap to buy), then sell higher if IV drops.
- **Tip 2:** widen the strikes for a higher probability of profit, at a worse risk-to-reward.

---

## 3. Short strangle

### Premise
- A short strangle = **short OTM call + short OTM put**. You want the stock to stay **below the short call and above
  the short put** (sideways, inside a range), so both legs profit.

### Example (XYZ at $75, 30 DTE, strikes 10 points out)
- Sell the **85 call at 2** and the **65 put at 2** → credit **4 ($400)**.
- **Stock at 82 at expiration:** both OTM, both worthless → **+4 = $400**. As one trade: sold at 4, now 0.
- **Stock at 94:** the put is worthless (+$200); the 85 call is 9 ITM, worth 9 (sold at 2 → −7). Net **−5 = −$500**.
- You have risk on both sides, but **you can't lose on both sides**: the stock can't be in two places at once. Selling
  a put and a call is **not double the risk**. (note: true at expiration. Before expiration a rise in IV can mark
  both short legs down at once.)

### Placing one in thinkorswim (Netflix)
- NFLX at **129.89**, options with **38 DTE**.
- Strikes further OTM → a wider range and a higher probability of profit, but less premium. "There's **no magic
  number** when choosing your strikes": balance a high probability against a decent return.
- Starting point: strikes with **~16% probability ITM** → the **150 call**; the put side at **~18%** → the **110
  put** ("close enough").
- Right-click the call's bid or ask → "sell strangle", then change the put strike (from the default 145 to 110).
  Position size keeps the 1:1 ratio automatically.
- Price: you are selling, so you want the **highest fill possible**; the example uses the current prices.
- **Always check the individual legs before sending** (here: sell the 150 call, sell the 110 put).
- Confirmation box: **buying power effect ≈ $1,300**; **max loss: infinite**, which they prefer to call
  **"undefined"**; max profit = the credit, **3.69 → $369** for 1 contract, earned if the stock stays between the
  short strikes.
- **Break-evens:** short call strike + credit; short put strike − credit. Inside → profit; outside → loss.

---

## 4. Short straddle

### Premise
- "The strangle's more aggressive twin brother": sell an **ATM call and an ATM put at the same strike**, hoping the
  stock stays as close to that strike as possible.

### Strangle vs straddle (XYZ at $75)
- Strangle: sell 85 call at 2 + 65 put at 2 = 4 credit. Max profit **$400** anywhere between 65 and 85.
  Break-evens: **85 + 4 = 89** and **65 − 4 = 61**. Profit between 61 and 89.
- Straddle: sell **75 call at 4.50** + **75 put at 4.50** = **9 credit**. Max profit **$900**, but **only if the
  stock pins exactly at 75**; profit shrinks the further it ends from 75 and eventually turns into a loss.
  Break-evens: **75 + 9 = 84** and **75 − 9 = 66**.
- "We basically just want the stock to stick to our strike price like a magnet"; at minimum, it should not move more
  than the credit (9 points) either way.
- Trade-off: the straddle's range is tighter → **lower probability of profit** but a **higher potential payout**. The
  strangle → higher probability, smaller payout.
- "We actually trade both of these strategies on a regular basis"; the choice depends on the market environment,
  covered in "part two" (not in this course section).

### Scenarios (short 75 straddle at 9)
- **Stock at 77:** put worthless, call worth 2 → straddle worth 2 → **+7 = $700**.
- **Stock at 61:** call worthless, put worth 14 → straddle worth 14 → **−5 = −$500**.
- Rule: **at expiration the straddle is worth |stock − strike|.**

### In thinkorswim
- Right-click the **ATM call's** bid or ask → "sell straddle". The box shows buying power effect, max loss, max
  profit and break-evens; the same as a strangle except the break-evens are tighter and max profit needs the exact
  strike.

---

## 5. "Back ratio" spread (1×2, as taught)

### Construction
- Think of it as a **long vertical financed by selling an extra OTM option**: buy 1, sell 2.
- Example: **buy 1 80 call at 3.15**, **sell 2 85 calls at 2.00** → net **credit 0.85**. Ratios of 1:3, 1:4,
  1:5 are possible, but "we usually just stick to the 1:2 ratio to keep it simple".
- Decomposition: long 80/85 call vertical at 3.15 − 2.00 = **1.15 debit**, plus **one naked short 85 call at 2.00**.
- (note: what is taught here (buy 1 lower strike, sell 2 higher, for a credit, unlimited upside risk) is usually
  called a **1×2 ratio (front) spread**. In thinkorswim it is entered as "sell back ratio", which is why the
  instructor uses that name. A textbook "ratio backspread" is the opposite: sell 1, buy 2, with unlimited upside
  profit.)

### Scenarios at expiration
- **Stock at 73:** everything worthless. Vertical −1.15, short call +2.00 → **+0.85** (keep the credit).
- **Stock at 85 (the short strike), best case:** vertical worth 5 (+3.85), extra short call worthless (+2.00) →
  **+5.85 = $585**. In the platform: sold at 0.85, closed at a **debit of −5.00**. The spread "doesn't stop when it goes
  to zero. It can go negative", so you can make more than the credit.
- **Max profit** = strike width + net credit = 5 + 0.85 = **5.85**.
- Summary: big money if the stock rises a little and ends at the short strike; a small profit (the credit) if it
  falls or goes sideways.
- **Risk:** the vertical's gain is capped at 3.85 but the extra short call has **theoretically unlimited loss**
  ("undefined") on a big rally.
- **Stock at 90.85:** vertical +3.85; 85 call worth 5.85 (sold at 2 → −3.85) → **break-even**. Below it you make
  money, above it you lose.
- **Break-even** = short strike + max profit = 85 + 5.85 = **90.85**.
- Risk profile: a small profit below 80; **more than the credit between 80 and 90**; losses above 90.85.
- "Taking theoretical risk is how we make big money in the markets because **theoretical risk is not always
  indicative of actual risk**" (opinion; see Claims).
- The put version is the mirror image.

### In thinkorswim (SPY)
- Right-click a call's bid or ask → "sell back ratio".
- SkyView habit: **widen the strikes as far as possible while still collecting a net credit.**
  - Default 1 point wide (short strike 228): credit **2.57**.
  - Short strike 229: smaller credit; 230 (3 wide): credit **0.41**; 231: **a debit**. That means the long vertical
    is no longer fully financed, so go back to 230.
  - Why: a smaller credit, but a **wider zone** where you make more than the credit. Still always take a credit, so a
    fall in the stock doesn't lose money.
- Confirmation box: the **capital requirement is high**, about the same as **one naked SPY call** (one of the two
  short calls is covered by the long call). "There's no way to really calculate this": check the pop-up.
- Max profit = 3 + 0.41 = **3.41 ($341)**; max loss **undefined** (naked call); break-even = 230 + 3.41 =
  **233.41**. Below it you profit, above it you lose.

### Recap
- **Call back ratio** (as taught): **bearish to neutral**, with a "home run" if the stock rises a little and ends at
  the short call strike.
- **Put back ratio:** the same idea, **bullish to neutral**; a home run if the stock dips a little and ends at the
  short put strike.

---

## Rules a bot could use

Most of this quarter covers multi-leg premium-selling spreads that Scalp City does not trade (it buys single 0DTE
calls and puts). The rules below are the ones that can be checked in code, with where each comes from. **None of them
is backed by data in the video**; they are the instructor's practices.

**Contract and strike selection**
1. **Choose strikes by probability ITM, or by delta if probability ITM isn't available.** "add the probability in the
   money column ... If you are using a platform that doesn't have this feature, then you can use Delta instead." (Iron
   condor, TSLA.) Check: the selector reads `prob_itm` or falls back to |delta|.
2. **Short strikes for neutral premium selling at about 13–18% probability ITM**, the same on both sides for a
   neutral stance: "find a call with a probability in the money of 13%"; "the same probability in the money as our
   call"; strangle "probability in the money of around 16%". Short-premium strategies only; not applicable to the
   bot's long entries.
3. **DTE 30–60 for these spreads.** "we prefer to initiate our trades with 30 to 60 days to expiration." This
   contradicts 0DTE. Record it as the instructor's preference for premium selling, not a rule for the towers.
4. **Prefer OTM contracts for liquidity.** "out of the money options tend to be a bit more liquid than deep in the
   money options. So we simply choose to go wherever the liquidity is." Check: when two contracts express the same
   view, pick the OTM one (or the one with the tighter spread and higher volume or OI). No numeric thresholds are
   given.
5. **There is no magic strike.** "there's no magic number when choosing your strikes": a probability-of-profit vs
   return trade-off. Moving strikes closer raises the credit and the reward:risk but lowers the probability (TSLA:
   1.01 → 1.70 credit). For a bot: tune strike distance on data and report both win rate and payoff.

**Order entry and pre-trade checks**
6. **Verify every leg and the risk box before sending.** "do one last check before sending the order and make sure
   the spread you are trading is correct by looking at the individual legs"; "check this popup box before sending the
   order". Check: assert symbol, strike, side, quantity, max loss and break-even before submit.
7. **Limit price on the right side.** "we are selling this spread. So we would want to get filled at the highest price
   possible." (A buyer wants the lowest.) Check: limit orders, never paying through the mid unnecessarily.
8. **Check the capital requirement before trading undefined-risk structures.** "You'll just have to check what the
   capital requirement is by clicking confirm and send." Check: buying-power effect ≤ the configured limit.

**Risk definition and sizing**
9. **Prefer defined risk; max loss = capital requirement on an iron condor.** "Our maximum loss is simply the width
   between our short and long strikes minus our net entry price ... This $300 is also our capital requirement."
   Check: compute max loss before entry and size from it.
10. **A butterfly's max loss = the debit only when the wings are equidistant.** "Everything I'm saying ... is true,
    assuming the wings of the butterfly are equidistant." Check: reject asymmetric wings if the risk model assumes
    debit = max loss.
11. **Undefined-risk structures (short strangle, straddle, 1×2 ratio) have unlimited loss**: "the max loss is infinite
    or as we like to say it's undefined." Scalp City is long-only premium; never add these without a separate risk
    model.

**Exits**
12. **Close near-worthless short premium instead of holding to expiration.** The TSLA condor at 2 DTE was worth
    0.01: "We could close this position at 1 cent for a profit. Or ... let the options expire worthless ... The choice
    is yours." No profit-target percentage or stop-loss rule is given in this quarter.
13. **Track the spread's net price, not the legs.** "we are usually just monitoring the price of the iron condor as a
    whole." For a bot: P/L and exits on the position's combined mark.

**Volatility**
14. **Buy (ATM) butterflies when IV is high; they gain if IV falls.** "Initiate the trade when implied volatility is
    high ... we will be able to buy a butterfly for a very cheap price." Not directly a single-option rule, but the
    same lesson as elsewhere in the course: a long-premium position loses when IV falls, so a long call or put bought
    at high IV is exposed to IV dropping.
15. **Time decay depends on placement:** "if the stock is in between your break even points when you initiate the
    trade, then time decay will typically be in your favor ... outside ... against you." A plain long call or put
    always has decay against it (note: the course says this in earlier parts; not restated here).

**Not covered in this quarter:** explicit delta ranges for buying single options, open-interest/volume/bid-ask
thresholds, IV rank/percentile numbers, earnings or IV-crush rules, position-size percentages, stop-losses.

---

## Claims to verify

- **"Iron condor is so powerful because we can sell option premium with very little risk."** Opinion. The risk is
  defined, but in the TSLA example the risk is ~4× the reward (101 vs 399). "Little risk" refers only to the capital
  required, not to the reward:risk or the expected value.
- **"The trade has a very high probability of success."** (TSLA condor.) A probability-ITM reading from the platform's
  model, not a measured win rate. A high win rate with a 1:4 payoff can still lose money.
- **"You don't have double the risk because you can't lose money on both sides."** True at expiration; before
  expiration, a rise in IV can lose money on both short legs at once (note).
- **"Theoretical risk is not always indicative of actual risk" / "taking theoretical risk is how we make big money in
  the markets."** Opinion with no evidence. Unlimited-risk short calls can and do produce large losses.
- **"Butterflies will be very cheap when implied volatility is high", so buy them when IV is high.** Broadly true for
  ATM butterflies (net short vega); for butterflies far OTM, vega can be positive (note). No data shown that this
  timing makes money.
- **Put and call butterflies are "exactly the same".** Shown on one example with the same strikes; true at expiration
  by put-call parity (note). With American options, dividends or early assignment they can differ slightly.
- **"We actually trade both of these strategies on a regular basis."** About their own practice; no results given.
- **Turning "$20 into $100" (butterfly) and $480 per $20 risked.** Best-case arithmetic; the instructor himself calls
  max profit "a long shot". Not a performance figure.
- **The name "back ratio" for a buy-1/sell-2 spread** follows thinkorswim's "sell back ratio" order. Most references
  call this a ratio (front) spread (note).
- No backtests, win rates or account results are presented in this quarter. Every "high probability" statement rests
  on the platform's model-implied probability ITM.
