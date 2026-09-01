# TradeMind AI

TradeMind AI is a simple stock market dashboard. Enter a ticker symbol to see
its live quote, a buy/sell/hold signal, and a 30-day closing-price chart.

## Project structure

- `backend/` — FastAPI service that proxies live quotes from
  [Finnhub](https://finnhub.io) and historical daily prices from
  [Alpha Vantage](https://www.alphavantage.co).
- `frontend/` — Next.js app that queries the backend and renders the quote
  card and price chart.

## Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `backend/.env` file with your API keys:

```
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

Run the API:

```bash
uvicorn main:app --reload
```

The API is served at `http://127.0.0.1:8000`.

- `GET /stock/{symbol}` — live quote and a BUY/SELL/HOLD signal.
- `GET /history/{symbol}` — last 30 days of daily OHLCV data.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser. The frontend expects the
backend to be running at `http://127.0.0.1:8000`.

## Tech stack

- Backend: FastAPI, httpx
- Frontend: Next.js, React, Recharts
