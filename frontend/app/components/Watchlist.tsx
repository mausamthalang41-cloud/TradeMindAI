import { signalColor } from "../lib/colors";
import type { WatchlistQuote } from "../types";

type WatchlistProps = {
  quotes: WatchlistQuote[];
  activeSymbol?: string;
  onSelect: (symbol: string) => void;
  onToggle: (symbol: string) => void;
};

export default function Watchlist({
  quotes,
  activeSymbol,
  onSelect,
  onToggle,
}: WatchlistProps) {
  if (quotes.length === 0) {
    return null;
  }

  return (
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
        {quotes.map((quote) => (
          <div
            key={quote.symbol}
            onClick={() => onSelect(quote.symbol)}
            style={{
              cursor: "pointer",
              padding: "15px",
              borderRadius: "12px",
              background: "#334155",
              border:
                activeSymbol === quote.symbol
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
                  onToggle(quote.symbol);
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
                <p style={{ margin: "6px 0 0" }}>${quote.price?.toFixed(2)}</p>
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
  );
}
