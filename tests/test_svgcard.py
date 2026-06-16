"""Tests for the SVG card renderer."""

import re

from crypto_pulse.pulse import compute_pulse
from crypto_pulse.sample_data import SAMPLE_COINS, sample_chart
from crypto_pulse.svgcard import render_card


def _render():
    charts = {c["id"]: sample_chart(c["id"]) for c in SAMPLE_COINS}
    pulse = compute_pulse(SAMPLE_COINS)
    return render_card(SAMPLE_COINS, charts, pulse, "2026-01-01 00:00 UTC", top_n=6)


def test_is_valid_svg_root():
    svg = _render()
    assert svg.lstrip().startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


def test_links_to_coinstats():
    assert "coinstats.app/crypto-api" in _render()


def test_no_content_overflows_viewbox():
    svg = _render()
    width = int(re.search(r'width="(\d+)"', svg).group(1))
    xs = [float(m) for m in re.findall(r'(?:x|x1|x2|cx)="([\d.]+)"', svg)]
    for points in re.findall(r'points="([^"]+)"', svg):
        xs += [float(p.split(",")[0]) for p in points.split() if "," in p]
    assert max(xs) <= width


def test_contains_top_symbols():
    svg = _render()
    assert ">BTC<" in svg
    assert ">ETH<" in svg


def test_no_scripts_for_github_safety():
    # GitHub strips <script> from SVGs; make sure we never emit one.
    assert "<script" not in _render().lower()
