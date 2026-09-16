import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


load_dotenv(Path(__file__).with_name(".env"))
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "trademind.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(DB_PATH) as connection:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            added_at TEXT NOT NULL
        )
        """
    )

app = FastAPI(
    title="TradeMind AI API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "app": "TradeMind AI",
        "status": "Running",
        "data_source": "Finnhub",
    }


@app.post("/watchlist/{symbol}")
def add_to_watchlist(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO watchlist (symbol, added_at) VALUES (?, ?)",
            (clean_symbol, datetime.now(timezone.utc).isoformat()),
        )

    return {"symbol": clean_symbol, "watchlisted": True}


@app.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    clean_symbol = symbol.strip().upper()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("DELETE FROM watchlist WHERE symbol = ?", (clean_symbol,))

    return {"symbol": clean_symbol, "watchlisted": False}


@app.get("/watchlist/quotes")
async def get_watchlist_quotes():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT symbol FROM watchlist ORDER BY added_at"
        ).fetchall()

    quotes = []

    for (symbol,) in rows:
        try:
            quotes.append(await get_stock_data(symbol))
        except HTTPException as error:
            quotes.append({"symbol": symbol, "error": error.detail})

    return {"quotes": quotes}


@app.get("/stock/{symbol}")
async def stock(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

    return await get_stock_data(clean_symbol)


async def get_stock_data(clean_symbol: str):
    if not FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="Finnhub API key is missing.")

    url = "https://finnhub.io/api/v1/quote"
    parameters = {
        "symbol": clean_symbol,
        "token": FINNHUB_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=parameters)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Could not contact the stock-data service.",
        )

    current_price = data.get("c", 0)
    price_change = data.get("d", 0)
    percentage_change = data.get("dp", 0)

    if current_price == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for {clean_symbol}.",
        )

    sma5 = None
    sma20 = None
    rsi = None

    try:
        closes = [point["close"] for point in await fetch_daily_series(clean_symbol)]
        if len(closes) >= 5:
            sma5 = round(sum(closes[-5:]) / 5, 2)
        if len(closes) >= 20:
            sma20 = round(sum(closes[-20:]) / 20, 2)
        rsi = calculate_rsi(closes)
    except HTTPException:
        pass

    signal, signal_reason = determine_signal(percentage_change, sma5, sma20, rsi)

    return {
        "symbol": clean_symbol,
        "price": round(current_price, 2),
        "change": f"{percentage_change:+.2f}%",
        "price_change": round(price_change, 2),
        "previous_close": round(data.get("pc", 0), 2),
        "signal": signal,
        "signal_reason": signal_reason,
        "rsi": rsi,
    }


_series_cache: dict[str, tuple[float, list]] = {}
_SERIES_CACHE_TTL_SECONDS = 60


async def fetch_daily_series(clean_symbol: str):
    cached = _series_cache.get(clean_symbol)
    if cached and time.monotonic() - cached[0] < _SERIES_CACHE_TTL_SECONDS:
        return cached[1]

    if not ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key is missing.",
        )

    url = "https://www.alphavantage.co/query"
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": clean_symbol,
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=parameters)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Could not contact the historical-data service.",
        )

    if "Error Message" in data:
        raise HTTPException(
            status_code=404,
            detail=f"No historical data found for {clean_symbol}.",
        )

    if "Note" in data or "Information" in data:
        message = data.get("Note") or data.get("Information")
        raise HTTPException(status_code=429, detail=message)

    daily_prices = data.get("Time Series (Daily)")

    if not daily_prices:
        raise HTTPException(
            status_code=404,
            detail=f"No historical data found for {clean_symbol}.",
        )

    series = []

    for date, values in list(daily_prices.items())[:30]:
        series.append(
            {
                "date": date,
                "open": round(float(values["1. open"]), 2),
                "high": round(float(values["2. high"]), 2),
                "low": round(float(values["3. low"]), 2),
                "close": round(float(values["4. close"]), 2),
                "volume": int(values["5. volume"]),
            }
        )

    series.reverse()
    _series_cache[clean_symbol] = (time.monotonic(), series)
    return series


def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None

    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    relative_strength = avg_gain / avg_loss
    return round(100 - (100 / (1 + relative_strength)), 2)


def determine_signal(percentage_change, sma5, sma20, rsi):
    score = 0
    reasons = []

    if sma5 is not None and sma20 is not None:
        if sma5 > sma20:
            score += 1
            reasons.append("5-day average is above the 20-day average")
        elif sma5 < sma20:
            score -= 1
            reasons.append("5-day average is below the 20-day average")

    if rsi is not None:
        if rsi < 30:
            score += 1
            reasons.append(f"RSI of {rsi} is oversold")
        elif rsi > 70:
            score -= 1
            reasons.append(f"RSI of {rsi} is overbought")

    if percentage_change > 0:
        score += 0.5
    elif percentage_change < 0:
        score -= 0.5

    if not reasons:
        reasons.append("Based on today's price move only")

    if score > 0:
        signal = "BUY"
    elif score < 0:
        signal = "SELL"
    else:
        signal = "HOLD"

    return signal, " · ".join(reasons)


@app.get("/history/{symbol}")
async def stock_history(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

    history = await fetch_daily_series(clean_symbol)

    for index, point in enumerate(history):
        if index >= 4:
            last_5_closes = [
                history[position]["close"]
                for position in range(index - 4, index + 1)
            ]
            point["sma5"] = round(sum(last_5_closes) / 5, 2)
        else:
            point["sma5"] = None

        if index >= 19:
            last_20_closes = [
                history[position]["close"]
                for position in range(index - 19, index + 1)
            ]
            point["sma20"] = round(sum(last_20_closes) / 20, 2)
        else:
            point["sma20"] = None

    return {
        "symbol": clean_symbol,
        "history": history,
    }