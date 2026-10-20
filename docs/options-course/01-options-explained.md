# Part 1: Options Explained (what an option is, insurance, leverage)
Source: SkyView Trading options playlist, video 1 (https://www.youtube.com/watch?v=4HMm6mBvGKE). Read in full from the
auto-captions on 2026-10-20.

## What an option is
- A contract that gives the buyer the **right, not the obligation**, to buy (**call**) or sell (**put**) 100 shares at
  the **strike price** on or before the **expiration date**.
- The buyer pays a **premium** for that right. The **seller** collects the premium and takes on the obligation.
- You don't have to exercise. Most traders simply **buy the option and sell it back** before expiration.

## Why options exist: insurance (buying a put)
Example: 100 shares bought at $125 ($12,500). A 125 put bought for $500 works like an insurance policy.
| Stock at expiration | Stock alone | Stock + put | Put seller |
|---|---|---|---|
| $132 | +$700 | +$200 (the $500 premium is the cost of the insurance) | +$500 |
| $113 | −$1,200 | −$500 (the loss stops at the premium) | −$700 |

## Why buy a call: leverage with less capital
Example: instead of $12,500 of stock, a 125 call for $500.
| Stock at expiration | 100 shares | 125 call |
|---|---|---|
| $137 | +$1,200 | +$1,200 − $500 = **+$700** on $500 |
| $100 | −$2,500 | **−$500** (the most a buyer can lose) |

A put bought without owning the stock is a bearish bet: it gains when the stock falls.

## The warning that ends the video
"Before you go out and start buying calls … there are big negatives to buying options like this." The rest of the
course explains them: the stock has to move past the **break-even** (strike + premium for a call), **fast enough** to
beat **time decay**, and a fall in **implied volatility** can erase a correct call on direction.

## For the bots
- Already true: the towers only **buy** calls and puts, so the most a trade can lose is the premium paid
  (sizing then keeps that loss near `sizing.risk` at the chart stop).
- They never hold to exercise: every position is sold back before the 15:55 flatten.
- The "big negatives" are why the contract scout prices time decay and the spread into every pick (Parts 3–5).
