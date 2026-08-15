from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TradeMind AI API",
    version="0.1.0",
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
    }


@app.get("/stock/{symbol}")
def stock(symbol: str):
    prices = {
        "AAPL": 213.45,
        "TSLA": 305.82,
        "NVDA": 178.21,
        "MSFT": 512.37,
        "GOOGL": 194.66,
    }

    clean_symbol = symbol.strip().upper()
    price = prices.get(clean_symbol, 100.00)

    return {
        "symbol": clean_symbol,
        "price": price,
        "change": "+2.31%",
        "signal": "BUY",
    }