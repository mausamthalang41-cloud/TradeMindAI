import { probabilityColor } from "../lib/colors";
import type { AiPrediction } from "../types";

type AiPredictionCardProps = {
  prediction: AiPrediction;
};

export default function AiPredictionCard({ prediction }: AiPredictionCardProps) {
  return (
    <div
      style={{
        marginTop: "30px",
        padding: "20px",
        background: "#334155",
        borderRadius: "15px",
      }}
    >
      <h2 style={{ textAlign: "center" }}>AI Prediction</h2>

      <p
        style={{
          textAlign: "center",
          marginTop: "10px",
          fontSize: "22px",
          fontWeight: "bold",
          color: probabilityColor(prediction.probability_up),
        }}
      >
        {prediction.probability_up}% chance of a higher close tomorrow
      </p>

      <p
        style={{
          textAlign: "center",
          color: "#94a3b8",
          fontSize: "14px",
          marginTop: "5px",
        }}
      >
        {prediction.test_accuracy !== null
          ? `Logistic regression trained on this symbol's own price history: ${prediction.test_accuracy}% accurate on ${prediction.samples_tested} held-out days it wasn't trained on (${prediction.samples_trained} training days).`
          : `Logistic regression trained on ${prediction.samples_trained} days of this symbol's own price history.`}{" "}
        Not financial advice - a coin flip beats this on a bad day.
      </p>
    </div>
  );
}
