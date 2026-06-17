"""crypto-pulse — a live terminal crypto dashboard and self-updating README
SVG card, powered by the CoinStats Crypto API (https://api.coinstats.app/).
"""

from __future__ import annotations

__version__ = "1.0.0"

from .api import CoinStatsClient, CoinStatsError
from .pulse import compute_pulse
from .sparkline import sparkline
from .svgcard import render_card

__all__ = [
    "__version__",
    "CoinStatsClient",
    "CoinStatsError",
    "compute_pulse",
    "sparkline",
    "render_card",
]
