# Crypto city: archived for a separate city later

On 2026-10-21 the owner asked for this city to trade **options only**, and to keep the crypto work for a separate
crypto city later. Everything crypto was removed from the code. The last commit that still has all of it is
**`7a28e85`** on branch `claude/blissful-ride-nikmtn`. Nothing is lost: any file can be brought back with

```bash
git show 7a28e85:<path>                  # read it
git checkout 7a28e85 -- <path>           # restore it into a working tree (best in a new repo or branch)
```

## What there was

| Piece | Where (at 7a28e85) | What it did |
|---|---|---|
| Config | `config.crypto.yaml` | BTC/USD, ETH/USD, SOL/USD workers; dashboard :8766; `data/scalpcity-crypto.db` |
| Launcher | `Start Crypto City.command` | Double-click start for the crypto bots (Alpaca paper) |
| Market switch | `core/calendar.py` (`set_market`, `is_crypto`, `MARKETS`) | Crypto days run every day, 00:00–24:00 ET |
| Config field | `core/config.py` (`market: options\|crypto`, `sim.crypto_half_spread_pct`, `sim.crypto_fee_pct`) | Picks the market; modeled spread and Alpaca's 0.25% taker fee |
| Instrument | `core/events.py` (`CryptoAsset`, `is_crypto_symbol`) | A coin bought outright: multiplier 1, fractional qty, long only |
| Costs | `core/costs.py` (crypto branches of `fees`, `round_qty`, `fmt_qty`) | % fee of the fill value; 6-decimal quantities |
| Data | `data/alpaca_data.py` (`_crypto_bars`, `crypto_quote`, `AlpacaCryptoStream`), `data/daily.py`, `data/bars.py` (`fill_gaps`) | Coin minute/daily bars, quotes, a quote-midpoint stream (Alpaca's crypto trades are too sparse for candles), flat bars for quiet minutes |
| Price feed | `bots/price_feed_bot.py` | Used the crypto stream when `market: crypto` |
| Options chain bot | `bots/options_chain_bot.py` (`crypto_quote`, crypto spread in the sim) | Coin quotes in place of option chains |
| Contract selector | `bots/decision_bots.py` | Took the coin quote instead of picking a contract; crypto buying power (non-marginable) in the risk manager; no PDT guard |
| Signal filter | `bots/signal_filter_bot.py` (`LONG_ONLY`) | PUT signals were refused (Alpaca can't short crypto) |
| Execution | `bots/execution_bots.py` | Exit limits walked down 0.05% per try; reconciliation allowed 2% on fractional holdings (fee taken in coin) |
| Broker | `brokers/alpaca.py`, `brokers/base.py` | GTC fractional orders; sold what was really held on a full exit; read crypto positions |
| Dashboard | `bots/dashboard_bot.py`, `dashboard/app.js` | `market` in the state; "long only" text and coin labels |
| Tests | `tests/test_crypto_and_expiries.py`, `tests/conftest.py` | Crypto calendar, long-only week, fee shortfall, order format, quote stream (the expiry tests moved to `tests/test_expiries.py`) |
| Docs | `README.md`, `CLAUDE.md`, `.claude/skills/run-scalpcity/SKILL.md` | How to run it, and its known limits |

## What it showed (keep in mind for the new city)
- **It lost money in every backtest.** Alpaca crypto bars, 2026-10-01 to 10-15, the shipped `config.crypto.yaml`:
  344 trades, 2.3% wins, −$2,765, no green days. The ~0.25% fee per side means a trade must move about 0.5% just to
  break even.
- Crypto "VWAP" had no real volume: Alpaca's crypto venue is thin, so candles came from quote midpoints.
- The TJR and research bots were never tested on crypto.

## Your Alpaca paper account
At the switch, the paper account still held about **0.0029 BTC** from an earlier crypto run. The options city
ignores it (it only reconciles option positions). You can sell it on Alpaca's paper site whenever you like; it
doesn't affect the options bots.
