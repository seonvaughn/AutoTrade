# Part 5: How to Buy Options (long call, long put)
Source: https://www.youtube.com/watch?v=BsnsI4JK76A (21 min). Read in full from the transcript.

## Why buy a call instead of the stock: leverage
- **Example:** TLT at about 122, calls at 31 DTE (mid prices): 121 call 2.64, 122 call 2.10, 123 call 1.68, and so on.
- **If TLT goes to 130:**
  - The stock makes +6.6%.
  - The 121 call is worth its intrinsic value of 9: +$636 on $264, **+240.9%**.
  - The 125 call goes from about $97 to $500, **over +400%**.

## Strike choice: payout vs probability
- **Further OTM:** cheaper, with a bigger percentage payout, but a **worse breakeven and a lower probability of profit
  (POP)**.
- **Further ITM:** costs more, with a smaller percentage payout, a **better POP**, and **less time decay** (more
  intrinsic, less extrinsic value).
- **Breakevens:**
  - Long call = strike + premium. Example: 121 + 2.64 = 123.64.
  - Long put = strike − premium.
  - The stock must be past the breakeven at expiration to profit.

## Expiration choice (from the Greeks)
- **Short-dated (4 DTE):** much higher theta (decay hurts more) but higher gamma (faster profits if right). "Much less
  room for error if we don't time the entry perfectly."
- **Long-dated (60 DTE):** lower theta, lower gamma.
- **Their middle ground: about 25 DTE, at the money.**

## Walk-through (thinkorswim)
- Example: FB 122 call at 2.62. Cost $262 + commission = $263.
- **Risk on a long option = the premium paid** (it can't go below zero). The buying-power effect is the same $263.
- **Max profit:** a call's is "infinite", which they say is better described as "undefined". A put's is large but
  limited.
- **Breakeven:** 122 + 2.62 = 124.62.
- **Risk profile:** a flat max loss below the strike, rising above it.
- **POP is the probability the stock finishes beyond the breakeven: 34.57% here** (65.43% chance of a loss).
- "**When buying an option you will never have a probability of profit better than 50%.**"

## Long put
- The same mechanics, bearish. Time decay is against you, and you benefit from IV rising. Breakeven = strike −
  premium. Loses the whole premium if the stock is above the strike at expiration.

## Expiration handling
- **Close in-the-money long options before expiration.** Otherwise an ITM call becomes long stock and an ITM put
  becomes short stock, which needs much more capital.
- Holding an ITM call into stock is the same P&L as selling the call and buying stock ("pricing is always fair").
- **OTM options can be left to expire worthless;** they won't turn into stock.

## For the bots
- **Already in place:**
  - Risk per trade is the premium at most, and sizing caps the dollars at the chart stop.
  - Contracts are 1+ days out at about 0.70 delta or chosen by the scout (higher POP, less decay, as the course says
    ITM options give).
  - Everything is flattened at 15:55, so no long option is ever held into expiration or assignment.
- **New, from this part:**
  - **Breakeven / POP awareness in the contract scout:** the scout already requires a profit at the plan's target
    after decay and spread. That's a stricter, trade-specific version of "the stock must clear the breakeven".
  - **A hard rule: never let a long option expire in the money.** It's already true for intraday trades because of the
    15:55 flatten. Keep it true if longer holds are ever added.
  - **Never buy far OTM "lottery" options:** the scout ignores deltas below 0.30.
- **Their own warning bears repeating:** a long option's POP is below 50%. A high win rate doesn't come from buying
  options; it has to come from the setup reaching its target before the stop.
