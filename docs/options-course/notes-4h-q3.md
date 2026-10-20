# 4-hour course, third quarter: short options in practice, assignment, covered stock, verticals, iron condor (start)

Source: "Options Trading For Beginners (Complete 4 Hour Course)", https://www.youtube.com/watch?v=u847cbKEWu0
(Sky View Trading). This file covers the third quarter of the transcript (scratch file `7-part-02`, 271 caption lines),
read in full. Auto-captions: prices like "37", "1965" or "10180" are cents or dollars-and-cents ($0.37, $19.65,
$101.80) and "ThinkersW"/"Thinker Swim" is the thinkorswim platform; fixed below. Citations are "L<n>" = line in
that transcript part, with a few quoted words. The quarter starts mid-example and ends mid-way through the iron condor.

## 1. Short option trade walk-through (GDX short put, Caterpillar short call), held to expiration (L1–L57)

- Setup carried over from the previous quarter: both trades have **11 days to expiration (DTE)**, one contract each.
  - **GDX:** sold the **20-strike put for $0.37**. Platform showed a **67% chance** of the option expiring out of the
    money, i.e. of keeping the full credit (L1–L2). Capital requirement ("buying power effect") **$329** (L3).
  - **Caterpillar:** short the **99-strike call**, sold for **$0.35** (L9, L36).
  - Capital requirements vary a lot by underlying ("some ... are just outrageous"): they depend on stock price,
    implied volatility (IV), etc. "Just make sure you check what it is before making the trade" (L3–L5).
- They deliberately did not take profits or cut losses: hold to expiration to show the outcome, hoping one would lose
  "as you aren't going to learn from only seeing profitable trades" (L10–L11).
- **Day 1 (10 DTE):** both stocks rose. GDX position delta **+26.61** (positive delta = profits when the stock rises).
  CAT delta **−21.42** (loses when the stock rises): **down $10.50** (L12–L14).
- **Parentheses around P&L = a loss**; no parentheses = profit (L14–L15).
- **9 DTE:** GDX fell toward the 20 strike: −$15 on the day, open P&L +$9. CAT moved in their favour: +$26.50 on the
  day, open P&L +$14 (L15–L17).
