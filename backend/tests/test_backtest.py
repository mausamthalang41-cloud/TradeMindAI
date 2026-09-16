from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _series(closes):
    return [
        {"date": f"2026-01-{index + 1:02d}", "close": close}
        for index, close in enumerate(closes)
    ]


def _patch_series(monkeypatch, closes):
    monkeypatch.setattr(
        main, "fetch_daily_series", AsyncMock(return_value=_series(closes))
    )


def test_backtest_classifies_every_day_by_sign_of_change(monkeypatch):
    # Short series (<15 points) keeps RSI at None and (<20 points) keeps
    # SMA20 at None throughout, so determine_signal falls back to scoring
    # purely off that day's price change - making the expected signal for
    # each day just the sign of (close[i] - close[i-1]).
    closes = [100, 102, 101, 103, 104, 103, 105, 106, 104, 107]
    _patch_series(monkeypatch, closes)

    response = client.get("/backtest/TEST")
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "TEST"
    assert data["days_tested"] == 8
    assert data["buy_and_hold_return"] == 7.0

    by_signal = {row["signal"]: row for row in data["summary"]}
    assert set(by_signal) == {"BUY", "SELL"}

    buy_days = [1, 3, 4, 6, 7]
    sell_days = [2, 5, 8]

    expected_buy_avg = round(
        sum((closes[i + 1] - closes[i]) / closes[i] * 100 for i in buy_days)
        / len(buy_days),
        2,
    )
    expected_sell_avg = round(
        sum((closes[i + 1] - closes[i]) / closes[i] * 100 for i in sell_days)
        / len(sell_days),
        2,
    )

    assert by_signal["BUY"]["occurrences"] == len(buy_days)
    assert by_signal["BUY"]["avg_next_day_return"] == expected_buy_avg
    assert by_signal["SELL"]["occurrences"] == len(sell_days)
    assert by_signal["SELL"]["avg_next_day_return"] == expected_sell_avg


def test_backtest_reports_hold_with_no_win_rate(monkeypatch):
    # First transition (100 -> 100) is a flat day, which determine_signal
    # scores as HOLD since it has no trend/momentum data and no price move.
    closes = [100, 100, 102, 98, 101, 99]
    _patch_series(monkeypatch, closes)

    response = client.get("/backtest/FLAT")
    assert response.status_code == 200
    data = response.json()

    by_signal = {row["signal"]: row for row in data["summary"]}
    assert by_signal["HOLD"]["occurrences"] == 1
    assert by_signal["HOLD"]["win_rate"] is None
    assert by_signal["HOLD"]["avg_next_day_return"] == 2.0
