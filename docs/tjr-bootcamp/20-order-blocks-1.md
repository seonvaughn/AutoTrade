# Day 20: Order Blocks Pt 1 (what they are)
Source: https://www.youtube.com/watch?v=qhuFg_OXdmE (13 min). Read in full from the transcript.

## Concepts
- **An order block is the leg that caused a liquidity sweep.**
  - For a bearish setup, the order block is the move *up* that took out the high, just before the BOS down.
  - For a bullish setup, it is the move *down* that took out the low, just before the BOS up.
  - Orders were filled in that price range. When price retraces into it, market makers fill more orders there and
    push price on in the new direction.
- **Ranking of entries:**
  1. The sweep plus BOS is "the top of the entry".
  2. If that's missed, there are three retracement re-entries. In his order of priority: order block, then FVG,
     then equilibrium.
  - The order block comes first because it is still at the top of the move. It can even give a better price than the
    BOS entry, since the swept extreme is the start of the order block.
- **One order block per trend.** It forms at the trend shift (sweep, then BOS). Later pullbacks in the same trend are
  FVGs or equilibrium, not new order blocks. A new order block appears only at the next trend shift.
- They exist on every timeframe and show up on the 1m every day. He also calls them "accumulation areas": "same
  thing, different terminology".
- How to spot them: Day 22 (transcript not available) and Day 23 (putting it together).
- Aside: on a PPI and FOMC day, GBPJPY had moved only 34 pips on the 15m since the US open. Chop like that is why
  he doesn't trade those days.

## For the bots
- **Order-block marking:** when a sweep is followed by a BOS, record the order block as the price range of the leg
  that ran into the swept level (from the start of that leg to the swept extreme). Hold one order block per
  symbol, timeframe and trend, and replace it at the next trend shift.
- **Order-block retest entry:** in the new trend, price retraces into the order block, then a lower-timeframe BOS in
  the trend direction gives the entry. The stop goes beyond the swept extreme. It ranks ahead of the FVG retest.
