"""The live terminal dashboard, built with `rich`."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .pulse import compute_pulse
from .sparkline import sparkline

console = Console()


def _fmt_price(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:.4f}".rstrip("0").rstrip(".")


def _fmt_big(value: float) -> str:
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if value >= size:
            return f"${value / size:.2f}{unit}"
    return f"${value:.0f}"


def _pct_text(value: Optional[float]) -> Text:
    if value is None:
        return Text("—", style="dim")
    arrow = "▲" if value > 0 else ("▼" if value < 0 else "▬")
    style = "bold green" if value > 0 else ("bold red" if value < 0 else "dim")
    return Text(f"{arrow} {abs(value):.2f}%", style=style)


def _gauge_bar(score: int, width: int = 32) -> Text:
    """A red→yellow→green gradient bar with a marker at ``score``."""
    bar = Text()
    marker_pos = int(round(score / 100 * (width - 1)))
    for i in range(width):
        frac = i / (width - 1)
        if frac < 0.4:
            color = "red"
        elif frac < 0.6:
            color = "yellow"
        else:
            color = "green"
        if i == marker_pos:
            bar.append("◆", style="bold white")
        else:
            bar.append("━", style=color)
    return bar


def _coin_change(coin: Dict[str, Any], key: str) -> Optional[float]:
    value = coin.get(key)
    return float(value) if value is not None else None


def build_table(
    coins: List[Dict[str, Any]],
    charts: Dict[str, List[float]],
    currency: str,
) -> Table:
    table = Table(
        expand=True,
        box=None,
        pad_edge=False,
        header_style="bold cyan",
        row_styles=["", "on grey7"],
    )
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Coin", style="bold")
    table.add_column("Price", justify="right")
    table.add_column("1h", justify="right")
    table.add_column("24h", justify="right")
    table.add_column("7d", justify="right")
    table.add_column("24h trend", justify="left")
    table.add_column("Mkt Cap", justify="right", style="dim")

    for coin in coins:
        spark_prices = charts.get(coin.get("id", ""), [])
        change_1d = _coin_change(coin, "priceChange1d") or 0.0
        spark_style = "green" if change_1d > 0 else ("red" if change_1d < 0 else "dim")
        spark = Text(sparkline(spark_prices, width=16) or "·", style=spark_style)

        symbol = str(coin.get("symbol", "")).upper()
        name = str(coin.get("name", ""))
        coin_cell = Text.assemble((symbol, "bold white"), ("  " + name, "dim"))

        table.add_row(
            str(coin.get("rank", "")),
            coin_cell,
            _fmt_price(float(coin.get("price", 0) or 0)),
            _pct_text(_coin_change(coin, "priceChange1h")),
            _pct_text(_coin_change(coin, "priceChange1d")),
            _pct_text(_coin_change(coin, "priceChange1w")),
            spark,
            _fmt_big(float(coin.get("marketCap", 0) or 0)),
        )
    return table


def build_pulse_panel(coins: List[Dict[str, Any]]) -> Panel:
    pulse = compute_pulse(coins)

    gainers = sorted(coins, key=lambda c: c.get("priceChange1d", 0) or 0, reverse=True)
    top_gain = gainers[0] if gainers else None
    top_loss = gainers[-1] if gainers else None

    body = Text()
    body.append(f"{pulse['emoji']}  ", style="")
    body.append(f"{pulse['label']}", style="bold")
    body.append(f"   {pulse['score']}/100\n", style="dim")
    body.append(_gauge_bar(pulse["score"]))
    body.append("\n\n")
    body.append("Breadth  ", style="dim")
    body.append(f"{pulse['advancers']}▲ ", style="green")
    body.append(f"{pulse['decliners']}▼", style="red")
    body.append(f"   ({pulse['breadth'] * 100:.0f}% up)\n", style="dim")
    body.append("Weighted 24h  ", style="dim")
    body.append(_pct_text(pulse["weighted_change"]))

    if top_gain is not None and top_loss is not None:
        body.append("\n\nTop gainer  ", style="dim")
        body.append(f"{str(top_gain.get('symbol','')).upper()} ", style="bold")
        body.append(_pct_text(top_gain.get("priceChange1d")))
        body.append("\nTop loser   ", style="dim")
        body.append(f"{str(top_loss.get('symbol','')).upper()} ", style="bold")
        body.append(_pct_text(top_loss.get("priceChange1d")))

    return Panel(body, title="[bold]Market Pulse[/bold]", border_style="cyan", padding=(1, 2))


def build_dashboard(
    coins: List[Dict[str, Any]],
    charts: Dict[str, List[float]],
    currency: str,
    demo: bool = False,
) -> Group:
    header = Text()
    header.append("₿ CRYPTO PULSE", style="bold yellow")
    header.append("  ·  live crypto dashboard powered by the ", style="dim")
    header.append("CoinStats Crypto API", style="cyan")
    if demo:
        header.append("   [DEMO DATA]", style="bold magenta")

    footer = Text(
        "data: api.coinstats.app   ·   ctrl-c to quit",
        style="dim",
        justify="center",
    )

    return Group(
        Align.center(header),
        Text(""),
        build_table(coins, charts, currency),
        Text(""),
        build_pulse_panel(coins),
        Text(""),
        footer,
    )


def run_live(
    fetch_coins,
    fetch_chart,
    currency: str = "USD",
    interval: float = 30.0,
    chart_refresh: float = 300.0,
    demo: bool = False,
):
    """Render the dashboard and refresh it on an interval.

    ``fetch_coins()`` returns the coin list; ``fetch_chart(coin_id)`` returns a
    price series. Charts refresh less often than prices to conserve API credits.
    """
    charts: Dict[str, List[float]] = {}
    last_chart_at = 0.0

    def refresh_charts(coins):
        result = {}
        for coin in coins:
            cid = coin.get("id")
            if not cid:
                continue
            try:
                result[cid] = fetch_chart(cid)
            except Exception:  # one bad chart shouldn't kill the dashboard
                result[cid] = charts.get(cid, [])
        return result

    coins = fetch_coins()
    charts = refresh_charts(coins)
    last_chart_at = time.monotonic()

    with Live(
        build_dashboard(coins, charts, currency, demo),
        console=console,
        screen=True,
        refresh_per_second=4,
    ) as live:
        while True:
            time.sleep(interval)
            try:
                coins = fetch_coins()
            except Exception as exc:
                console.log(f"[red]price refresh failed:[/red] {exc}")
                continue
            now = time.monotonic()
            if now - last_chart_at >= chart_refresh:
                charts = refresh_charts(coins)
                last_chart_at = now
            live.update(build_dashboard(coins, charts, currency, demo))
