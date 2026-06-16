"""Render the market snapshot as a self-contained, GitHub-friendly SVG card.

The SVG uses only shapes and text (no external images or scripts) so it renders
correctly when embedded in a README via ``<img src="...svg">`` and survives
GitHub's SVG sanitiser.
"""

from __future__ import annotations

from html import escape
from typing import Any, Dict, List, Optional

W = 820
PAD = 28
ROW_H = 46
HEADER_H = 116


def _fmt_price(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:.4f}".rstrip("0").rstrip(".")


def _fmt_pct(value: float) -> str:
    arrow = "▲" if value > 0 else ("▼" if value < 0 else "▬")
    return f"{arrow} {abs(value):.2f}%"


def _pct_color(value: float) -> str:
    if value > 0:
        return "#34d399"
    if value < 0:
        return "#f87171"
    return "#9ca3af"


def _spark_path(prices: List[float], x: float, y: float, w: float, h: float) -> str:
    if not prices:
        return ""
    pts = prices
    low, high = min(pts), max(pts)
    span = (high - low) or 1.0
    n = len(pts)
    coords = []
    for i, p in enumerate(pts):
        px = x + (w * i / (n - 1 if n > 1 else 1))
        py = y + h - ((p - low) / span) * h
        coords.append(f"{px:.1f},{py:.1f}")
    return " ".join(coords)


def _pulse_marker_x(score: int, x: float, w: float) -> float:
    return x + w * (score / 100.0)


def render_card(
    coins: List[Dict[str, Any]],
    charts: Dict[str, List[float]],
    pulse: Dict[str, Any],
    generated_at: str,
    top_n: int = 6,
) -> str:
    """Return a complete SVG document string."""
    shown = coins[:top_n]
    height = HEADER_H + ROW_H * len(shown) + 56

    rows = []
    row_y = HEADER_H + 8
    for coin in shown:
        symbol = escape(str(coin.get("symbol", "")).upper())
        name = escape(str(coin.get("name", "")))
        price = float(coin.get("price", 0) or 0)
        change = float(coin.get("priceChange1d", 0) or 0)
        color = _pct_color(change)

        spark_pts = _spark_path(
            charts.get(coin.get("id", ""), []),
            x=W - PAD - 150,
            y=row_y + 8,
            w=150,
            h=ROW_H - 22,
        )
        spark = ""
        if spark_pts:
            spark = (
                f'<polyline fill="none" stroke="{color}" stroke-width="2" '
                f'stroke-linejoin="round" stroke-linecap="round" points="{spark_pts}"/>'
            )

        baseline = row_y + ROW_H / 2 + 5
        rows.append(
            f'<g>'
            f'<text x="{PAD}" y="{baseline}" class="sym">{symbol}</text>'
            f'<text x="{PAD + 78}" y="{baseline}" class="name">{name}</text>'
            f'<text x="{W - PAD - 320}" y="{baseline}" class="price" text-anchor="end">{_fmt_price(price)}</text>'
            f'<text x="{W - PAD - 175}" y="{baseline}" class="pct" fill="{color}" text-anchor="end">{_fmt_pct(change)}</text>'
            f'{spark}'
            f'<line x1="{PAD}" y1="{row_y + ROW_H}" x2="{W - PAD}" y2="{row_y + ROW_H}" class="sep"/>'
            f'</g>'
        )
        row_y += ROW_H

    # Pulse gauge geometry.
    gauge_x = W - PAD - 240
    gauge_y = 70
    gauge_w = 240
    marker_x = _pulse_marker_x(pulse["score"], gauge_x, gauge_w)
    pulse_color = _pct_color(pulse["weighted_change"]) if pulse["score"] != 50 else "#9ca3af"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="Crypto market pulse card">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0f172a"/>
      <stop offset="1" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="gauge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ef4444"/>
      <stop offset="0.5" stop-color="#eab308"/>
      <stop offset="1" stop-color="#22c55e"/>
    </linearGradient>
    <style>
      text {{ font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
      .title {{ font-size: 24px; font-weight: 700; fill: #f8fafc; }}
      .subtitle {{ font-size: 12px; fill: #64748b; }}
      .sym {{ font-size: 17px; font-weight: 700; fill: #e2e8f0; }}
      .name {{ font-size: 13px; fill: #94a3b8; }}
      .price {{ font-size: 16px; font-weight: 600; fill: #f1f5f9; }}
      .pct {{ font-size: 14px; font-weight: 600; }}
      .sep {{ stroke: #1f2a3d; stroke-width: 1; }}
      .pulse-label {{ font-size: 13px; font-weight: 700; }}
      .pulse-score {{ font-size: 13px; fill: #cbd5e1; }}
      .foot {{ font-size: 12px; fill: #64748b; }}
      .foot-link {{ font-size: 12px; font-weight: 600; fill: #38bdf8; }}
      .marker {{ animation: blink 2.4s ease-in-out infinite; }}
      @keyframes blink {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.45; }} }}
    </style>
  </defs>

  <rect x="0" y="0" width="{W}" height="{height}" rx="16" fill="url(#bg)"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="16" fill="none" stroke="#1f2a3d"/>

  <text x="{PAD}" y="44" class="title">₿ Crypto Market Pulse</text>
  <text x="{PAD}" y="64" class="subtitle">Top {len(shown)} by market cap · 24h change · updated {escape(generated_at)}</text>

  <text x="{gauge_x}" y="44" class="pulse-label" fill="{pulse_color}" text-anchor="start">{pulse["emoji"]} {escape(pulse["label"]).upper()}</text>
  <text x="{gauge_x + gauge_w}" y="44" class="pulse-score" text-anchor="end">{pulse["score"]}/100</text>
  <rect x="{gauge_x}" y="{gauge_y}" width="{gauge_w}" height="8" rx="4" fill="url(#gauge)"/>
  <g class="marker">
    <line x1="{marker_x:.1f}" y1="{gauge_y - 4}" x2="{marker_x:.1f}" y2="{gauge_y + 12}" stroke="#f8fafc" stroke-width="2.5"/>
    <circle cx="{marker_x:.1f}" cy="{gauge_y + 4}" r="5" fill="#f8fafc"/>
  </g>

  {''.join(rows)}

  <text x="{PAD}" y="{height - 18}" class="foot">Live data from the CoinStats Crypto API · </text>
  <text x="{PAD + 232}" y="{height - 18}" class="foot-link">coinstats.app/crypto-api</text>
</svg>
'''
    return svg
