import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


load_dotenv(Path(__file__).with_name(".env"))
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

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