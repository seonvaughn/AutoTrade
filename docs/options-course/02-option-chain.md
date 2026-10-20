# Part 2: Options Trading Explained (option chain, pricing basics)
Source: https://www.youtube.com/watch?v=1fMAjyC5lZ8 (11 min). Read in full from the transcript.

## Concepts
- **Option chain:** the list of every option you can trade on a ticker, with prices. It's in your broker's platform
  (also Yahoo/Google Finance). If a ticker has no options, the platform says "no options available for this symbol".
- **Choosing an option = choosing an expiration and a strike.**
  - The expiration list shows the date and the **days left to expiration** (e.g. 11 days).
  - Calls are on the left and puts on the right. Strikes are listed in the centre.
  - Which expiration and strike to choose is taught later. Each choice has pros and cons.
- **Bid and ask:** buy at the **ask** (where the sellers are), sell at the **bid** (where buyers will take it).
- **One contract controls 100 shares**, so option prices have a **×100 multiplier**. Example: AAPL 385 call, bid
  2.76, ask 2.81. Buying one costs $281, and two cost $562.
- **You don't have to exercise. You can just trade the option's price.** Example: buy one at 2.81 ($281), sell later
  at 4.00 ($400): +$119. Two contracts: $562 → $800, +$238.
- **Three things move an option's price.** The first is the underlying stock price: calls tend to rise when the stock
  rises, and puts when it falls. The other two (taught in Part 3) are "extremely important, so don't go buying options
  yet".

## For the bots
- Already built in: contracts use `contract.multiplier` (100), buys fill at the ask and sells at the bid (sim and
  live), and the chain is read per expiry and strike (`contract_selector`).
- Nothing new to codify.
