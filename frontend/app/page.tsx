"use client";

import { useState } from "react";

export default function Home() {
  const [symbol, setSymbol] = useState("AAPL");
  const [stock, setStock] = useState({
    symbol: "AAPL",
    price: 213.45,
    change: "+2.31%",
    signal: "BUY",
  });

  async function searchStock() {
    const response = await fetch(
      `http://127.0.0.1:8000/stock/${symbol}`
    );

    const data = await response.json();

    setStock(data);
  }

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
          background: "#1e293b",
          padding: "40px",
          borderRadius: "20px",
        }}
      >
        <h1
          style={{
            textAlign: "center",
            color: "#38bdf8",
          }}
        >
          TradeMind AI
        </h1>

        <p style={{ textAlign: "center" }}>
          AI Powered Trading Platform
        </p>

        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Enter stock..."
          style={{
            width: "100%",
            padding: "15px",
            marginTop: "20px",
            fontSize: "18px",
          }}
        />

        <button
          onClick={searchStock}
          style={{
            width: "100%",
            marginTop: "15px",
            padding: "15px",
            background: "#38bdf8",
            border: "none",
            color: "white",
            fontSize: "18px",
            cursor: "pointer",
          }}
        >
          Search
        </button>

        <div
          style={{
            marginTop: "30px",
            background: "#334155",
            padding: "20px",
            borderRadius: "15px",
          }}
        >
          <h2>{stock.symbol}</h2>

          <h3>${stock.price}</h3>

          <p>{stock.change}</p>

          <h2
            style={{
              color: "lime",
            }}
          >
            {stock.signal}
          </h2>
        </div>
      </div>
    </main>
  );
}