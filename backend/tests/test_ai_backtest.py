from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _series(closes):
    return [
        {
            "date": f"2026-01-{(index % 28) + 1:02d}",
            "close": close,
            "low": close - 1,
            "volume": 1_000_000 + (index % 7) * 50_000,
        }
        for index, close in enumerate(closes)
    ]


def _patch_series(monkeypatch, closes):
    monkeypatch.setattr(
        main, "fetch_training_series", AsyncMock(return_value=_series(closes))
    )


def test_ai_backtest_returns_one_entry_per_walked_day(monkeypatch):
    # 25 closes: start = max(21, 25-150) = 21, so days are walked for
    # index 21..23 (3 days) - too short for the AI to ever train
    # (needs 66+), so every day should fall back to probability_up=None.
    closes = [100 + (i % 5) for i in range(25)]
    _patch_series(monkeypatch, closes)

    response = client.get("/ai/backtest/TEST")
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "TEST"
    assert len(data["days"]) == 3

    for day in data["days"]:
        assert set(day) == {
            "date", "close", "low", "next_close", "signal", "probability_up",
        }
        assert day["signal"] in ("BUY", "SELL", "HOLD")
        assert day["probability_up"] is None
        assert day["low"] == day["close"] - 1


def test_ai_backtest_rejects_too_little_history(monkeypatch):
    closes = [100, 101, 102]
    _patch_series(monkeypatch, closes)

    response = client.get("/ai/backtest/TOOSHORT")
    assert response.status_code == 404
