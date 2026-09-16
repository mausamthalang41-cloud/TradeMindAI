def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None

    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    relative_strength = avg_gain / avg_loss
    return round(100 - (100 / (1 + relative_strength)), 2)


def simple_moving_average(closes, period):
    if len(closes) < period:
        return None
    return round(sum(closes[-period:]) / period, 2)
