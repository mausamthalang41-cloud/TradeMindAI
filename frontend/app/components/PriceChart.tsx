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

import type { HistoryPoint } from "../types";

type PriceChartProps = {
  history: HistoryPoint[];
};

export default function PriceChart({ history }: PriceChartProps) {
  if (history.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        marginTop: "30px",
        padding: "20px",
        background: "#334155",
        borderRadius: "15px",
      }}
    >
      <h2 style={{ textAlign: "center" }}>30-Day Price &amp; Moving Averages</h2>

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
  );
}
