#!/usr/bin/env python3
"""
Fetch latest closing price + 1-day & 5-day % change for every ticker in companies.json.
Saves to src/data/prices.json — consumed by /business page at build time.

Usage:
  pip3 install yfinance       # one-time
  python3 scripts/fetch-prices.py

Run weekly (or via GitHub Action) to refresh data baked into the static site.
yfinance handles Yahoo's cookie/crumb auth + endpoint fallback internally.
"""

import json
import os
import sys
from datetime import datetime, timezone

try:
    import yfinance as yf
except ImportError:
    sys.exit("Missing yfinance. Run: pip3 install yfinance")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANIES = os.path.join(REPO_ROOT, "src/data/companies.json")
OUT_PATH  = os.path.join(REPO_ROOT, "src/data/prices.json")


def fetch_one(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="7d", auto_adjust=False)
        closes = hist["Close"].dropna().tolist()
        if len(closes) < 2:
            return None
        last = closes[-1]
        prev = closes[-2]
        first = closes[0]
        info = t.fast_info  # cheap currency lookup
        currency = getattr(info, "currency", "USD") or "USD"
        return {
            "ticker": ticker,
            "last_close": round(last, 2),
            "prev_close": round(prev, 2),
            "pct_change_1d": round((last - prev) / prev * 100, 2) if prev else 0,
            "pct_change_5d": round((last - first) / first * 100, 2) if first else 0,
            "currency": currency,
        }
    except Exception as e:
        print(f"  ✗ {ticker}: {type(e).__name__}: {str(e)[:80]}")
        return None


def main():
    with open(COMPANIES) as f:
        companies = json.load(f)

    print(f"Fetching prices for {len(companies)} tickers via yfinance...")
    out = {}
    fail = 0
    for c in companies:
        ticker = c["ticker"]
        result = fetch_one(ticker)
        if result:
            out[ticker] = result
            arrow = "▲" if result["pct_change_1d"] >= 0 else "▼"
            print(f"  ✓ {ticker:<12} {result['last_close']:>9} {result['currency']}  {arrow} {result['pct_change_1d']:+.2f}% 1d   {result['pct_change_5d']:+.2f}% 5d")
        else:
            fail += 1

    payload = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "prices": out,
    }
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n→ src/data/prices.json  ({len(out)} ok, {fail} failed)")


if __name__ == "__main__":
    main()
