import type { SymbolSuggestion } from "../types";

type SymbolSearchProps = {
  symbol: string;
  onSymbolChange: (value: string) => void;
  suggestions: SymbolSuggestion[];
  showSuggestions: boolean;
  onFocus: () => void;
  onBlur: () => void;
  onCloseSuggestions: () => void;
  onSelectSuggestion: (symbol: string) => void;
  onSearch: () => void;
  loading: boolean;
};

export default function SymbolSearch({
  symbol,
  onSymbolChange,
  suggestions,
  showSuggestions,
  onFocus,
  onBlur,
  onCloseSuggestions,
  onSelectSuggestion,
  onSearch,
  loading,
}: SymbolSearchProps) {
  return (
    <>
      <div style={{ position: "relative" }}>
        <input
          value={symbol}
          onChange={(event) => onSymbolChange(event.target.value)}
          onFocus={onFocus}
          onBlur={onBlur}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              onSearch();
            }
            if (event.key === "Escape") {
              onCloseSuggestions();
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
                onMouseDown={() => onSelectSuggestion(suggestion.symbol)}
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
        onClick={onSearch}
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
    </>
  );
}
