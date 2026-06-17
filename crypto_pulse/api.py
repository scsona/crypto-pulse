"""Thin, dependency-light client for the CoinStats Crypto API.

Docs & free API key: https://api.coinstats.app/
Base URL: https://openapiv1.coinstats.app
Auth: send your key in the ``X-API-KEY`` header.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

BASE_URL = "https://openapiv1.coinstats.app"

# Periods accepted by the /coins/{id}/charts endpoint.
VALID_PERIODS = ("24h", "1w", "1m", "3m", "6m", "1y", "all")


class CoinStatsError(RuntimeError):
    """Raised when the CoinStats API returns a non-2xx response."""

    def __init__(self, status: int, message: str, path: str = ""):
        self.status = status
        self.message = message
        self.path = path
        super().__init__(f"CoinStats API error {status} on {path}: {message}")


class CoinStatsClient:
    """Minimal CoinStats Open API client built on the standard library.

    Parameters
    ----------
    api_key:
        Your CoinStats API key. Falls back to the ``COINSTATS_API_KEY``
        environment variable. Grab a free key at
        https://api.coinstats.app/
    timeout:
        Per-request timeout in seconds.
    max_retries:
        How many times to retry on transient errors (429 / 5xx).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 15.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.environ.get("COINSTATS_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set COINSTATS_API_KEY or pass api_key=... "
                "Get a free key at https://api.coinstats.app/"
            )
        self.timeout = timeout
        self.max_retries = max_retries

    # -- low level ---------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        query = ""
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            query = "?" + urllib.parse.urlencode(clean)
        url = f"{BASE_URL}{path}{query}"

        request = urllib.request.Request(url, method="GET")
        request.add_header("X-API-KEY", self.api_key)
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", "crypto-pulse/1.0 (+https://github.com/scsona/crypto-pulse)")

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    payload = resp.read().decode("utf-8")
                return json.loads(payload) if payload else None
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", "replace")
                message = body
                try:
                    message = json.loads(body).get("message", body)
                except (ValueError, AttributeError):
                    pass
                # Retry only on rate limiting / server hiccups.
                if exc.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(1.5 * (attempt + 1))
                    last_error = exc
                    continue
                raise CoinStatsError(exc.code, str(message), path) from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < self.max_retries:
                    time.sleep(1.5 * (attempt + 1))
                    last_error = exc
                    continue
                raise CoinStatsError(0, str(exc), path) from exc

        # Should not get here, but guard anyway.
        raise CoinStatsError(0, str(last_error), path)

    # -- endpoints ---------------------------------------------------------

    def get_coins(
        self,
        limit: int = 10,
        page: int = 1,
        currency: str = "USD",
    ) -> List[Dict[str, Any]]:
        """Return the top coins by rank.

        Wraps ``GET /coins``. The endpoint returns ``{"result": [...]}``;
        we normalise to just the list and tolerate a bare-list response too.
        """
        data = self._get(
            "/coins",
            {"limit": limit, "page": page, "currency": currency},
        )
        if isinstance(data, dict):
            return data.get("result", []) or []
        if isinstance(data, list):
            return data
        return []

    def get_coin(self, coin_id: str, currency: str = "USD") -> Dict[str, Any]:
        """Return a single coin's details. Wraps ``GET /coins/{coinId}``."""
        data = self._get(f"/coins/{coin_id}", {"currency": currency})
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data or {}

    def get_coin_chart(self, coin_id: str, period: str = "24h") -> List[float]:
        """Return a flat list of prices for a coin over ``period``.

        Wraps ``GET /coins/{coinId}/charts``. The endpoint returns an array of
        ``[timestamp, price, ...]`` points; we extract just the price series,
        which is what sparklines and mini-charts need.
        """
        if period not in VALID_PERIODS:
            raise ValueError(f"period must be one of {VALID_PERIODS}, got {period!r}")
        data = self._get(f"/coins/{coin_id}/charts", {"period": period})
        points = data
        if isinstance(data, dict):
            points = data.get("result") or data.get("chart") or []
        prices: List[float] = []
        for point in points or []:
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                prices.append(float(point[1]))
            elif isinstance(point, (int, float)):
                prices.append(float(point))
        return prices

    def get_markets(self) -> Dict[str, Any]:
        """Return global market stats. Wraps ``GET /markets``."""
        data = self._get("/markets")
        if isinstance(data, dict):
            return data.get("result", data)
        return {}
