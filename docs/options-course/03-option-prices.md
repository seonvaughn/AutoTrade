# Part 3: Understanding Option Prices
Source: https://www.youtube.com/watch?v=1u4sdf-3twQ (32 min). Read in full from the transcript.

**Three things move an option's price: (1) the stock price, (2) time to expiration, (3) the stock's volatility.**
The course explains all three with an insurance analogy.

## 1. Stock price: moneyness
- **In the money (ITM):** a call with its strike below the stock price, or a put with its strike above it.
  Example: a 120 call with the stock at 125 is worth at least $5. **Out of the money (OTM):** the reverse.
  Example: a 120 call with the stock at 115 is worth nothing at expiration.
- **The deeper in the money, the more expensive** (a bigger discount to buy or sell the stock). Example: TWTR puts at
  28 DTE with the stock at 18: the 18 put costs $1.59 (full cover) and the 16 put $0.75.
- **Calls gain when the stock rises; puts gain when it falls.**
- **At expiration an option is worth only its intrinsic value** (how far in the money it is). OTM options expire
  worthless.
  - Example at 0 DTE with TWTR at 18.09: the 17 call ≈ 1.09, and the 16 call ≈ 2.09 (screen 2.15; the spread is wide
    that deep).

## 2. Time to expiration: time decay
- More time costs more, like insurance by the month: a 60-day option costs more than the same 30-day option.
- **OTM options have value before expiration only because the stock could still move.** The further OTM, the cheaper,
  because it's less likely to pay.
- **Intrinsic value** is the in-the-money part. **Extrinsic (time) value** is everything above it, and it's zero at
  expiration.
  - Example (28 DTE, TWTR 18.09): the 17 call at 2.20 = 1.09 intrinsic + 1.11 extrinsic. If the stock goes
    sideways for 28 days, it decays to 1.09: −$111 with no move at all.
  - **Breakeven at expiration = strike + premium** (17 + 2.20 = 19.20). The stock must rise from 18.09 to 19.20
    just to break even.
- **"Options are constantly decaying as time passes."** Time value decays gradually, so a quick move can still profit
  before expiration. You can close any time before expiration.
- **The course's stance:** "we never buy options as a way to guess direction … we trade them in a way to take
  advantage of this time decay" (selling, taught later). Their least favourite way to trade options is buying
  them.

## 3. Volatility: implied volatility (IV)
- Volatility is the size of a stock's price swings. **High volatility means more expensive options** (riskier
  insurance), just as a smoker pays more for life insurance.
  - Example: EWZ and FXI at almost the same price, both 28 DTE. EWZ's expected move is ±$2.44 and FXI's ±$1.89. The
    37 put costs about 0.85 on EWZ and about 0.54 on FXI, and calls and puts at every strike are dearer on EWZ.
- **IV is implied by option prices** (supply and demand for options), not the other way round. Lots of buyers make
  options dearer and IV rises; lots of sellers make them cheaper and IV falls. **IV is a "fear gauge"**: fear brings
  insurance buying.
- **IV rising makes both calls and puts dearer; IV falling makes them cheaper.**
- "Implied volatility is actually very predictable, whereas stock prices aren't." (Their opinion; it underpins their
  premium-selling.)

## Scenario examples (thinkorswim analysis tool; TWTR 19 call bought at 1.28, 28 DTE)
| Scenario | Option price | P&L |
|---|---|---|
| Only time passes | decays to 0 | −$128 |
| Stock +1 at once | 1.79 | |
| Stock +2 at once | 2.38 | +$110 (more than the stock's move per share: explained by the Greeks) |
| IV +25% only | 1.79 | +$51 |
| 1 week, stock +1.50 | 1.84 | +$56 |
| 3 weeks, stock +1.50 | 1.23 | −$5 (time decay beat a correct direction) |
| 1 week, stock +0.50, IV −10% | 1.12 | −$16 (IV drop + decay beat a correct direction) |
| 3+ weeks, stock flat, IV +25%, 4 DTE left | 0.53 | −$75 |

"In most of these scenarios we lost money, and in most of these scenarios the stock went in our favour." Buying
options needs the stock to move far enough and **fast enough**, and IV not to fall.

## For the bots
- **This supports the evidence already in the project:** long options fight time decay and IV, so a correct
  direction can still lose. Already in place:
  - the contract scout prices time decay over the expected hold, and only picks contracts that still gain at the
    target after the spread;
  - 0DTE is avoided (1+ days out, higher delta);
  - stops and targets are on the stock.
- **New rule to add: IV awareness.** The scout prices at the quote's own IV but assumes IV stays the same. The course
  shows an IV drop can turn a correct move into a loss. The candidate rule is to avoid buying when IV is high relative
  to its own recent range (IV rank). This needs an IV history per ticker, which the bots don't keep yet; see the
  Greeks/IV parts of the 4-hour course notes.
- **The course's main point (sell premium, don't buy direction) is a different business:** selling options has a
  different, tail-heavy risk profile, and the project is built for buying. Noted for the owner; not switched without
  a decision and a separate test.
