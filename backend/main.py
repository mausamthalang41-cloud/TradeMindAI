import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


load_dotenv(Path(__file__).with_name(".env"))
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

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


@app.get("/stock/{symbol}")
async def stock(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

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

    if percentage_change > 0:
        signal = "BUY"
    elif percentage_change < 0:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "symbol": clean_symbol,
        "price": round(current_price, 2),
        "change": f"{percentage_change:+.2f}%",
        "price_change": round(price_change, 2),
        "previous_close": round(data.get("pc", 0), 2),
        "signal": signal,
    }
@app.get("/history/{symbol}")
async def stock_history(symbol: str):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")

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

    history = []

    for date, values in list(daily_prices.items())[:30]:
        history.append(
            {
                "date": date,
                "open": round(float(values["1. open"]), 2),
                "high": round(float(values["2. high"]), 2),
                "low": round(float(values["3. low"]), 2),
                "close": round(float(values["4. close"]), 2),
                "volume": int(values["5. volume"]),
            }
        )

    history.reverse()

    return {
        "symbol": clean_symbol,
        "history": history,
    }