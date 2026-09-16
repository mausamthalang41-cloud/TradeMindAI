import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "../app/page";

type Route = {
  match: (url: string) => boolean;
  ok?: boolean;
  body: unknown;
};

function mockFetch(routes: Route[]) {
  global.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = input.toString();
    const route = routes.find((candidate) => candidate.match(url));

    if (!route) {
      throw new Error(`No mock route for ${url}`);
    }

    return Promise.resolve({
      ok: route.ok ?? true,
      json: () => Promise.resolve(route.body),
    } as Response);
  }) as typeof fetch;
}

const emptyWatchlist: Route = {
  match: (url) => url.includes("/watchlist/quotes"),
  body: { quotes: [] },
};

const noSuggestions: Route = {
  match: (url) => url.includes("/symbols/search"),
  body: { results: [] },
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Home", () => {
  it("shows the empty-state prompt before any search", async () => {
    mockFetch([emptyWatchlist, noSuggestions]);
    render(<Home />);

    expect(
      await screen.findByText(/search for a stock to view live data/i)
    ).toBeInTheDocument();
  });

  it("renders the stock card, backtest table, and news after a successful search", async () => {
    mockFetch([
      emptyWatchlist,
      noSuggestions,
      {
        match: (url) => url.includes("/stock/AAPL"),
        body: {
          symbol: "AAPL",
          price: 333.53,
          change: "+0.66%",
          price_change: 2.19,
          previous_close: 331.34,
          signal: "BUY",
          signal_reason: "5-day average is above the 20-day average",
          signal_win_rate: 52.4,
          rsi: 63.49,
        },
      },
      {
        match: (url) => url.includes("/history/AAPL"),
        body: { symbol: "AAPL", history: [] },
      },
      {
        match: (url) => url.includes("/backtest/AAPL"),
        body: {
          symbol: "AAPL",
          days_tested: 28,
          summary: [
            {
              signal: "BUY",
              occurrences: 21,
              avg_next_day_return: 0.25,
              win_rate: 52.4,
            },
          ],
          buy_and_hold_return: 7.1,
        },
      },
      {
        match: (url) => url.includes("/news/AAPL"),
        body: {
          symbol: "AAPL",
          articles: [
            {
              headline: "Apple announces new product",
              source: "Yahoo",
              url: "https://example.com/article",
              datetime: 1700000000,
            },
          ],
        },
      },
    ]);

    render(<Home />);

    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    expect(await screen.findByText("$333.53")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /BUY/ })
    ).toBeInTheDocument();
    expect(screen.getByText(/52.4% historical win rate/)).toBeInTheDocument();
    expect(screen.getByText(/RSI \(14\): 63.49/)).toBeInTheDocument();

    expect(await screen.findByText("Signal Backtest (28 days)")).toBeInTheDocument();
    expect(screen.getByText(/\+0.25%/)).toBeInTheDocument();

    expect(
      await screen.findByText("Apple announces new product")
    ).toBeInTheDocument();
  });

  it("shows an error message when the stock lookup fails", async () => {
    mockFetch([
      emptyWatchlist,
      noSuggestions,
      {
        match: (url) => url.includes("/stock/BADSYM"),
        ok: false,
        body: { detail: "No market data found for BADSYM." },
      },
      {
        match: (url) => url.includes("/history/BADSYM"),
        ok: false,
        body: { detail: "No historical data found for BADSYM." },
      },
      {
        match: (url) => url.includes("/backtest/BADSYM"),
        ok: false,
        body: { detail: "Not enough historical data." },
      },
      {
        match: (url) => url.includes("/news/BADSYM"),
        body: { symbol: "BADSYM", articles: [] },
      },
    ]);

    render(<Home />);

    const input = screen.getByPlaceholderText(/enter a stock symbol/i);
    fireEvent.change(input, { target: { value: "BADSYM" } });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    expect(
      await screen.findByText("No market data found for BADSYM.")
    ).toBeInTheDocument();
  });

  it("stars a stock by POSTing to the watchlist and reloading it", async () => {
    const routes: Route[] = [
      emptyWatchlist,
      noSuggestions,
      {
        match: (url) => url.includes("/stock/AAPL"),
        body: {
          symbol: "AAPL",
          price: 333.53,
          change: "+0.66%",
          price_change: 2.19,
          previous_close: 331.34,
          signal: "BUY",
          signal_reason: "Based on today's price move only",
          signal_win_rate: null,
          rsi: null,
        },
      },
      { match: (url) => url.includes("/history/AAPL"), body: { symbol: "AAPL", history: [] } },
      {
        match: (url) => url.includes("/backtest/AAPL"),
        body: { symbol: "AAPL", days_tested: 0, summary: [], buy_and_hold_return: 0 },
      },
      { match: (url) => url.includes("/news/AAPL"), body: { symbol: "AAPL", articles: [] } },
      {
        match: (url) =>
          url.includes("/watchlist/AAPL") && !url.includes("quotes"),
        body: { symbol: "AAPL", watchlisted: true },
      },
    ];
    mockFetch(routes);

    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: /search/i }));
    await screen.findByText("$333.53");

    fireEvent.click(screen.getByTitle("Add to watchlist"));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/watchlist/AAPL"),
        expect.objectContaining({ method: "POST" })
      );
    });
  });
});
