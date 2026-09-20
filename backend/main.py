import json
import os
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_signal import train_and_predict
from indicators import calculate_rsi


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
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS series_cache (
            symbol TEXT PRIMARY KEY,
            fetched_at REAL NOT NULL,
            data TEXT NOT NULL
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


def format_news_articles(raw_articles: list, limit: int = 6) -> list:
    articles = [
        {
            "headline": item["headline"],
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "datetime": item.get("datetime", 0),
        }
        for item in raw_articles
        if item.get("headline")
    ]
    articles.sort(key=lambda article: article["datetime"], reverse=True)
    return articles[:limit]


@app.get("/ai/predict/{symbol}")
async def ai_predict(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

    series = await fetch_training_series(clean_symbol)

    try:
        result = train_and_predict(series)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    return {"symbol": clean_symbol, **result}


@app.get("/news/{symbol}")
async def get_company_news(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

    if not FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="Finnhub API key is missing.")

    to_date = date.today()
    from_date = to_date - timedelta(days=7)

    url = "https://finnhub.io/api/v1/company-news"
    parameters = {
        "symbol": clean_symbol,
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
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
            detail="Could not contact the news service.",
        )

    return {"symbol": clean_symbol, "articles": format_news_articles(data)}


@app.get("/symbols/search")
async def search_symbols(q: str = ""):
    clean_query = q.strip()

    if not clean_query:
        return {"results": []}

    if not FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="Finnhub API key is missing.")

    url = "https://finnhub.io/api/v1/search"
    parameters = {"q": clean_query, "token": FINNHUB_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=parameters)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Could not contact the symbol-search service.",
        )

    results = [
        {"symbol": item["symbol"], "description": item.get("description", "")}
        for item in data.get("result", [])
        if item.get("type") == "Common Stock"
    ][:8]

    return {"results": results}


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
    closes = None

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

    signal_win_rate = None
    if closes and len(closes) >= 3:
        for row in run_backtest(closes)["summary"]:
            if row["signal"] == signal:
                signal_win_rate = row["win_rate"]
                break

    return {
        "symbol": clean_symbol,
        "price": round(current_price, 2),
        "change": f"{percentage_change:+.2f}%",
        "price_change": round(price_change, 2),
        "previous_close": round(data.get("pc", 0), 2),
        "signal": signal,
        "signal_reason": signal_reason,
        "signal_win_rate": signal_win_rate,
        "rsi": rsi,
    }


_series_cache: dict[str, tuple[float, list]] = {}
# Alpha Vantage's free tier caps out at 25 requests/day, and TIME_SERIES_DAILY
# only changes once per trading day, so cache aggressively to make that quota
# stretch across a full day of repeated searches instead of a single minute.
_SERIES_CACHE_TTL_SECONDS = 12 * 60 * 60


def _load_disk_cached_series(clean_symbol: str):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT fetched_at, data FROM series_cache WHERE symbol = ?",
            (clean_symbol,),
        ).fetchone()

    if not row:
        return None

    fetched_at, data_json = row
    return (fetched_at, json.loads(data_json))


