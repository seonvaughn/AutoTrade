# The futures city (MES, MNQ, MGC on Interactive Brokers paper)

A second city next to the options city. It runs the same bots and rules on three micro futures, in the New York
session only:

| Tower | Contract | $ per point | Tick | Roll |
|---|---|---|---|---|
| MES | Micro E-mini S&P 500 | $5 | 0.25 ($1.25) | 8 days before the quarterly expiry (3rd Friday of Mar/Jun/Sep/Dec) |
| MNQ | Micro E-mini Nasdaq-100 | $2 | 0.25 ($0.50) | same |
| MGC | Micro Gold | $10 | 0.10 ($1.00) | the 15th of the month before (Feb/Apr/Jun/Aug/Oct/Dec contracts) |

- **What's the same as the options city:**
  - TJR's model (`smc_retrace`) and the opening-range retest (`orb_ntz_retest`).
  - The 07:00 morning study, the research gate, the lessons book and trade reviews.
  - Sessions: 09:35–11:00, plus 13:00–15:30 only if the morning had no trade.
  - At most 2 trades a day, $300 risk each.
  - The $900 daily loss limit and kill switch, the 15:55 flatten (nothing held overnight) and the stale-data pause.
- **What's different:**
  - **Long or short.** A bullish setup buys the future; a bearish one sells it short (no options).
  - **Sizing in points.** Contracts = $300 ÷ (stop distance in points × $ per point). If one contract would risk more
    than $300 (a wide stop on MNQ or MGC), the trade is skipped.
  - **Margin, not premium.** Each contract sets aside margin (about $2,700 MES, $3,500 MNQ, $3,000 MGC; the broker's
    figure counts). The towers together stay under `risk.max_premium_exposure` ($15,000).
  - The pattern-day-trader rule doesn't apply to futures.
  - **Its own** database (`data/scalpcity-futures.db`), lessons book (`data/lessons-futures.json`) and city
    (http://127.0.0.1:8767).

## Safety
- Paper only. `config.futures.yaml` refuses live mode.
- The bots refuse Interactive Brokers' live ports (4001, 7496).
- After connecting, they refuse any login whose account isn't a paper account (paper ids start with "DU").

## One-time setup on the Mac
1. **An Interactive Brokers account with paper trading.** Every IBKR account comes with a paper account (a
   separate username, shown in Client Portal → Settings → Paper Trading Account). Futures trading must be enabled
   on the account (Settings → Trading Permissions → Futures, US).
2. **Market data for CME/COMEX.**
   - Real-time futures prices need a market-data subscription on the live account. Paper accounts share it once
     you enable sharing (Client Portal → Settings → Paper Trading Account → share market data).
   - Without it IBKR sends no live prices, and the bots pause on stale data.
   - The non-professional CME/COMEX bundles are a few dollars a month. Check IBKR's current price list.
3. **IB Gateway** (the small "stable" version) from interactivebrokers.com, then log in with the **paper**
   username. In Configure → Settings → API → Settings:
   - turn on "Enable ActiveX and Socket Clients";
   - set the socket port to **4002**;
   - turn **off** "Read-Only API";
   - make sure "Allow connections from localhost only" stays on.
4. **Start the city:** double-click **Start Futures City.command**. The first start installs `ib_async` and fetches
   about 60 sessions of history (about 40 requests, a few minutes).

Keep IB Gateway running and logged in while the bots run. IBKR logs it out once a day (you choose when in its
settings); log it back in before the session.

## Backtests
- There is no futures history in the cloud, so `data.source: proxy` replays SPY / QQQ / GLD minute bars scaled
  to MES / MNQ / MGC prices (×10, ×41, ×10.85).
- It's an approximation: the real futures trade almost 24 hours and their gap to the ETF drifts over time. GLD
  is the weakest stand-in for gold futures.
- Results show how the rules behave on that price path, not what the futures would have earned.
- See `docs/research-log.md` for the results.