- **Next day:** GDX **pierced the 20 strike**. The put sold at $0.37 is now **$1.23** ("put options rise in value when
  the stock falls"): down $0.86 = **−$86** on one contract (L18–L20).
- **Delta grows against a short option ("gamma risk").** GDX delta went from about +26 to **+70**. "As the position
  goes against us, our deltas will grow." Gamma is the rate of change of delta; short options carry a lot of gamma.
  "Any strategy where time decay is in your favor, you will have gamma against you" (theta for you, gamma against you)
  (L21–L23).
- **Why the delta grew so fast: short DTE.** "We tend to place our trades in an expiration cycle with around 30 to 60
  days to expiration. But for these two trades, we broke that rule ... 11 days ... that's why our deltas have grown so
  fast" (L25–L26). Hence keep position size in check and choose an expiration with less gamma exposure (L24–L25).
- **Delta bound:** a single contract's delta can never exceed 100 (one contract = 100 shares) (L26–L27).
- Their view: they "tend to be more bullish on stocks that have recently sold off and bearish on stocks that have been
  making new highs", so getting longer as GDX falls is acceptable to them (L28–L30). (Opinion; see Claims.)
- Time decay helped GDX P&L while the stock traded flat; at expiration an option is worth only its intrinsic value
  (L32–L33). CAT was profitable enough to close early if wanted (L33–L34).
- **Expiration day (Friday, 0 DTE):** options expire after the close that evening (L34–L35).
  - **CAT (far OTM):** "highly unlikely" to reach 99 that day, so let it **expire worthless**: keep the $35; the
    position is removed over the weekend. **No commission to close** when an option expires worthless (L35–L38).
  - **GDX (ITM):** a short put held through expiration ITM turns into **long 100 shares at $20** on Monday. Fine if you
    want the stock; otherwise **close before expiration**. It was down $47.50 (L38–L41).
- **Closing a short option = buying it back** ("create closing order", buy to close). You can sell to open and buy to
  close (L41–L44).
- **Fill example:** order to buy back at **$0.76** while bid **$0.76** / ask **$0.79**: not filled. **Cancel/replace**
  at **$0.78**: filled (L45–L49).
- **Result:** GDX sold $0.37, bought back $0.78 → **−$41**. CAT sold $0.35, expired → **+$35**. Net a few dollars
  lost (L51–L54).
- They made **three other trades (AAPL, QQQ, DIA)**, all profitable, "hoping at least one ... would be a losing
  trade". Four winners, one loser, presented as showing "how powerful it is to trade a high probability trading
  strategy" (L54–L58). Note they also "did a few takes on these trades" (L54).

## 2. Short call: recap and rules (L58–L69)

- **Bearish to neutral**: want the stock to go down or stay below the strike (L58–L59).
- **Time decay in your favour** ("why this strategy provides so much consistency"); **benefits from a fall in IV**
  (L59–L60).
- "Selling options is like selling insurance", and **IV is a measure of fear**: high fear/IV → expensive options
  (L60–L61).
- **Max profit** = price sold. **Max loss = undefined** (no limit to how high the stock can go) (L61–L62).
- **Break-even = strike + entry price.** Below it at expiration: profit; above: loss (L62–L63).
- **Recommendations** (L63–L69):
  1. **Trade it when IV is high**: the premium lets you go further OTM with decent profit potential ("in depth in
     part two").
  2. **Open with 30 to 60 DTE**: "We've done a lot of research that suggests that 30 to 60 days is the sweet spot for
     selling option premium."
  3. **Strike selection: around 65% to 85% probability OTM**, "if and only if you can collect a decent profit".
  4. **Minimum credit: "never sell an option cheaper than 75 cents or so"**, so you can (a) take profits early and
     (b) keep fees from eating the profit. "Most of the time we are selling options for no less than 75 and usually
     even more" (they break it "every now and then").

## 3. Short put: recap (L69–L77)

- Same idea, **bullish to neutral**: want the stock to go up or stay above the strike. Theta in favour; benefits from
  falling IV (L70–L71).
- **Break-even = strike − entry price** (L71–L72).
- **Max profit** = premium received. **Max loss is not undefined**: the stock can't go below zero, so max loss =
  **strike − entry price** (per share), i.e. equal to the break-even stock price (L72–L76).
  - Example given: short GDX 20 put "at 35" → break-even $19.65 → max loss $19.65/share = **$1,965** per contract.
    (note: earlier the same put was sold at $0.37, which would give $19.63 / $1,963; the instructor mixed it up with
    the CAT credit of $0.35. The formula is right.)
- Tips: same as the short call (L76).

## 4. Early assignment ("assignment nuisance") (L77–L102)

- Horror stories: assigned on a short option without the capital to cover. Called **early assignment risk** (L77–L78).
- **Example:** $5,000 account, short 1 XYZ 100-strike put, capital requirement $500, $4,500 free. Broker emails "Alert,
  immediate action required ... assignment may cause insufficient balances ..." (L78–L81).
- What it means: whoever bought the option from you exercised it. The **short put becomes long 100 shares at $100**:
  capital requirement $10,000 (only **$5,000 in a margin account, 50% for stock**) (L86–L89). You don't have the
  capital (L89–L90).
- **Two fixes:** (1) deposit more money; or (2) more likely, **close the stock at market and re-open the original
  option position at its current market price**: "it's like it never happened, aside from the small commission of $15
  you might have had to pay for the assignment" (L90–L93).
- Instructor's claims: "won't even result in any trading losses, aside from the small assignment fee"; rename it
  "assignment nuisance"; any short option is exposed to early assignment "but ... it rarely happens": "thousands of
  trades ... only remember two or three times" (L94–L99). Offered email help (info@ Sky View Trading address; the
  caption reads "skytrading.com") (L100–L101). "Don't believe the horror stories" (L101–L102).
- (note: closing stock and re-opening the option at market is not free in general: you cross two bid/ask spreads,
  and the stock may have moved between assignment and the open. Early assignment of short calls is also more likely
  before an ex-dividend date, when the short owes the dividend. The instructor does not mention either.)
- Promo break (L104–L106): like/subscribe, and they "work with traders on a case-by-case basis" on automating and
  scaling trading (link in description). Not course content.

## 5. Covered stock / covered call (L106–L159)

- **Definition:** long stock + short call (one contract per 100 shares). Often the first option strategy for stock
  investors; improves probability of profit and enhances returns by collecting premium (L106–L109).
- **Example:** XYZ $75, 30 DTE. Buy 100 shares at $75, sell 1 **85-strike call for $2** (L110–L112).
- **Treat it as one trade / one spread price.** Net entry (net cost) = 75 − 2 = **$73** (L118–L121).
- **Scenario 1, stock to $85 at expiration:** call at the money, no intrinsic value, worthless. Stock +10, call +2 →
  **+12 points = $1,200**. Net exit 85 − 0 = 85; bought at 73 → +12 (L113–L121). Stock alone: +10 (L121–L122).
- **+12 is the max profit.** Above the strike the short call's loss offsets the stock gain:
  - stock $90: stock +15, call worth 5 (sold 2) → −3 → net +12 (L124–L125);
  - stock $150 (doubles): stock +75, call worth 65 → −63 → net +12 (L125–L128).
  - The spread "can never go higher than ... the strike price of the option" (L128).
- Being called away is "no harm to us"; regretting the capped gain is "an amateur thing ... all hindsight"; "we want
  the stock to go through our short call strike because that means we make the max potential profit" (L128–L130).
- **Scenario 2, stock to $73.50:** stock −1.50, call worthless +2 → **+$0.50** (L131–L133). The premium lowers the
  cost and **improves the break-even (here $73)** (L133–L136).
- **Trade-off:** capped profit in exchange for a better break-even and a higher probability of profit (L136–L137).
- **Scenario 3, stock to $67:** stock −8, call +2 → **−6** (less than −8 for stock alone) (L137–L139). "We are always
  going to be two points better off, unless the stock skyrockets" (L140).
- **Two ways to trade it** (L141–L146):
  1. Sell a call against stock you already own. **Strike = where you're willing to sell the stock.** No extra capital:
     "doing so adds absolutely no risk to your portfolio" (L142–L144).
  2. Enter and exit as **one position** (spread order).
- **thinkorswim example (AAPL):** stock $116.29; would happily sell at $119. Right-click the 119 call → "buy covered
  stock". Call about $1; **net price $115.28**. The platform keeps the 1 contract : 100 shares ratio when you change
  size. Buying a spread → want the lowest fill price (L145–L152).
  - Always check the individual legs before sending (sell the 119 call, buy 100 shares) (L152–L153).
  - Buying power effect "a little over $3,000" (L154). **Max loss = price paid**: $115.28 × 100 = **$11,528** if the
    stock goes to zero ("highly unlikely" for Apple) (L154–L156).
  - **Max profit = strike − covered-stock entry**: 119 − 115.28 = **$3.72** (L156–L157).
  - **Break-even = price paid for the covered stock** (L157–L158).
- (note: a covered call reduces risk versus stock alone but the stock's downside is still there; "adds absolutely no
  risk" is true only relative to already owning the shares.)

## 6. Long vertical spread (debit spread) (L159–L207)

- Most beginners **buy options** because it's simplest and needs less capital than stock (L159–L161).
- **Problem with buying a single ("naked") option:** XYZ $75; buy the **70 call for $7.50** ($750). Time decay is
  against you and the stock must move a lot to break even: **break-even $77.50**, 2.5 points above the price. Sideways
  = "you're screwed" because the option decays every day. "Options ... are depreciating assets. And any smart investor
  is not going to buy a depreciating asset and call it an investment" (L161–L166).
- **Fix: buy the 70 call ($7.50) and sell the 80 call ($2.50)** → net **$5.00** ($500). This is **buying a vertical
  spread**: lower cost, better break-even (**$75 = current price**), better probability of success. Claimed to
  "eliminate time decay altogether" (L167–L171).
- **Scenarios at expiration** (L172–L188):

  | Stock at expiry | 70/80 call vertical (cost $500) | Long 70 call (cost $750) |
  |---|---|---|
  | **$79.50** | short 80 worthless +$250; long 70 worth $9.50 → +$200; **+$450, 90% return**; max risk $500 | worth $9.50 → **+$200, 26.67%**; max risk $750 |
  | **$75** (sideways) | long 70 worth $5 → −$250; short 80 +$250 → **break-even** | **−$250 (−33%)** from time decay |
  | **$50** (wrong way) | both worthless: −$750 + $250 = **−$500** | **−$750** |
  | **$85** (big move) | long 70 worth $15 → +$750; short 80 worth $5 → −$250; **+$500 (100%)** | **+$750** |

  - The vertical wins in the first three; the naked call wins only on a big move. "Only downfall": **limited profit
    potential**. "Unlimited" upside of a long call is "just theoretical" (L183–L187).
  - "These three scenarios are going to happen way more often, and the vertical spread will pay you far more in the
    long run than the few times you might ... hit a home run" (L187–L188).
- **thinkorswim:** right-click the option to buy → "buy vertical", adjust strikes. **Instructor's preference: "buy one
  strike in the money and sell one strike out of the money"** (L189–L190). The confirm box shows max profit, max loss,
  capital required, break-even (L191). Same on the put side for a bearish bet (L191–L192).
- **Long call vertical recap** (L192–L203):
  - Bullish; "kind of like stock replacement": a directional bet (L192–L193).
  - "If you properly choose your strikes, then time decay will not be an issue, but it also won't be in your favor.
    And the same goes for implied volatility" (L193–L194).
  - **Max loss = net entry price** (L194).
  - **Max profit = strike width − entry price.** Example: 70/75 (width 5) bought at 2 → max profit 3. The spread can
    never be worth more than the width (L194–L197).
  - **Break-even = long strike + entry price**: 70 + 2 = **72** (L197–L199).
  - **Tip 1: pay about 50% of the strike width** (1-wide → ~$0.50; 5-wide → ~$2.50). That puts the break-even at about
    the current stock price. "Make sure that your break even point is better than or equal to the current stock price
    ... then time decay will not be against you" (L199–L203).
  - **Tip 2: trade it with small size**, "because we don't have that much of an edge with this strategy since it's
    simply just a directional bet" (L203–L204).
- **Long put vertical:** same, bearish. Max profit/loss computed the same way; **break-even = long strike − entry
  price** (L204–L207).

## 7. Short vertical spread (credit spread) (L208–L257)

- **Netflix example:** stock $93; bet it won't exceed $100. Selling the 100 call for $3 alone keeps $3 if NFLX stays
  below 100 (L209–L211). Problems with a naked short: (1) **unknown max risk**; (2) **possibly very large capital
  requirement** (L211–L213).
- **Fix:** sell the **100 call for $3.00**, buy the **105 call for $1.20** → credit **$1.80**: sell time premium "with
  very little capital and also with defined risk" (L213–L214).
- **Scenarios** (L215–L231):
  - **NFLX below $100:** both expire worthless: +$300 − $120 = **+$180**. No action, no commission to close; or close
    any time before expiry (L215–L221).
  - **NFLX to $130** ("only a 1% chance"): short 100 call worth $30 → −$2,700 (a naked short would have lost that);
    long 105 call worth $25 → +$2,380; **net −$320**. Same loss at $130 or $190 or anything above $105: the spread is
    worth at most the width ($5). Sold at $1.80, closed at $5 → −$3.20 (L221–L227).
  - **Between strikes, e.g. $101:** spread worth $1 → **+$80** (L227–L230).
  - **Break-even = short strike + credit = $101.80** (L230–L231).
- **Recap** (L232–L235): **max profit = credit ($180)**; **max loss = width − credit ($320), which is also the capital
  requirement**; **break-even = short strike + credit**. P&L graph: x-axis stock price, y-axis P&L. thinkorswim
  calculates all of this before you send (L235–L236).
- **Why risk more than you can make?** It "allows you to achieve a very high probability of success and profit
  without having to predict stock prices. Risk-to-reward and probability of success are directly tied to each other"
  (L237–L238).
- **thinkorswim, SPY:** right-click an OTM call bid/ask → "sell vertical"; defaults to **one strike wide**; the short
  strike is where you want the stock to stay below (L239–L242).
- **Pricing:** when selling you want a higher fill. "The default is the **mid price** between the bid and the ask on
  both options. So, use the mid price as a guide. The closer to the mid price that you can get in the trade, the
  better. And this is why we stick to **only liquid stocks**" (their "Sky View watch list") (L242–L244).
- **Put side:** sell a put, buy a further OTM put as protection; want the stock above the short put. **Short put
  vertical = bullish to neutral; short call vertical = bearish to neutral** (L245–L247).
- **Key rule:** when selling a vertical, **sell the closer-to-the-money, more expensive option and buy the further OTM,
  cheaper one** (thinkorswim defaults to this) (L247–L249).
- **Short call vertical overview** (L249–L254): bearish to neutral; theta in favour; benefits from falling IV.
  - **Tip 1: collect about 20% to 33% of the strike width.** 5-wide: 20% = $1.00, 33% = $1.67 → credit between $1.00
    and $1.67. Gives "plenty of profit potential while still ... a decently high probability of profit". A rule of
    thumb they sometimes break (L250–L254).
  - **Tip 2: open when IV is high** → options expensive → go further OTM for the same credit (L254–L255).
- **Short put vertical:** same, bullish to neutral. You only need the stock above the break-even; max profit if it
  stays above the short put strike (L255–L257).

## 8. Iron condor (introduction; continues in the next quarter) (L257–L271)

- **Time decay illustration, Netflix 90 put:** **3.35 × 3.50** with **37 DTE** vs **0.11 × 0.15** with **2 DTE**.
  "Each and every day, time premium is sucked out of these options." If you buy options "you are constantly fighting
  this time decay. Instead of fighting it, we prefer to let it work for us" (L258–L262).
- Presented as "one of our favorite option strategies ... even with a small account" (L262–L263).
- **Structure:** sell an OTM put and an OTM call (hoping the stock stays between the strikes and both go to zero), and
  buy a further OTM put and call for protection, because naked short options "can have a lot of risk and can require
  a lot of capital". Four options: two sold, two bought. Traded as one order (L263–L270).
- **Example:** XYZ $75: **sell 85 call $2, sell 65 put $2, buy 90 call $1, buy 60 put $1**; opened at **30 DTE**; the
  stock trades sideways and the options stay OTM as expiration nears (L267–L271). (note: that is a net credit of
  $2.00 on 5-wide wings; the instructor's own totals come in the next quarter.)

## Rules a bot could use

Context for Scalp City: the towers **buy** 0DTE calls/puts after chart setups. Most of this quarter teaches **selling**
premium at 30–60 DTE, and the instructor argues against buying single options. The rules below are what the source
says; where one conflicts with the bots' design, that is flagged, not resolved.

**Contract selection / structure**
1. **Prefer a debit vertical over a single long option for a directional bet.** "Instead of just buying the 70 strike
   call option ... simultaneously sell a cheaper out-of-the-money option to reduce our cost" (L167–L169). Checkable:
   compare break-even and max loss of long call vs vertical at entry.
2. **Debit vertical strikes: long one strike ITM, short one strike OTM.** "buy one strike in the money and sell one
   strike out of the money" (L190).
3. **Debit vertical price: pay ≈50% of the width; require break-even ≤ current price (calls) / ≥ current price
   (puts).** "pay about 50% of the strike width ... make sure that your break even point is better than or equal to
   the current stock price" (L199–L202). Break-even = long strike ± debit (L197, L206).
4. **Single long option break-even check:** long call break-even = strike + premium; the 70 call at $7.50 with stock
   $75 needs +2.5 points just to break even (L164). A bot can reject a long option whose break-even distance exceeds
   the expected move to target.
5. **Credit vertical: sell the nearer-the-money leg, buy the further OTM leg** (L247–L248); **collect 20–33% of width**
   (L251–L252).
6. **Short single options: 65–85% probability OTM, credit ≥ ~$0.75** (L66–L67). (Not applicable to a long-only bot,
   but the $0.75 floor rationale, fees and room to take profits early, applies to tiny-premium 0DTE contracts too.)

**Days to expiration / gamma**
7. **30–60 DTE for selling premium**: "30 to 60 days is the sweet spot for selling option premium" (L65). Short DTE
   means fast-growing delta (gamma): "we broke that rule ... 11 days ... that's why our deltas have grown so fast"
   (L25–L26). The source gives no DTE guidance for long options in this quarter; 0DTE is the extreme of the gamma it
   warns about.
8. **Time decay accelerates near expiry:** the NFLX 90 put went from 3.35×3.50 (37 DTE) to 0.11×0.15 (2 DTE) (L259–L260).
   A long-option bot is on the wrong side of this every minute it holds.

**Implied volatility**
9. **Sell premium when IV is high** (L63–L64, L254). Short options and short verticals benefit from falling IV
   (L60, L250). Corollary (not stated as a rule here): long single options are hurt by falling IV; a long vertical is
   roughly IV-neutral "if you properly choose your strikes" (L193–L194).

**Liquidity and order handling**
10. **Price spread orders at the mid; trade only liquid underlyings.** "use the mid price as a guide. The closer to
    the mid price that you can get in the trade, the better. And this is why we stick to only liquid stocks"
    (L243–L244). No numeric open-interest/volume/spread thresholds are given in this quarter.
11. **If not filled, cancel/replace one step toward the far side.** Bid 0.76 / ask 0.79: order at 0.76 unfilled;
    replaced at 0.78 and filled (L47–L49). A bot can step a limit from mid toward the ask in small increments with a
    cap.
12. **Verify legs before sending** a multi-leg order: "always good to do one last check ... looking at the individual
    legs" (L152–L153).

**Position sizing / risk**
13. **Small size for pure directional bets:** "trade this strategy with small size because we don't have that much of
    an edge ... it's simply just a directional bet" (L203–L204). Directly relevant: the towers' trades are directional
    bets.
14. **Keep sizing in check where gamma is against you** (L24).
15. **Check the capital requirement (buying power effect) before every trade** (L4–L5).

**Exits / expiration handling**
16. **Close in-the-money short options before expiration** unless you want the stock: held ITM, a short put becomes
    long stock (L38–L41). (For a long-option bot: an ITM long option held through expiry is exercised into stock;
    the bots already flatten before the close.)
17. **Far-OTM short options on expiration day can be left to expire** (no closing commission) (L35–L38).
18. No profit-target or stop-loss percentages are given in this quarter; the walk-through explicitly held to
    expiration "so you can see how they perform" (L10).

**When to avoid buying**
19. The instructor's general stance: avoid buying single options because time decay is against you and sideways
    markets lose: "if XYZ sits still and trades sideways, you're screwed" (L165). The vertical was break-even when the
    stock didn't move while the long call lost 33% (L177–L180). No earnings/IV-crush rule appears in this quarter.

## Claims to verify

- **"67% chance" / "65 to 85% probability OTM"** (L1, L66): these are the platform's model probabilities (delta/IV
  based), not observed frequencies.
- **"Research ... suggests that 30 to 60 days is the sweet spot for selling option premium"** (L65): no data shown.
- **"how powerful it is to trade a high probability trading strategy" (4 of 5 winners)** (L57–L58): five trades, and
  they "did a few takes ... in hopes that at least one of them would be a losing trade" (L54), so the sample is tiny
  and selected. High win rate says nothing about expectancy: one GDX loss (−$41) wiped out more than one winner
  (+$35). Same lesson as this repo's own results (report profit factor, not just win rate).
- **Assignment "won't even result in any trading losses, aside from the small assignment fee"** (L95–L96) and **"it
  rarely happens ... two or three times"** in thousands of trades (L98–L99): anecdotal; see the note in section 4
  (spreads, gaps, dividends). The **$15 assignment fee** is broker-specific.
- **"Time decay is in our favor, which is why this strategy provides so much consistency"** (L59): consistency of
  small wins with undefined tail risk on a short call (L61–L62).
- **Being more bullish on stocks that sold off and bearish on new highs** (L28): a stated preference, no evidence.
- **"Options ... are depreciating assets. Any smart investor is not going to buy a depreciating asset"** (L165–L166):
  opinion. True that extrinsic value decays; not a proof that buying options loses.
- **A long vertical will "eliminate time decay altogether"** (L167): overstated. The instructor's own recap says theta
  "will not be an issue, but it also won't be in your favor" **if** strikes are chosen with break-even at the current
  price (L193); net theta is reduced, not zero, and changes as the stock moves.
- **"These three scenarios are going to happen way more often, and the vertical spread will pay you far more in the
  long run"** (L187–L188): opinion; depends on the distribution of moves and the prices paid. Not backtested here.
- **"Only a 1% chance"** of NFLX going from $93 to $130 (L221): illustrative, no source.
- **"Risk-to-reward and probability of success are directly tied"** (L238): they are linked (higher probability ↔
  worse reward:risk at fair prices), which also means a high win rate alone is not an edge.
- **Covered call "adds absolutely no risk to your portfolio"** (L143–L144): relative to already holding the stock;
  the stock's downside remains and upside is capped.
- **"Very little capital"** for short verticals (L214): the capital requirement equals the max loss (L234–L235), e.g.
  $320 to make $180.
- AAPL covered stock "buying power effect a little over $3,000" vs max loss $11,528 (L154–L155): depends on the
  account's margin type; not explained.
