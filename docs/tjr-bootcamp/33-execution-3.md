# Day 33: Execution Pt 3 (sweep + BOS + FVG, and adding equilibrium)
Source: https://www.youtube.com/watch?v=K8DwhtmvAW8 (24 min). Read in full from the transcript the owner pasted
(the YouTube download was blocked from the cloud server).

Opening motto: "I did that. Well, don't do it again" (the same idea as Days 11 and 15: learn from each mistake once).
Most of the first 6 minutes is off-topic.

## Model 3: liquidity sweep + break of structure + fair value gap
- **S&P example:** he didn't trade it because Powell was speaking, but it was a decent setup.
  1. Lows taken (sweep).
  2. **15m BOS up**, which left an imbalance.
  3. Price retraced into the FVG: an **FVG entry, not an order-block entry**. There was also a second, higher
     imbalance.
  4. "**Scale down to a lower timeframe to find confirmation**": a lower-timeframe BOS. Stop under the lows (the
     sweep).
  5. Price then ran ("capitulates").
- **Sweep inside the retrace:** liquidity taken, BOS up, imbalance. Price came down, **also swept 15m liquidity on the
  way into the FVG**, filled it and rallied, targeting the previous liquidity one pool after another.
- **An FVG that price runs straight through is discarded** ("goes all the way past it, get rid of it"). The next
  imbalance is used instead.
- **Waiting for the reaction:** price fills the imbalance, then "some sort of reaction on a lower timeframe": a **15m BOS
  up (a candle closes above), then execute**. Targets are the previous draws on liquidity, then the higher-timeframe
  highs.
- **On the hourly:** price may fill one imbalance completely without reaching the next FVG, then target the previous
  liquidity (an order block and lows below).
- **He also shows a BOS + FVG with no clear sweep that worked:** a BOS up, an imbalance, price fills it and rallies.
  Another: "this move down was a liquidity sweep… that's an order block", then the order block reacts, BOS up, a new
  imbalance, fill, rally. The sweep is part of the model, but he points out the FVG reaction appearing in these too.
- **Combinations:** an FVG gets filled with a slight reaction, then price comes into the order block below and reacts.
  Each zone gets its chance in turn.

## Model 4: + equilibrium
- "Literally the same thing": sweep + BOS + FVG or OB, with **equilibrium drawn on top**.
- **When to draw it:** "as soon as I see a retracement candle (a down candle in an uptrend), I'm instantly looking for
  equilibrium." Measure from the swing low to the swing high (bullish), or swing high to swing low (bearish).
- **An FVG that lines up with equilibrium is "a high-confluence trade".**
- **Daily example:** sweep of lows, rally, a close above (BOS). The first bearish daily candle is the cue to draw
  equilibrium from the low to the high. The imbalance sits at equilibrium.
- **Equilibrium and FVGs are "our last-chance entries":** when you missed the BOS entry or the order-block entry, the
  FVG and equilibrium still give one.
- **Stacked-confluence example:**
  1. Sweep and BOS. The whole leg is an order block.
  2. To get more precise inside it: price **wicks into equilibrium**, into the **5m order block**, and into the
     **5m FVG**.
  3. Then a BOS.
  - He calls each one a confluence (1, 2, 3, 4, then the break). Many confluences together are what gives the
    confidence to take the trade.

## Daily bias (preview of Days 34–36)
- A lower-timeframe sweep + BOS **not in line with the daily bias** gives a short-lived move. It "might not hit your
  first take profit".

## Homework (his)
- 10 examples of sweep + BOS + FVG with the reaction that followed.
- 10 examples of sweep + BOS + (OB or FVG) + equilibrium.

## For the bots
- **This confirms the `smc_retrace` design:**
  1. Setup on the setup timeframe: a sweep, then a body-close BOS.
  2. Draw equilibrium on the leg (re-anchored as the leg extends).
  3. Wait for price to retrace into the discount or premium half **and** into an order block or unfilled FVG of that
     leg. Lower-timeframe FVGs (1m) count too.
  4. Then a lower-timeframe BOS in the trade direction gives the entry.
  5. Stop beyond the sweep. Targets at liquidity.
- **Drop an FVG once price closes through its far side,** and move on to the next zone (an order block further back).
  A setup stays alive until price closes beyond the swept extreme.
- **A sweep during the retrace** (e.g. a 15m low taken while going into the FVG) adds to the setup. It isn't needed.
- **BOS + FVG without a sweep:** he shows it working but teaches the sweep as part of the model. The bots keep the
  sweep required, and score a `require_sweep: false` variant separately before ever relying on it.
- **Daily bias stays a hard requirement**, as here and on Days 34 and 44.
