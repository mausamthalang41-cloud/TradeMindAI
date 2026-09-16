"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Stock = {
  symbol: string;
  price: number;
  change: string;
  price_change: number;
  previous_close: number;
  signal: string;
  signal_reason: string;
  signal_win_rate: number | null;
  rsi: number | null;
};

type WatchlistQuote = {
  symbol: string;
  price?: number;
  change?: string;
  signal?: string;
  signal_reason?: string;
  signal_win_rate?: number | null;
  error?: string;
};

type BacktestRow = {
  signal: string;
  occurrences: number;
  avg_next_day_return: number;
  win_rate: number | null;
};

type Backtest = {
  days_tested: number;
  summary: BacktestRow[];
  buy_and_hold_return: number;
};

type SymbolSuggestion = {
  symbol: string;
  description: string;
};

type HistoryPoint = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma5: number | null;
  sma20: number | null;
};

export default function Home() {
  const [symbol, setSymbol] = useState("AAPL");
  const [stock, setStock] = useState<Stock | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [backtest, setBacktest] = useState<Backtest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [watchlistQuotes, setWatchlistQuotes] = useState<WatchlistQuote[]>([]);
  const watchlistSymbols = watchlistQuotes.map((quote) => quote.symbol);
  const [suggestions, setSuggestions] = useState<SymbolSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    loadWatchlist();
  }, []);

  useEffect(() => {
    const query = symbol.trim();

    if (!query || query.toUpperCase() === stock?.symbol) {
      setSuggestions([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/symbols/search?q=${encodeURIComponent(query)}`
        );
        const data = await response.json();
        setSuggestions(data.results ?? []);
      } catch {
        setSuggestions([]);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  async function loadWatchlist() {
    try {
      const response = await fetch("http://127.0.0.1:8000/watchlist/quotes");
      const data = await response.json();
      setWatchlistQuotes(data.quotes);
    } catch {
      // Watchlist is a non-critical enhancement; ignore failures.
    }
  }

  async function toggleWatchlist(targetSymbol: string) {
    const method = watchlistSymbols.includes(targetSymbol)
      ? "DELETE"
      : "POST";
    await fetch(`http://127.0.0.1:8000/watchlist/${targetSymbol}`, {
      method,
    });
    loadWatchlist();
  }

  async function searchStock(symbolOverride?: string) {
    const cleanSymbol = (symbolOverride ?? symbol).trim().toUpperCase();

    if (!cleanSymbol) {
      setError("Please enter a stock symbol.");
      return;
    }

    setSymbol(cleanSymbol);
    setShowSuggestions(false);
    setSuggestions([]);
    setLoading(true);
    setError("");
    setStock(null);
    setHistory([]);
    setBacktest(null);

    try {
      const [stockResponse, historyResponse, backtestResponse] =
        await Promise.all([
          fetch(`http://127.0.0.1:8000/stock/${cleanSymbol}`),
          fetch(`http://127.0.0.1:8000/history/${cleanSymbol}`),
          fetch(`http://127.0.0.1:8000/backtest/${cleanSymbol}`),
        ]);

      const stockData = await stockResponse.json();
      const historyData = await historyResponse.json();

      if (!stockResponse.ok) {
        throw new Error(stockData.detail || "Live stock data was not found.");
      }

      if (!historyResponse.ok) {
        throw new Error(
          historyData.detail || "Historical stock data was not found."
        );
      }

      setStock(stockData);
      setHistory(historyData.history);

      if (backtestResponse.ok) {
        setBacktest(await backtestResponse.json());
      }
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

  function signalColor(signal?: string) {
    if (signal === "BUY") return "#22c55e";
    if (signal === "SELL") return "#ef4444";
    return "#facc15";
  }

  return (
    <main
      style={{
        background: "#0f172a",
        minHeight: "100vh",
        color: "white",
        padding: "50px 20px",
        fontFamily: "Arial",
      }}
    >
      <div
        style={{
          maxWidth: "900px",
          margin: "0 auto",
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

        <div style={{ position: "relative" }}>
          <input
            value={symbol}
            onChange={(event) => {
              setSymbol(event.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setShowSuggestions(false)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                searchStock();
              }
              if (event.key === "Escape") {
                setShowSuggestions(false);
              }
            }}
            placeholder="Enter a stock symbol, for example AAPL"
            style={{
              boxSizing: "border-box",
              width: "100%",
              padding: "15px",
              marginTop: "20px",
              fontSize: "18px",
            }}
          />

          {showSuggestions && suggestions.length > 0 && (
            <div
              style={{
                position: "absolute",
                top: "100%",
                left: 0,
                right: 0,
                marginTop: "4px",
                background: "#0f172a",
                border: "1px solid #38bdf8",
                borderRadius: "8px",
                maxHeight: "260px",
                overflowY: "auto",
                zIndex: 10,
              }}
            >
              {suggestions.map((suggestion) => (
                <div
                  key={suggestion.symbol}
                  onMouseDown={() => searchStock(suggestion.symbol)}
                  style={{
                    padding: "10px 15px",
                    cursor: "pointer",
                    borderBottom: "1px solid #334155",
                  }}
                >
                  <strong>{suggestion.symbol}</strong>{" "}
                  <span style={{ color: "#94a3b8", fontSize: "13px" }}>
                    {suggestion.description}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={() => searchStock()}
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

        {watchlistQuotes.length > 0 && (
          <div style={{ marginTop: "30px" }}>
            <h2 style={{ textAlign: "center" }}>Watchlist</h2>

            <div
              style={{
                marginTop: "15px",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                gap: "12px",
              }}
            >
              {watchlistQuotes.map((quote) => (
                <div
                  key={quote.symbol}
                  onClick={() => searchStock(quote.symbol)}
                  style={{
                    cursor: "pointer",
                    padding: "15px",
                    borderRadius: "12px",
                    background: "#334155",
                    border:
                      stock?.symbol === quote.symbol
                        ? "2px solid #38bdf8"
                        : "2px solid transparent",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <strong>{quote.symbol}</strong>
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        toggleWatchlist(quote.symbol);
                      }}
                      title="Remove from watchlist"
                      style={{
                        background: "none",
                        border: "none",
                        color: "#94a3b8",
                        cursor: "pointer",
                        fontSize: "16px",
                      }}
                    >
                      ✕
                    </button>
                  </div>

                  {quote.error ? (
                    <p
                      style={{
                        margin: "6px 0 0",
                        fontSize: "13px",
                        color: "#f87171",
                      }}
                    >
                      {quote.error}
                    </p>
                  ) : (
                    <>
                      <p style={{ margin: "6px 0 0" }}>
                        ${quote.price?.toFixed(2)}
                      </p>
                      <p
                        style={{
                          margin: 0,
                          fontSize: "13px",
                          color: (quote.change ?? "").startsWith("-")
                            ? "#ef4444"
                            : "#22c55e",
                        }}
                      >
                        {quote.change}
                      </p>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          marginTop: "6px",
                        }}
                      >
                        <span
                          style={{
                            fontSize: "12px",
                            fontWeight: "bold",
                            color: signalColor(quote.signal),
                          }}
                        >
                          {quote.signal}
                        </span>
                        {quote.signal_win_rate !== null &&
                          quote.signal_win_rate !== undefined && (
                            <span
                              title="Historical win rate of this signal over the last 30 days"
                              style={{
                                fontSize: "11px",
                                color: "#94a3b8",
                              }}
                            >
                              ({quote.signal_win_rate}% win rate)
                            </span>
                          )}
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div
            style={{
              marginTop: "25px",
              padding: "15px",
              background: "#7f1d1d",
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
              padding: "20px",
              background: "#334155",
              borderRadius: "15px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <h2 style={{ margin: 0 }}>{stock.symbol}</h2>
              <button
                onClick={() => toggleWatchlist(stock.symbol)}
                title={
                  watchlistSymbols.includes(stock.symbol)
                    ? "Remove from watchlist"
                    : "Add to watchlist"
                }
                style={{
                  background: "none",
                  border: "none",
                  fontSize: "24px",
                  cursor: "pointer",
                  color: watchlistSymbols.includes(stock.symbol)
                    ? "#facc15"
                    : "#64748b",
                }}
              >
                {watchlistSymbols.includes(stock.symbol) ? "★" : "☆"}
              </button>
            </div>
            <h3>${stock.price.toFixed(2)}</h3>
            <p>Change: {stock.change}</p>
            <p>Price movement: ${stock.price_change.toFixed(2)}</p>
            <p>Previous close: ${stock.previous_close.toFixed(2)}</p>
            {stock.rsi !== null && <p>RSI (14): {stock.rsi}</p>}
            <h2 style={{ color: signalColor(stock.signal) }}>
              {stock.signal}
              {stock.signal_win_rate !== null && (
                <span
                  style={{
                    fontSize: "14px",
                    color: "#94a3b8",
                    marginLeft: "10px",
                  }}
                >
                  {stock.signal_win_rate}% historical win rate
                </span>
              )}
            </h2>
            <p style={{ color: "#94a3b8", fontSize: "14px" }}>
              {stock.signal_reason}
            </p>
          </div>
        )}

        {history.length > 0 && (
          <div
            style={{
              marginTop: "30px",
              padding: "20px",
              background: "#334155",
              borderRadius: "15px",
            }}
          >
            <h2 style={{ textAlign: "center" }}>
              30-Day Price &amp; Moving Averages
            </h2>

            <div style={{ width: "100%", height: "350px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={history}
                  margin={{ top: 20, right: 20, left: 10, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#64748b" />

                  <XAxis
                    dataKey="date"
                    stroke="#cbd5e1"
                    tickFormatter={(date) => date.slice(5)}
                  />

                  <YAxis
                    stroke="#cbd5e1"
                    domain={["auto", "auto"]}
                    tickFormatter={(value) => `$${value}`}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#0f172a",
                      border: "1px solid #38bdf8",
                      borderRadius: "8px",
                    }}
                    formatter={(value, name) => [
                      value == null ? "-" : `$${Number(value).toFixed(2)}`,
                      name,
                    ]}
                  />

                  <Legend />

                  <Line
                    type="monotone"
                    dataKey="close"
                    name="Close"
                    stroke="#38bdf8"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 6 }}
                  />

                  <Line
                    type="monotone"
                    dataKey="sma5"
                    name="SMA 5"
                    stroke="#facc15"
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />

                  <Line
                    type="monotone"
                    dataKey="sma20"
                    name="SMA 20"
                    stroke="#a78bfa"
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {backtest && (
          <div
            style={{
              marginTop: "30px",
              padding: "20px",
              background: "#334155",
              borderRadius: "15px",
            }}
          >
            <h2 style={{ textAlign: "center" }}>
              Signal Backtest ({backtest.days_tested} days)
            </h2>
            <p
              style={{
                textAlign: "center",
                color: "#94a3b8",
                fontSize: "14px",
                marginTop: "5px",
              }}
            >
              What today&apos;s signal logic would have called on each past
              day, and what the stock did the next day. Buy &amp; hold over
              the same period: {backtest.buy_and_hold_return >= 0 ? "+" : ""}
              {backtest.buy_and_hold_return}%
            </p>

            <table
              style={{
                width: "100%",
                marginTop: "15px",
                borderCollapse: "collapse",
              }}
            >
              <thead>
                <tr style={{ borderBottom: "1px solid #475569" }}>
                  <th style={{ textAlign: "left", padding: "8px" }}>Signal</th>
                  <th style={{ textAlign: "right", padding: "8px" }}>
                    Occurrences
                  </th>
                  <th style={{ textAlign: "right", padding: "8px" }}>
                    Avg Next-Day Return
                  </th>
                  <th style={{ textAlign: "right", padding: "8px" }}>
                    Win Rate
                  </th>
                </tr>
              </thead>
              <tbody>
                {backtest.summary.map((row) => (
                  <tr key={row.signal} style={{ borderBottom: "1px solid #475569" }}>
                    <td
                      style={{
                        padding: "8px",
                        color: signalColor(row.signal),
                        fontWeight: "bold",
                      }}
                    >
                      {row.signal}
                    </td>
                    <td style={{ textAlign: "right", padding: "8px" }}>
                      {row.occurrences}
                    </td>
                    <td style={{ textAlign: "right", padding: "8px" }}>
                      {row.avg_next_day_return >= 0 ? "+" : ""}
                      {row.avg_next_day_return}%
                    </td>
                    <td style={{ textAlign: "right", padding: "8px" }}>
                      {row.win_rate === null ? "—" : `${row.win_rate}%`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!stock && !loading && !error && (
          <p
            style={{
              marginTop: "25px",
              textAlign: "center",
              color: "#94a3b8",
            }}
          >
            Search for a stock to view live data and its 30-day chart.
          </p>
        )}
      </div>
    </main>
  );
}