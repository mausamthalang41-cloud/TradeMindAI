from fastapi import FastAPI

app = FastAPI(
    title="TradeMind AI API",
    version="0.1.0"
)

@app.get("/")
def home():
    return {
        "app": "TradeMind AI",
        "status": "Running"
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

    price = prices.get(symbol.upper(), 100.00)

    return {
        "symbol": symbol.upper(),
        "price": price,
        "change": "+2.31%",
        "signal": "BUY",
    }

   