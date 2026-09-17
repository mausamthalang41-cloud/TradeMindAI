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


def _ema_series(values, period):
    k = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(value * k + result[-1] * (1 - k))
    return result


def macd_histogram(closes, fast=12, slow=26, signal=9):
    """MACD line minus its signal line - positive/rising means bullish
    momentum is building, negative/falling means it's fading."""
    if len(closes) < slow + signal:
        return None

    fast_ema = _ema_series(closes, fast)
    slow_ema = _ema_series(closes, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = _ema_series(macd_line, signal)
    return round(macd_line[-1] - signal_line[-1], 4)