def _save_series_cache(clean_symbol: str, fetched_at: float, series: list):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO series_cache (symbol, fetched_at, data) VALUES (?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                fetched_at = excluded.fetched_at,
                data = excluded.data
            """,
            (clean_symbol, fetched_at, json.dumps(series)),
        )


async def _fetch_alpha_vantage_daily(clean_symbol: str, outputsize: str, limit: int):
    if not ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key is missing.",
        )

    url = "https://www.alphavantage.co/query"
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": clean_symbol,
        "outputsize": outputsize,
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

    for date, values in list(daily_prices.items())[:limit]:
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
    return series


# A cached series shorter than this was fetched by an older version of this
# function that capped the request at 30 rows (before the AI predictor needed
# up to 100) - treat those as stale so upgrading doesn't silently starve the
# predictor of history for up to a full cache TTL.
_MIN_USABLE_SERIES_LENGTH = 50


async def _fetch_and_cache_series(clean_symbol: str):
    """The full ~100-day compact series Alpha Vantage's free tier allows
    (outputsize=full is a premium-only feature), cached once per symbol so
    the chart/signal/backtest (last 30 days) and the AI predictor (all ~100)
    share a single fetch instead of burning quota twice.
    """
    now = time.time()

    cached = _series_cache.get(clean_symbol)
    if (
        cached
        and now - cached[0] < _SERIES_CACHE_TTL_SECONDS
        and len(cached[1]) >= _MIN_USABLE_SERIES_LENGTH
    ):
        return cached[1]

    disk_cached = _load_disk_cached_series(clean_symbol)
    if (
        disk_cached
        and now - disk_cached[0] < _SERIES_CACHE_TTL_SECONDS
        and len(disk_cached[1]) >= _MIN_USABLE_SERIES_LENGTH
    ):
        _series_cache[clean_symbol] = disk_cached
        return disk_cached[1]

    series = await _fetch_alpha_vantage_daily(clean_symbol, "compact", 100)
    _series_cache[clean_symbol] = (now, series)
    _save_series_cache(clean_symbol, now, series)
    return series


async def fetch_daily_series(clean_symbol: str):
    series = await _fetch_and_cache_series(clean_symbol)
    return series[-30:]


async def fetch_training_series(clean_symbol: str):
    return await _fetch_and_cache_series(clean_symbol)


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


def run_backtest(closes: list[float]) -> dict:
    trades = []

    for index in range(1, len(closes) - 1):
        window = closes[: index + 1]
        day_change = (closes[index] - closes[index - 1]) / closes[index - 1] * 100

        sma5 = round(sum(window[-5:]) / 5, 2) if len(window) >= 5 else None
        sma20 = round(sum(window[-20:]) / 20, 2) if len(window) >= 20 else None
        rsi = calculate_rsi(window)

        signal, _ = determine_signal(day_change, sma5, sma20, rsi)
        forward_return = (closes[index + 1] - closes[index]) / closes[index] * 100

        trades.append({"signal": signal, "forward_return": forward_return})

    summary = []

    for signal_type in ["BUY", "SELL", "HOLD"]:
        matching = [trade for trade in trades if trade["signal"] == signal_type]

        if not matching:
            continue

        avg_forward_return = round(
            sum(trade["forward_return"] for trade in matching) / len(matching), 2
        )

        win_rate = None
        if signal_type in ("BUY", "SELL"):
            wins = sum(
                1
                for trade in matching
                if (signal_type == "BUY" and trade["forward_return"] > 0)
                or (signal_type == "SELL" and trade["forward_return"] < 0)
            )
            win_rate = round(wins / len(matching) * 100, 1)

        summary.append(
            {
                "signal": signal_type,
                "occurrences": len(matching),
                "avg_next_day_return": avg_forward_return,
                "win_rate": win_rate,
            }
        )

    buy_and_hold_return = (
        round((closes[-1] - closes[0]) / closes[0] * 100, 2) if closes else 0
    )

    return {
        "days_tested": len(trades),
        "summary": summary,
        "buy_and_hold_return": buy_and_hold_return,
    }


@app.get("/backtest/{symbol}")
async def backtest_signal(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

    closes = [point["close"] for point in await fetch_daily_series(clean_symbol)]

    if len(closes) < 3:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough historical data to backtest {clean_symbol}.",
        )

    return {"symbol": clean_symbol, **run_backtest(closes)}


@app.get("/ai/backtest/{symbol}")
async def ai_backtest_signal(symbol: str):
    """Day-by-day rule signal + AI prediction for the last ~30 days, each
    one computed using only data available as of that day (the AI model is
    retrained fresh at every step) - no lookahead. This is the raw material
    for replaying a trading strategy's own decision logic against history;
    the decision logic itself belongs to whatever's consuming this (e.g.
    stock-bot's own strategy.py), not to TradeMindAI.
    """
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

    series = await fetch_training_series(clean_symbol)
    closes = [point["close"] for point in series]
    dates = [point["date"] for point in series]
    n = len(closes)

    start = max(21, n - 30)

    if start >= n - 1:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough historical data to backtest {clean_symbol}.",
        )

    days = []

    for index in range(start, n - 1):
        window_closes = closes[: index + 1]
        day_change = (closes[index] - closes[index - 1]) / closes[index - 1] * 100
        sma5 = round(sum(window_closes[-5:]) / 5, 2)
        sma20 = round(sum(window_closes[-20:]) / 20, 2)
        rsi = calculate_rsi(window_closes)
        signal, _ = determine_signal(day_change, sma5, sma20, rsi)

        probability_up = None
        try:
            result = train_and_predict(series[: index + 1])
            probability_up = result["probability_up"]
        except ValueError:
            probability_up = None

        days.append(
            {
                "date": dates[index],
                "close": closes[index],
                "next_close": closes[index + 1],
                "signal": signal,
                "probability_up": probability_up,
            }
        )

    return {"symbol": clean_symbol, "days": days}


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