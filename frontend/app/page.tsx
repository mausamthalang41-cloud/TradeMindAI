"use client";

import { useState } from "react";

type Stock = {
  symbol: string;
  price: number;
  change: string;
  price_change: number;
  previous_close: number;
  signal: string;
};

export default function Home() {
  const [symbol, setSymbol] = useState("AAPL");
  const [stock, setStock] = useState<Stock | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function searchStock() {
    const cleanSymbol = symbol.trim().toUpperCase();

    if (!cleanSymbol) {
      setError("Please enter a stock symbol.");
      return;
    }

    setLoading(true);
    setError("");
    setStock(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/stock/${encodeURIComponent(cleanSymbol)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Stock could not be found.");
      }

      setStock(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  const signalColor =
    stock?.signal === "BUY"
      ? "#22c55e"
      : stock?.signal === "SELL"
      ? "#ef4444"
      : "#facc15";

  return (
    <main
      style={{
        background: "#0f172a",
        minHeight: "100vh",
        color: "white",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Arial",
      }}
    >
      <div
        style={{
          width: "700px",
          maxWidth: "85%",
          background: "#1e293b",
          padding: "40px",
          borderRadius: "20px",
        }}
      >
        <h1 style={{ textAlign: "center", color: "#38bdf8" }}>
          TradeMind AI
        </h1>

        <p style={{ textAlign: "center" }}>
          Live Stock Market Analysis
        </p>

        <input
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              searchStock();
            }
          }}
          placeholder="Enter stock symbol, for example AAPL"
          style={{
            boxSizing: "border-box",
            width: "100%",
            padding: "15px",
            marginTop: "20px",
            fontSize: "18px",
          }}
        />

        <button
          onClick={searchStock}
          disabled={loading}
          style={{
            width: "100%",
            marginTop: "15px",
            padding: "15px",
            background: loading ? "#64748b" : "#38bdf8",
            border: "none",
            color: "white",
            fontSize: "18px",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Loading..." : "Search"}
        </button>

        {error && (
          <div
            style={{
              marginTop: "25px",
              background: "#7f1d1d",
              padding: "15px",
              borderRadius: "10px",
            }}
          >
            {error}
          </div>
        )}

        {stock && (
          <div
            style={{
              marginTop: "30px",
              background: "#334155",
              padding: "20px",
              borderRadius: "15px",
            }}
          >
            <h2>{stock.symbol}</h2>
            <h3>${stock.price.toFixed(2)}</h3>
            <p>Change: {stock.change}</p>
            <p>Price movement: ${stock.price_change.toFixed(2)}</p>
            <p>Previous close: ${stock.previous_close.toFixed(2)}</p>

            <h2 style={{ color: signalColor }}>
              {stock.signal}
            </h2>
          </div>
        )}

        {!stock && !loading && !error && (
          <p style={{ marginTop: "25px", textAlign: "center", color: "#94a3b8" }}>
            Search for a stock to see its latest market data.
          </p>
        )}
      </div>
    </main>
  );
}