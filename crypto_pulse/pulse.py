"""Compute a transparent, home-grown "Market Pulse" index.

This is NOT the official CoinStats / Alternative.me Fear & Greed index. It is a
simple, fully-explained heuristic derived from two signals in the top-coin set:

* **Momentum** — the market-cap-weighted average 24h price change.
* **Breadth** — the share of tracked coins that are up over 24h.

The two are blended into a 0-100 score so the dashboard and the SVG card have a
single at-a-glance number. Everything here is intentionally legible: tweak the
weights and you change the mood.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Score bands -> (label, emoji). Ordered low to high.
BANDS = [
    (25, "Extreme Fear", "😱"),
    (45, "Fear", "😟"),
    (56, "Neutral", "😐"),
    (75, "Greed", "🙂"),
    (101, "Extreme Greed", "🤑"),
]

# How many percent of weighted 24h move maps to the full half-range (±50).
# A ±8% weighted swing pins the momentum component to its extreme.
MOMENTUM_FULL_SCALE = 8.0

# Blend weights for the two signals (must sum to 1.0).
MOMENTUM_WEIGHT = 0.65
BREADTH_WEIGHT = 0.35


def _change_24h(coin: Dict[str, Any]) -> float:
    for key in ("priceChange1d", "priceChange24h", "priceChangePercentage24h"):
        value = coin.get(key)
        if value is not None:
            return float(value)
    return 0.0


def _market_cap(coin: Dict[str, Any]) -> float:
    value = coin.get("marketCap") or coin.get("marketCapUsd") or 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def compute_pulse(coins: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a dict describing the current market pulse.

    Keys: ``score`` (0-100 int), ``label``, ``emoji``, ``weighted_change``,
    ``breadth`` (0-1), ``advancers``, ``decliners``.
    """
    if not coins:
        return {
            "score": 50,
            "label": "Neutral",
            "emoji": "😐",
            "weighted_change": 0.0,
            "breadth": 0.5,
            "advancers": 0,
            "decliners": 0,
        }

    total_cap = sum(_market_cap(c) for c in coins)
    advancers = sum(1 for c in coins if _change_24h(c) > 0)
    decliners = len(coins) - advancers

    if total_cap > 0:
        weighted_change = sum(_change_24h(c) * _market_cap(c) for c in coins) / total_cap
    else:  # Fall back to an equal-weight average.
        weighted_change = sum(_change_24h(c) for c in coins) / len(coins)

    breadth = advancers / len(coins)

    # Momentum component: map weighted change through a clamped linear scale.
    momentum = 50.0 + (weighted_change / MOMENTUM_FULL_SCALE) * 50.0
    momentum = max(0.0, min(100.0, momentum))

    # Breadth component: fraction-up directly as 0-100.
    breadth_score = breadth * 100.0

    score = MOMENTUM_WEIGHT * momentum + BREADTH_WEIGHT * breadth_score
    score = int(round(max(0.0, min(100.0, score))))

    label, emoji = _band(score)
    return {
        "score": score,
        "label": label,
        "emoji": emoji,
        "weighted_change": weighted_change,
        "breadth": breadth,
        "advancers": advancers,
        "decliners": decliners,
    }


def _band(score: int):
    for threshold, label, emoji in BANDS:
        if score < threshold:
            return label, emoji
    return BANDS[-1][1], BANDS[-1][2]
