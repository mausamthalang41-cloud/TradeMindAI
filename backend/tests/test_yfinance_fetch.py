from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi import HTTPException

import main


def _fake_history():
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1_000_000, 1_100_000],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-05"]),
    )


def test_fetch_yfinance_daily_parses_rows_ascending(monkeypatch):
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = _fake_history()
    monkeypatch.setattr(main.yfinance, "Ticker", MagicMock(return_value=fake_ticker))

    series = main._fetch_yfinance_daily_sync("AAPL")

    assert series == [
        {
            "date": "2026-01-02",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 1_000_000,
        },
        {
            "date": "2026-01-05",
            "open": 101.0,
            "high": 103.0,
            "low": 100.0,
            "close": 102.0,
            "volume": 1_100_000,
        },
    ]
    fake_ticker.history.assert_called_once_with(period="2y", interval="1d")


def test_fetch_yfinance_daily_raises_404_on_empty_history(monkeypatch):
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = pd.DataFrame()
    monkeypatch.setattr(main.yfinance, "Ticker", MagicMock(return_value=fake_ticker))

    with pytest.raises(HTTPException) as exc_info:
        main._fetch_yfinance_daily_sync("NOTASYMBOL")

    assert exc_info.value.status_code == 404


def test_fetch_yfinance_daily_raises_502_on_fetch_failure(monkeypatch):
    fake_ticker = MagicMock()
    fake_ticker.history.side_effect = RuntimeError("network is down")
    monkeypatch.setattr(main.yfinance, "Ticker", MagicMock(return_value=fake_ticker))

    with pytest.raises(HTTPException) as exc_info:
        main._fetch_yfinance_daily_sync("AAPL")

    assert exc_info.value.status_code == 502
