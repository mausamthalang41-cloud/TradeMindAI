import { signalColor } from "../lib/colors";
import type { Stock } from "../types";

type StockCardProps = {
  stock: Stock;
  isWatchlisted: boolean;
  onToggleWatchlist: () => void;
};

export default function StockCard({
  stock,
  isWatchlisted,
  onToggleWatchlist,
}: StockCardProps) {
  return (
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
          onClick={onToggleWatchlist}
          title={isWatchlisted ? "Remove from watchlist" : "Add to watchlist"}
          style={{
            background: "none",
            border: "none",
            fontSize: "24px",
            cursor: "pointer",
            color: isWatchlisted ? "#facc15" : "#64748b",
          }}
        >
          {isWatchlisted ? "★" : "☆"}
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
  );
}
