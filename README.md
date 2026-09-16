# TradeMind AI

A personal stock research app: live quotes, a 30-day price chart with moving
averages, a BUY/SELL/HOLD signal (SMA5/SMA20 trend + RSI14) with its own
historical win rate, a backtest of that signal against the last 30 days, an
actual ML model (logistic regression, trained fresh per symbol) predicting
tomorrow's direction with honest held-out accuracy, a persistent watchlist,
symbol autocomplete, and recent news for the searched symbol.

## Stack

- **Backend**: FastAPI (Python), SQLite for the watchlist, an in-memory cache
  for Alpha Vantage responses.
- **Frontend**: Next.js (App Router) + Recharts, single page at
  `frontend/app/page.tsx`.
- **Data sources**: [Finnhub](https://finnhub.io) for live quotes, symbol
  search, and news; [Alpha Vantage](https://www.alphavantage.co) for daily
  historical prices (free tier: 25 requests/day, so responses are cached for
  12 hours since daily bars only change once a day).

## Setup

1. Get a free API key from [Finnhub](https://finnhub.io/register) and from
   [Alpha Vantage](https://www.alphavantage.co/support/#api-key).
2. Create `backend/.env`:
   ```
   FINNHUB_API_KEY=your_finnhub_key
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
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
| `GET /ai/predict/{symbol}` | Trains a logistic regression on the symbol's own ~100-day price history (`backend/ai_signal.py`) and predicts the probability tomorrow's close is higher, with accuracy on held-out days |
| `GET /news/{symbol}` | Last 7 days of headlines |
| `GET /symbols/search?q=` | Ticker/company name autocomplete |
| `GET /watchlist/quotes` | Batched quote + signal for every saved symbol |
| `POST /watchlist/{symbol}`, `DELETE /watchlist/{symbol}` | Add/remove a symbol from the watchlist |

## Notes

- The BUY/SELL/HOLD signal is a hand-written rule (SMA trend + RSI + today's
  price move), not a trained model - the backtest exists so you can see how
  it's actually performed rather than trusting it blindly.
- `/ai/predict` is the actual ML piece: a `LogisticRegression` trained from
  scratch on each symbol's own price history every time it's called (fast -
  under 100 rows, a few features). Its held-out accuracy usually lands close
  to a coin flip, which is realistic for daily-bar technical features alone;
  it's shown alongside the prediction rather than hidden, on purpose.
- Alpha Vantage's free tier is the tightest constraint (25 requests/day, and
  `outputsize=full` is a paid-only feature - `compact` tops out around 100
  daily bars). One fetch per symbol serves the chart/signal/backtest (last 30
  days) and the AI predictor (all ~100), cached for 12 hours in both memory
  and `database/trademind.db`, so normal use stays well under quota even
  across backend restarts.
