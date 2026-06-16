"""Tests for the market-pulse heuristic."""

from crypto_pulse.pulse import compute_pulse


def _coin(symbol, cap, change):
    return {"symbol": symbol, "marketCap": cap, "priceChange1d": change}


def test_empty_is_neutral():
    pulse = compute_pulse([])
    assert pulse["score"] == 50
    assert pulse["label"] == "Neutral"


def test_all_green_is_greedy():
    coins = [_coin("BTC", 1e12, 6.0), _coin("ETH", 5e11, 5.0), _coin("SOL", 1e11, 8.0)]
    pulse = compute_pulse(coins)
    assert pulse["score"] > 75
    assert pulse["label"] == "Extreme Greed"
    assert pulse["advancers"] == 3
    assert pulse["decliners"] == 0


def test_all_red_is_fearful():
    coins = [_coin("BTC", 1e12, -6.0), _coin("ETH", 5e11, -5.0), _coin("SOL", 1e11, -8.0)]
    pulse = compute_pulse(coins)
    assert pulse["score"] < 25
    assert pulse["label"] == "Extreme Fear"
    assert pulse["decliners"] == 3


def test_market_cap_weighting_dominates():
    # A huge-cap coin up should outweigh a tiny-cap coin down.
    coins = [_coin("BTC", 1e12, 4.0), _coin("TINY", 1e6, -90.0)]
    pulse = compute_pulse(coins)
    assert pulse["weighted_change"] > 0


def test_score_is_bounded():
    coins = [_coin("X", 1e12, 9999.0)]
    pulse = compute_pulse(coins)
    assert 0 <= pulse["score"] <= 100
