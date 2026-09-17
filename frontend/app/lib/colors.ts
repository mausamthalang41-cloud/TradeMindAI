export function signalColor(signal?: string) {
  if (signal === "BUY") return "#22c55e";
  if (signal === "SELL") return "#ef4444";
  return "#facc15";
}

export function probabilityColor(probabilityUp: number) {
  if (probabilityUp >= 55) return "#22c55e";
  if (probabilityUp <= 45) return "#ef4444";
  return "#facc15";
}
