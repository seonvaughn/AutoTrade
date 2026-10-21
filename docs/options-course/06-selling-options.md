# Part 6: How to Sell Options (short call, short put)
Source: SkyView Trading options playlist, video 6 (https://www.youtube.com/watch?v=2Vqz9GXkr5I). Read in full from the
transcript the owner pasted on 2026-10-21. The same material appears in the 4-hour course (notes-4h-q2/q3).

## The idea
- **Selling an option to open** ("being short") is a bet that the option is overpriced and will lose value: sell it
  high, buy it back lower, or let it expire worthless.
- **A short put is like selling insurance:** if the stock crashes and the buyer exercises, you must buy their shares
  at the strike. You want the stock to stay **above** the strike (bullish to neutral).
- **A short call** wants the stock to stay **below** the strike (bearish to neutral).
- "Rather than betting where the stock will go we are betting where the stock won't go."

## The example (Facebook at ~$117, 125 call sold for $1.02, 46 days)
| Stock at expiry | Option worth | Result |
|---|---|---|
| $122 (anything under 125) | 0 | **+$102**, the most it can make |
| $128 | 3.00 (intrinsic) | **−$198** |
| higher | rises without limit | loss grows without limit ("undefined") |

## Picking the strike
- **Delta ≈ the chance of finishing in the money.** A 0.12-delta call has about a 12% chance of the stock finishing
  above its strike, so about an 88% chance it expires worthless. thinkorswim's "probability out of the money"
  column shows the same thing.
- Further out of the money = higher chance of profit but a smaller premium (the 101 call paid only $0.15).
- "There really is no magic number": they took the 99 call on CAT with an 84% chance of staying out of the money.

## The live trades (11 days to expiry: they broke their own 30–60 day rule)
| Trade | Sold | Outcome |
|---|---|---|
| CAT 99 call (stock ~$95) | $0.35 | Expired worthless: **+$35** |
| GDX 20 put (67% chance OTM) | $0.37 | GDX fell through 20; bought back at $0.78: **−$41** |
| AAPL, QQQ, DIA (off camera) | – | All profitable |

- **Gamma risk:** as GDX fell, the short put's delta grew from +26 to +70 (the most it can reach is 100 for one
  contract). Time decay in your favour always comes with gamma against you. Keep size small, and prefer 30–60 days to
  expiry, where gamma is lower.
- **Expiration:** an out-of-the-money short can expire (no closing fee). An in-the-money short must be closed before
  the close, or it turns into stock (the GDX put would have become 100 shares at $20).
- **Orders:** sell at the highest price you can; when buying back, start at the bid and step toward the ask
  (filled at 0.78 with the market at 0.76 × 0.79).
- **Capital:** check the buying power effect before every short. The CAT call tied up about $1,500 (short expiry);
  the GDX put about $329.

## The recap
| | Short call | Short put |
|---|---|---|
| View | bearish to neutral | bullish to neutral |
| Max profit | the premium | the premium |
| Max loss | undefined | strike − premium (the stock can only fall to 0): $1,965 on the GDX put |
| Break-even | strike + premium | strike − premium |
| Helped by | time decay, a fall in IV | time decay, a fall in IV |

## Claims to check (their words, not evidence)
- "4 of 5 winners shows how powerful a high-probability strategy is": five trades, chosen from several takes, prove
  nothing. Their one loss (−$41) was bigger than a typical win (+$35). That's the same lesson as this repo's
  backtests: **a high win rate isn't an edge if the losses are bigger than the wins.**
- "The theoretical risk is much higher than the actual risk": opinion. A gap through the strike can lose many times
  the premium in one day.
- The presenters sell a course.

## For the bots
- Nothing to build: the towers only **buy** calls and puts and never sell to open. Selling premium (unlimited or large
  losses, margin, assignment) is a different business that needs the owner's decision and its own tests
  (README "Not adopted").
- What carries over, already in place:
  - delta as the chance of finishing in the money (shown with every pick);
  - never hold an in-the-money option through expiration (the 15:55 flatten);
  - limit orders that step toward the market (entries mid → ask, exits walk down from the bid);
  - win rate *and* payoff, never win rate alone.
