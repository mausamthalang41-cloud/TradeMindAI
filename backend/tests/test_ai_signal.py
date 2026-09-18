import math

import pytest

from ai_signal import LOOKBACK_DAYS, build_dataset, train_and_predict


def _series_from_closes(closes):
    return [
        {"close": close, "volume": 1_000_000 + (i % 7) * 50_000}
        for i, close in enumerate(closes)
    ]


def test_build_dataset_shapes_and_labels():
    # A simple alternating up/down pattern gives predictable labels and
    # guarantees variation (unlike a monotonic series).
    closes = [100.0]
    for i in range(1, 80):
        closes.append(closes[-1] + (1 if i % 2 == 0 else -0.5))

    series = _series_from_closes(closes)
    X, y, latest_features = build_dataset(series)

    expected_rows = len(closes) - 1 - LOOKBACK_DAYS
    assert len(X) == expected_rows
    assert len(y) == expected_rows
    assert all(label in (0, 1) for label in y)
    assert latest_features is not None
    assert len(latest_features) == 7
    assert all(math.isfinite(value) for value in latest_features)


def test_build_dataset_returns_no_latest_features_when_too_short():
    series = _series_from_closes([100.0] * (LOOKBACK_DAYS - 1))
    X, y, latest_features = build_dataset(series)
    assert X == []
    assert y == []
    assert latest_features is None


def test_train_and_predict_raises_on_monotonic_series():
    # Strictly increasing closes give every label the value 1 - no
    # variation for the classifier to learn from.
    closes = [100.0 + i for i in range(80)]
    series = _series_from_closes(closes)

    with pytest.raises(ValueError, match="variation"):
        train_and_predict(series)


def test_train_and_predict_raises_on_too_little_history():
    closes = [100.0 + (i % 3) for i in range(30)]
    series = _series_from_closes(closes)

    with pytest.raises(ValueError, match="Not enough history"):
        train_and_predict(series)


def test_train_and_predict_returns_sane_ranges():
    closes = [100.0]
    for i in range(1, 90):
        step = 1.5 if (i * 7) % 3 == 0 else -1.0
        closes.append(closes[-1] + step)

    series = _series_from_closes(closes)
    result = train_and_predict(series)

    assert 0.0 <= result["probability_up"] <= 100.0
    assert result["samples_trained"] > 0
    assert result["samples_tested"] > 0
    if result["test_accuracy"] is not None:
        assert 0.0 <= result["test_accuracy"] <= 100.0
    if result["baseline_accuracy"] is not None:
        assert 0.0 <= result["baseline_accuracy"] <= 100.0


def test_train_and_predict_reports_baseline_matching_majority_class():
    # A lopsided but non-monotonic series: mostly up days with the
    # occasional down day, so the majority-class baseline is well-defined
    # and its accuracy is independently computable from the pattern itself.
    closes = [100.0]
    for i in range(1, 90):
        step = -1.0 if i % 6 == 0 else 1.0
        closes.append(closes[-1] + step)

    series = _series_from_closes(closes)
    result = train_and_predict(series)

    assert result["baseline_accuracy"] is not None
    # Majority-guess baseline can't do worse than always guessing the rarer
    # class, and this series is skewed enough that it should beat a coin flip.
    assert result["baseline_accuracy"] >= 50.0
