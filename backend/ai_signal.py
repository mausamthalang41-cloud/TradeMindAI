from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from indicators import calculate_rsi, simple_moving_average

LOOKBACK_DAYS = 20
MIN_TRAINING_SAMPLES = 30


def _features_at(closes, index):
    window = closes[: index + 1]
    sma5 = simple_moving_average(window, 5)
    sma20 = simple_moving_average(window, 20)
    rsi = calculate_rsi(window)

    if sma5 is None or sma20 is None or rsi is None:
        return None

    day_change = (closes[index] - closes[index - 1]) / closes[index - 1] * 100
    momentum5 = (closes[index] - closes[index - 5]) / closes[index - 5] * 100

    return [sma5 - sma20, rsi, day_change, momentum5]


def build_dataset(series):
    """Turn a chronological list of {"close": ...} bars into (X, y, latest_features).

    X/y are features/labels for every day that has both a full lookback window
    and a known next-day outcome. latest_features is the feature vector for the
    most recent day - the one we actually want a prediction for - or None if
    there isn't enough history yet.
    """
    closes = [point["close"] for point in series]

    X = []
    y = []

    for index in range(LOOKBACK_DAYS, len(closes) - 1):
        features = _features_at(closes, index)
        if features is None:
            continue
        X.append(features)
        y.append(1 if closes[index + 1] > closes[index] else 0)

    latest_features = (
        _features_at(closes, len(closes) - 1) if len(closes) > LOOKBACK_DAYS else None
    )

    return X, y, latest_features


def train_and_predict(series):
    """Train a logistic regression on a symbol's own history and predict
    whether tomorrow's close will be higher than today's.

    Raises ValueError when there isn't enough (or varied enough) history to
    train a meaningful model - callers should treat that as "unavailable"
    rather than a server error.
    """
    X, y, latest_features = build_dataset(series)

    if len(X) < MIN_TRAINING_SAMPLES or latest_features is None:
        raise ValueError("Not enough history to train a model.")

    if len(set(y)) < 2:
        raise ValueError("Not enough variation in outcomes to train a model.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    latest_scaled = scaler.transform([latest_features])

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_scaled, y_train)

    test_accuracy = None
    if X_test:
        X_test_scaled = scaler.transform(X_test)
        test_accuracy = round(model.score(X_test_scaled, y_test) * 100, 1)

    probability_up = round(float(model.predict_proba(latest_scaled)[0][1]) * 100, 1)

    return {
        "probability_up": probability_up,
        "test_accuracy": test_accuracy,
        "samples_trained": len(X_train),
        "samples_tested": len(X_test),
    }
