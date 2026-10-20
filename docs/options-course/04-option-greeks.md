# Part 4: Option Greeks Explained
Source: https://www.youtube.com/watch?v=NxBUYBoA0zI (14 min). Read in full from the transcript. The course is by
SkyView Trading. They sell premium (iron condors on SPX) and say so throughout.

**The Greeks measure how sensitive an option's price is to each of the three price factors.** They "help us choose
which strikes and expirations to select" and "help us understand our risk".

| Greek | Meaning | Their example |
|---|---|---|
| **Delta** | Change in the option's price for a +1 point move in the stock. Calls are positive, puts negative. | 123 call, delta 0.47: stock +$1 → option +$0.47, i.e. **+$47 per contract**. |
| **Gamma** | Change in delta for a +1 move. | Gamma 0.05: delta 0.47 → 0.52 after +1. "We don't look at gamma much." |
| **Theta** | Change in the option's price after one day passes, all else equal. Every long option has negative theta. | −0.12 means it loses $0.12 a day if the stock and IV don't change. |
| **Vega** | Change for +1 percentage point of implied volatility. Positive for both calls and puts. | Vega 0.10: IV +1 point → +$0.10. |

- **Delta grows as an option goes deeper in the money** and shrinks out of the money.
- Theta doesn't guarantee tomorrow's price; it isolates time, with the stock and IV unchanged.

## Position Greeks (their SPX iron condor, 10 contracts, up $425)
- **Position delta −8.98:** SPX +1 → −$8.98; SPX −1 → +$8.98. A negative delta means short the market, positive means
  long.
  - **Delta = equivalent shares:** −8.98 is like being short about 9 shares. 100 contracts would be about −80
    (−$80 per point). **Use delta to keep directional exposure in line with risk tolerance** ("a good way, not the
    only way").
- **Position gamma:** SPX +1 moves the delta from −8.98 to −10.57.
- **Position theta +72.63:** the position earns about $72.63 a day from time decay. "All the strategies we use …
  benefit from time decay. Making sure you're on the right side of time decay is extremely important."
- **Position vega −176.78:** IV +1 point → −$176.78; IV −1 point → +$176.78.

## For the bots
- **Already used:** delta (contract choice, and sizing from the chart stop × delta × 100). The contract scout prices
  theta implicitly by repricing at a later time.
- **To add:**
  - **Position delta as exposure:** limit the account's total dollar delta (sum of qty × delta × 100 × stock price)
    as well as premium exposure. The risk manager can check it.
  - **Theta per day, in dollars, as a cost of holding:** show it on each open position in the city, so the cost of
    waiting is visible.
  - **Vega:** IV awareness (see Part 3). A long option loses vega × IV drop. Avoid buying when IV is unusually high for
    the ticker.
