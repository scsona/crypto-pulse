#!/usr/bin/env python3
"""Generate the README market-pulse SVG card.

Used by the GitHub Action in .github/workflows/update-card.yml, but also handy
to run locally:

    COINSTATS_API_KEY=... python scripts/generate_card.py
    python scripts/generate_card.py --demo      # no key needed

Get a free API key at https://api.coinstats.app/
"""

from __future__ import annotations

import os
import sys

# Allow running straight from the repo root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto_pulse.cli import main  # noqa: E402

if __name__ == "__main__":
    argv = ["card", "--limit", "10", "--top", "6", "--output", "assets/market-pulse.svg"]
    # Pass through extra flags like --demo or --currency.
    argv.extend(sys.argv[1:])
    raise SystemExit(main(argv))
