"""A frozen, plausible market snapshot used by ``--demo`` mode.

Lets you preview the dashboard and generate the SVG card with no API key, so
the README renders out of the box. Live data comes from the CoinStats Crypto
API: https://api.coinstats.app/
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

# Top coins snapshot (illustrative values, not live quotes).
SAMPLE_COINS: List[Dict[str, Any]] = [
    {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC", "rank": 1,
     "price": 64210.55, "marketCap": 1_268_000_000_000, "volume": 31_400_000_000,
     "priceChange1h": 0.21, "priceChange1d": 2.34, "priceChange1w": 5.10},
    {"id": "ethereum", "name": "Ethereum", "symbol": "ETH", "rank": 2,
     "price": 3420.18, "marketCap": 411_000_000_000, "volume": 14_900_000_000,
     "priceChange1h": 0.12, "priceChange1d": 1.12, "priceChange1w": 3.42},
    {"id": "tether", "name": "Tether", "symbol": "USDT", "rank": 3,
     "price": 1.0003, "marketCap": 112_000_000_000, "volume": 48_200_000_000,
     "priceChange1h": 0.00, "priceChange1d": 0.01, "priceChange1w": -0.02},
    {"id": "binance-coin", "name": "BNB", "symbol": "BNB", "rank": 4,
     "price": 592.40, "marketCap": 87_300_000_000, "volume": 1_700_000_000,
     "priceChange1h": -0.08, "priceChange1d": -0.81, "priceChange1w": 2.05},
    {"id": "solana", "name": "Solana", "symbol": "SOL", "rank": 5,
     "price": 148.22, "marketCap": 68_900_000_000, "volume": 3_100_000_000,
     "priceChange1h": 0.45, "priceChange1d": -0.83, "priceChange1w": 8.74},
    {"id": "ripple", "name": "XRP", "symbol": "XRP", "rank": 6,
     "price": 0.5273, "marketCap": 29_300_000_000, "volume": 1_200_000_000,
     "priceChange1h": 0.05, "priceChange1d": 1.92, "priceChange1w": -1.31},
    {"id": "cardano", "name": "Cardano", "symbol": "ADA", "rank": 7,
     "price": 0.4488, "marketCap": 15_900_000_000, "volume": 410_000_000,
     "priceChange1h": -0.11, "priceChange1d": 3.06, "priceChange1w": 6.62},
    {"id": "dogecoin", "name": "Dogecoin", "symbol": "DOGE", "rank": 8,
     "price": 0.1234, "marketCap": 17_800_000_000, "volume": 980_000_000,
     "priceChange1h": 0.33, "priceChange1d": -2.14, "priceChange1w": 4.18},
]


def sample_chart(coin_id: str, points: int = 48) -> List[float]:
    """Deterministically synthesise a believable price wiggle for a coin.

    Seeded by the coin id so each coin has its own stable shape and the demo
    output is reproducible (no randomness -> identical SVG every run).
    """
    base = next((c["price"] for c in SAMPLE_COINS if c["id"] == coin_id), 100.0)
    change = next((c["priceChange1d"] for c in SAMPLE_COINS if c["id"] == coin_id), 0.0)
    seed = sum(ord(ch) for ch in coin_id)
    series: List[float] = []
    for i in range(points):
        t = i / float(points - 1)
        # Gentle trend toward the 24h change plus a couple of sine ripples.
        trend = (change / 100.0) * base * t
        ripple = math.sin(t * math.pi * 3 + seed) * base * 0.004
        ripple += math.sin(t * math.pi * 7 + seed * 0.5) * base * 0.002
        series.append(base - (change / 100.0) * base + trend + ripple)
    return series
