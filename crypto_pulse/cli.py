"""Command-line entry point for crypto-pulse.

Usage:
    crypto-pulse dash            # live terminal dashboard
    crypto-pulse card -o out.svg # render the README market-pulse SVG card
    crypto-pulse --help

Data comes from the CoinStats Crypto API: https://coinstats.app/api/
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List


def _load_dotenv() -> None:
    """Minimal .env loader so a key in ./.env is picked up. No dependency."""
    import os

    path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crypto-pulse",
        description="Live crypto dashboard + README SVG card, powered by the CoinStats Crypto API "
        "(https://coinstats.app/api/).",
    )
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-l", "--limit", type=int, default=10, help="number of coins to fetch (default: 10)")
    common.add_argument("-c", "--currency", default="USD", help="quote currency (default: USD)")
    common.add_argument("--period", default="24h", help="chart period for sparklines (default: 24h)")
    common.add_argument("--demo", action="store_true", help="use bundled sample data, no API key needed")

    dash = sub.add_parser("dash", parents=[common], help="run the live terminal dashboard")
    dash.add_argument("-i", "--interval", type=float, default=30.0, help="price refresh seconds (default: 30)")
    dash.add_argument("--chart-refresh", type=float, default=300.0, help="sparkline refresh seconds (default: 300)")
    dash.add_argument("--once", action="store_true", help="render a single frame and exit (good for screenshots)")
    dash.add_argument("--no-spark", action="store_true", help="skip sparkline chart calls (saves API credits)")

    card = sub.add_parser("card", parents=[common], help="render the market-pulse SVG card")
    card.add_argument("-o", "--output", default="assets/market-pulse.svg", help="output path")
    card.add_argument("--top", type=int, default=6, help="coins to show on the card (default: 6)")

    return parser


def _make_fetchers(args):
    """Return (fetch_coins, fetch_chart) closures for demo or live mode."""
    if args.demo:
        from .sample_data import SAMPLE_COINS, sample_chart

        def fetch_coins():
            return SAMPLE_COINS[: args.limit]

        def fetch_chart(coin_id):
            return sample_chart(coin_id)

        return fetch_coins, fetch_chart

    from .api import CoinStatsClient

    client = CoinStatsClient()  # raises a clear error if no key

    def fetch_coins():
        return client.get_coins(limit=args.limit, currency=args.currency)

    def fetch_chart(coin_id):
        return client.get_coin_chart(coin_id, period=args.period)

    return fetch_coins, fetch_chart


def _run_dash(args) -> int:
    from .dashboard import build_dashboard, console, run_live

    fetch_coins, fetch_chart = _make_fetchers(args)

    if args.no_spark:
        def fetch_chart(_coin_id):  # noqa: F811 - intentional override
            return []

    if args.once:
        coins = fetch_coins()
        charts: Dict[str, List[float]] = {}
        if not args.no_spark:
            for coin in coins:
                cid = coin.get("id")
                if cid:
                    try:
                        charts[cid] = fetch_chart(cid)
                    except Exception:
                        charts[cid] = []
        console.print(build_dashboard(coins, charts, args.currency, demo=args.demo))
        return 0

    try:
        run_live(
            fetch_coins,
            fetch_chart,
            currency=args.currency,
            interval=args.interval,
            chart_refresh=args.chart_refresh,
            demo=args.demo,
        )
    except KeyboardInterrupt:
        console.print("\n[dim]bye 👋[/dim]")
    return 0


def _run_card(args) -> int:
    import datetime
    import os

    from .pulse import compute_pulse
    from .svgcard import render_card

    fetch_coins, fetch_chart = _make_fetchers(args)
    coins = fetch_coins()
    charts: Dict[str, List[float]] = {}
    for coin in coins[: args.top]:
        cid = coin.get("id")
        if cid:
            try:
                charts[cid] = fetch_chart(cid)
            except Exception:
                charts[cid] = []

    pulse = compute_pulse(coins)
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    svg = render_card(coins, charts, pulse, generated_at, top_n=args.top)

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(svg)
    print(f"wrote {args.output}  ·  pulse {pulse['score']}/100 {pulse['label']} {pulse['emoji']}")
    return 0


def main(argv=None) -> int:
    _load_dotenv()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # Default to the dashboard with sensible defaults.
        args = parser.parse_args(["dash", *(argv or [])])

    try:
        if args.command == "dash":
            return _run_dash(args)
        if args.command == "card":
            return _run_card(args)
    except ValueError as exc:  # e.g. missing API key
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface a clean message
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
