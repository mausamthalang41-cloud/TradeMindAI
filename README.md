# TradeMind AI

A personal stock research app: live quotes, a 30-day price chart with moving
averages, a BUY/SELL/HOLD signal (SMA5/SMA20 trend + RSI14) with its own
historical win rate, a backtest of that signal against the last 30 days, an
actual ML model (logistic regression, trained fresh per symbol) predicting
tomorrow's direction with honest held-out accuracy, a persistent watchlist,
symbol autocomplete, and recent news for the searched symbol.

## Stack

- **Backend**: FastAPI (Python), SQLite for the watchlist, an in-memory +
  on-disk cache for historical price data.
- **Frontend**: Next.js (App Router) + Recharts, single page at
  `frontend/app/page.tsx`.
- **Data sources**: [Finnhub](https://finnhub.io) for live quotes, symbol
  search, and news; [Yahoo Finance](https://finance.yahoo.com) (via
  `yfinance`) for ~2 years of daily historical prices - no API key, no rate
  limit to manage. Cached 12h per symbol regardless, since daily bars only
  change once a day.

## Setup

1. Get a free API key from [Finnhub](https://finnhub.io/register).
2. Create `backend/.env`:
   ```
   FINNHUB_API_KEY=your_finnhub_key
   ```
3. Backend:
   ```
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
4. Frontend (separate terminal):
   ```
   cd frontend
   npm install
   npm run dev
   ```
5. Open http://localhost:3000 (backend runs on http://127.0.0.1:8000).

## Tests

Backend logic (RSI, signal scoring, backtesting, news formatting) has unit
tests with no network calls required:

```
cd backend
source venv/bin/activate
python -m pytest
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /stock/{symbol}` | Live quote + BUY/SELL/HOLD signal, reason, and historical win rate |
| `GET /history/{symbol}` | 30-day OHLCV with SMA5/SMA20 |
| `GET /backtest/{symbol}` | Replays the signal logic day-by-day and reports occurrences/avg return/win rate per signal, plus a buy-and-hold baseline |
| `GET /ai/predict/{symbol}` | Trains a logistic regression on the symbol's own ~2-year price history (`backend/ai_signal.py`) and predicts the probability tomorrow's close is higher, with accuracy (and a majority-class baseline for comparison) on held-out days |
| `GET /ai/backtest/{symbol}` | Rule signal + walk-forward-retrained AI prediction for each of the last ~150 days (no lookahead - the model is retrained fresh at every step). Raw material for replaying a trading strategy's own decision logic against history; see `trading-survival/stock-bot/backtest.py` for a real consumer of this |
| `GET /news/{symbol}` | Last 7 days of headlines |
| `GET /symbols/search?q=` | Ticker/company name autocomplete |
| `GET /watchlist/quotes` | Batched quote + signal for every saved symbol |
| `POST /watchlist/{symbol}`, `DELETE /watchlist/{symbol}` | Add/remove a symbol from the watchlist |

## Notes

- The BUY/SELL/HOLD signal is a hand-written rule (SMA trend + RSI + today's
  price move), not a trained model - the backtest exists so you can see how
  it's actually performed rather than trusting it blindly.
- `/ai/predict` is the actual ML piece: a `LogisticRegressionCV` trained
  from scratch on each symbol's own price history every time it's called
  (fast - ~80ms even on ~500 rows - 7 technical features: SMA trend, RSI,
  MACD, 5/10-day momentum, volume ratio). It also reports what a trivial
  "always guess the more common outcome" baseline would have scored on the
  same held-out days (`baseline_accuracy`), shown next to the model's own
  accuracy - on individual symbols tested it's landed anywhere from clearly
  beating that baseline to clearly losing to it, which is itself the honest
  finding: no consistent edge, shown in the UI on purpose rather than
  hidden behind a confident-looking number.
- Originally built on Alpha Vantage, which capped free-tier history at
  ~100 days and 25 requests/day. Switched to `yfinance` (Yahoo Finance,
  keyless, ~2 years of history, no daily cap) once that data ceiling
  turned out to be the actual bottleneck on the AI model's training set
  size (and on how many days `/ai/backtest` could honestly evaluate).
  One fetch per symbol serves the chart/signal/backtest (last 30 days) and
  the AI predictor (the full ~2 years), cached 12h in both memory and
  `database/trademind.db`.
- `trading-survival/stock-bot` (a separate sibling project) consumes
  `/ai/backtest` to replay its own combined rule+AI strategy against real
  history using its actual decision code, not a reimplementation of it -
  see that repo's README for the (currently unconvincing) results.
