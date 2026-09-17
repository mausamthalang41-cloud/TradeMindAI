"use client";

import { useEffect, useState } from "react";

import AiPredictionCard from "./components/AiPredictionCard";
import BacktestTable from "./components/BacktestTable";
import NewsList from "./components/NewsList";
import PriceChart from "./components/PriceChart";
import StockCard from "./components/StockCard";
import SymbolSearch from "./components/SymbolSearch";
import Watchlist from "./components/Watchlist";
import type {
  AiPrediction,
  Backtest,
  HistoryPoint,
  NewsArticle,
  Stock,
  SymbolSuggestion,
  WatchlistQuote,
} from "./types";

export default function Home() {
  const [symbol, setSymbol] = useState("AAPL");
  const [stock, setStock] = useState<Stock | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [backtest, setBacktest] = useState<Backtest | null>(null);
  const [aiPrediction, setAiPrediction] = useState<AiPrediction | null>(null);
  const [news, setNews] = useState<NewsArticle[]>([]);
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
    setAiPrediction(null);
    setNews([]);

    try {
      const [
        stockResponse,
        historyResponse,
        backtestResponse,
        aiResponse,
        newsResponse,
      ] = await Promise.all([
        fetch(`http://127.0.0.1:8000/stock/${cleanSymbol}`),
        fetch(`http://127.0.0.1:8000/history/${cleanSymbol}`),
        fetch(`http://127.0.0.1:8000/backtest/${cleanSymbol}`),
        fetch(`http://127.0.0.1:8000/ai/predict/${cleanSymbol}`),
        fetch(`http://127.0.0.1:8000/news/${cleanSymbol}`),
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

      if (aiResponse.ok) {
        setAiPrediction(await aiResponse.json());
      }

      if (newsResponse.ok) {
        const newsData = await newsResponse.json();
        setNews(newsData.articles ?? []);
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

        <SymbolSearch
          symbol={symbol}
          onSymbolChange={(value) => {
            setSymbol(value);
            setShowSuggestions(true);
          }}
          suggestions={suggestions}
          showSuggestions={showSuggestions}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setShowSuggestions(false)}
          onCloseSuggestions={() => setShowSuggestions(false)}
          onSelectSuggestion={(selected) => searchStock(selected)}
          onSearch={() => searchStock()}
          loading={loading}
        />

        <Watchlist
          quotes={watchlistQuotes}
          activeSymbol={stock?.symbol}
          onSelect={(selected) => searchStock(selected)}
          onToggle={toggleWatchlist}
        />

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
          <StockCard
            stock={stock}
            isWatchlisted={watchlistSymbols.includes(stock.symbol)}
            onToggleWatchlist={() => toggleWatchlist(stock.symbol)}
          />
        )}

        <NewsList articles={news} />

        <PriceChart history={history} />

        {backtest && <BacktestTable backtest={backtest} />}

        {aiPrediction && <AiPredictionCard prediction={aiPrediction} />}

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
