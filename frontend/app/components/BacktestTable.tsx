import { signalColor } from "../lib/colors";
import type { Backtest } from "../types";

type BacktestTableProps = {
  backtest: Backtest;
};

export default function BacktestTable({ backtest }: BacktestTableProps) {
  return (
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
        What today&apos;s signal logic would have called on each past day,
        and what the stock did the next day. Buy &amp; hold over the same
        period: {backtest.buy_and_hold_return >= 0 ? "+" : ""}
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
            <th style={{ textAlign: "right", padding: "8px" }}>Win Rate</th>
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
  );
}
