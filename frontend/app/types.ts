export type Stock = {
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

export type WatchlistQuote = {
  symbol: string;
  price?: number;
  change?: string;
  signal?: string;
  signal_reason?: string;
  signal_win_rate?: number | null;
  error?: string;
};

export type BacktestRow = {
  signal: string;
  occurrences: number;
  avg_next_day_return: number;
  win_rate: number | null;
};

export type Backtest = {
  days_tested: number;
  summary: BacktestRow[];
  buy_and_hold_return: number;
};

export type AiPrediction = {
  probability_up: number;
  test_accuracy: number | null;
  baseline_accuracy: number | null;
  samples_trained: number;
  samples_tested: number;
};

export type NewsArticle = {
  headline: string;
  source: string;
  url: string;
  datetime: number;
};

export type SymbolSuggestion = {
  symbol: string;
  description: string;
};

export type HistoryPoint = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma5: number | null;
  sma20: number | null;
};
