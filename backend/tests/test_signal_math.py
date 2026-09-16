from main import calculate_rsi, determine_signal


def test_rsi_none_when_not_enough_history():
    assert calculate_rsi([1, 2, 3], period=14) is None


def test_rsi_all_gains_is_100():
    assert calculate_rsi([1, 2, 3, 4, 5], period=3) == 100.0


def test_rsi_all_losses_is_0():
    assert calculate_rsi([5, 4, 3, 2, 1], period=3) == 0.0


def test_rsi_matches_hand_calculation():
    # gains=[1,1,0,2], losses=[0,0,1,0] over period=3, then one more
    # smoothing step -> RS=5.0 -> RSI=100-100/6=83.33 (see PR description
    # in the commit that added this test for the full derivation).
    assert calculate_rsi([10, 11, 12, 11, 13], period=3) == 83.33


def test_signal_buy_when_everything_bullish():
    signal, reason = determine_signal(
        percentage_change=1.0, sma5=105, sma20=100, rsi=25
    )
    assert signal == "BUY"
    assert "5-day average is above the 20-day average" in reason
    assert "RSI of 25 is oversold" in reason


def test_signal_sell_when_everything_bearish():
    signal, reason = determine_signal(
        percentage_change=-1.0, sma5=95, sma20=100, rsi=75
    )
    assert signal == "SELL"
    assert "5-day average is below the 20-day average" in reason
    assert "RSI of 75 is overbought" in reason


def test_signal_hold_with_no_history():
    signal, reason = determine_signal(
        percentage_change=0, sma5=None, sma20=None, rsi=None
    )
    assert signal == "HOLD"
    assert reason == "Based on today's price move only"


def test_signal_hold_when_trend_and_momentum_disagree():
    # Bullish trend (+1) cancels out overbought momentum (-1).
    signal, reason = determine_signal(
        percentage_change=0, sma5=105, sma20=100, rsi=75
    )
    assert signal == "HOLD"
    assert "5-day average is above the 20-day average" in reason
    assert "RSI of 75 is overbought" in reason
