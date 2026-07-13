export default function Home() {
  return (
    <main
      style={{
        background: "#0f172a",
        minHeight: "100vh",
        color: "white",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Arial",
      }}
    >
      <div
        style={{
          width: "700px",
          background: "#1e293b",
          padding: "40px",
          borderRadius: "20px",
        }}
      >
        <h1
          style={{
            color: "#38bdf8",
            textAlign: "center",
            fontSize: "42px",
          }}
        >
          TradeMind AI
        </h1>

        <p
          style={{
            textAlign: "center",
            color: "#94a3b8",
          }}
        >
          AI Powered Trading Platform
        </p>

        <hr />

        <input
          placeholder="Search Stock..."
          style={{
            width: "100%",
            padding: "15px",
            marginTop: "20px",
            borderRadius: "10px",
            fontSize: "18px",
          }}
        />

        <div
          style={{
            marginTop: "30px",
            background: "#334155",
            padding: "20px",
            borderRadius: "15px",
          }}
        >
          <h2>AAPL</h2>

          <h3>$213.45</h3>

          <p>Change: +2.31%</p>

          <h2
            style={{
              color: "lime",
            }}
          >
            BUY
          </h2>
        </div>
      </div>
    </main>
  );
}