#!/usr/bin/env python3
"""
Aggregate the past 7 days of business news for the antibody/biologics companies
in src/data/companies.json. Sources:

  - NewsAPI (uses key already in new-post.py)
  - Google News RSS, scoped to site:reuters.com / bloomberg.com / ft.com / fiercebiotech.com / endpts.com / biopharmadive.com

Each story is matched against company tickers + names, then categorized by Claude
(claude -p) into M&A / Approvals / Trials / Earnings / Pipeline / Other.

Output: src/data/business-news.json — consumed by /business page at build time.

Usage:
  python3 scripts/fetch-business-news.py
  python3 scripts/fetch-business-news.py --no-categorize    # skip Claude pass (faster, all items go to "Other")
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape

REPO_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANIES  = os.path.join(REPO_ROOT, "src/data/companies.json")
OUT_PATH   = os.path.join(REPO_ROOT, "src/data/business-news.json")

NEWSAPI_KEY = "b2e9703e570b413e89697497b21acba9"

# Sites whose coverage of biotech business is reliable, queried via Google News RSS
RSS_SITES = [
    "reuters.com",
    "bloomberg.com",
    "ft.com",
    "fiercebiotech.com",
    "endpts.com",
    "biopharmadive.com",
    "statnews.com",
]

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}


def http_get(url, timeout=12):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_newsapi(query, days=7):
    today = datetime.now(timezone.utc)
    since = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    params = urllib.parse.urlencode({
        "q": query,
        "from": since,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": "30",
        "apiKey": NEWSAPI_KEY,
    })
    try:
        data = json.loads(http_get(f"https://newsapi.org/v2/everything?{params}"))
        return [
            {
                "title": a.get("title", "").strip(),
                "url": a.get("url", ""),
                "source": (a.get("source") or {}).get("name") or "",
                "published": (a.get("publishedAt") or "").split("T")[0],
                "description": a.get("description", "") or "",
                "_origin": "newsapi",
            }
            for a in data.get("articles", [])
            if a.get("title") and a.get("url")
        ]
    except Exception as e:
        print(f"  NewsAPI fetch failed: {e}")
        return []


def fetch_google_news_rss(query, days=7):
    """Returns articles from Google News RSS for a given query (already site-scoped)."""
    when = f"when:{days}d"
    full_q = f"{query} {when}"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(full_q)}&hl=en-US&gl=US&ceid=US:en"
    try:
        xml_bytes = http_get(url)
    except Exception as e:
        print(f"  Google News RSS fetch failed for q='{query[:40]}': {e}")
        return []

    items = []
    try:
        root = ET.fromstring(xml_bytes)
        for it in root.iter("item"):
            title = unescape((it.findtext("title") or "").strip())
            link = (it.findtext("link") or "").strip()
            pub = (it.findtext("pubDate") or "").strip()
            source = (it.find("source").text if it.find("source") is not None else "")
            # Pub is RFC822, e.g. "Mon, 21 Apr 2026 13:45:00 GMT"
            try:
                from email.utils import parsedate_to_datetime
                pub_iso = parsedate_to_datetime(pub).strftime("%Y-%m-%d") if pub else ""
            except Exception:
                pub_iso = ""
            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "source": source,
                    "published": pub_iso,
                    "description": "",
                    "_origin": "google_news_rss",
                })
    except Exception as e:
        print(f"  Google News RSS parse failed: {e}")
    return items


def dedupe(items):
    seen = set()
    out = []
    for i in items:
        # Dedupe on cleaned title (Google News appends source after dash)
        key = re.sub(r"\s*-\s*[^-]+$", "", i["title"]).strip().lower()[:120]
        if key in seen:
            continue
        seen.add(key)
        out.append(i)
    return out


def tag_tickers(items, companies):
    """For each article, attach the list of company tickers mentioned by name or ticker symbol."""
    # Build name → ticker lookup
    pairs = []
    for c in companies:
        name = c["name"]
        ticker = c["ticker"]
        # Use the most distinctive 1–2 words of the name to avoid false positives
        # (e.g. "Roche" → "Roche", "Bristol Myers Squibb" → "Bristol Myers")
        short = " ".join(name.split()[:2])
        pairs.append((re.compile(rf"\b{re.escape(short)}\b", re.I), ticker))
        # Also match bare ticker if it's 4+ chars (avoids matching "MR" etc as MRK)
        if len(ticker) >= 4 and ticker.isalpha():
            pairs.append((re.compile(rf"\b{re.escape(ticker)}\b"), ticker))

    for item in items:
        text = f"{item['title']} {item.get('description','')}"
        matched = []
        for rx, ticker in pairs:
            if rx.search(text) and ticker not in matched:
                matched.append(ticker)
        item["tickers"] = matched
    return items


def categorize_with_claude(items, batch_size=15):
    """Ask Claude to label each item with one of:
    M&A | Approvals | Trials | Earnings | Pipeline | Other.
    Returns items with item['category'] set.

    Batched to keep prompt size sensible."""
    if not items:
        return items

    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        numbered = "\n".join(f"{i+1}. {b['title']}" for i, b in enumerate(batch))
        prompt = f"""You are categorizing biotech / pharma business news headlines.

For each numbered headline, output ONE of these labels (and ONLY the label):
- M&A          (mergers, acquisitions, deals, partnerships, license agreements)
- Approvals    (FDA/EMA approval, PDUFA, orphan designation, regulatory clearance)
- Trials       (clinical trial readouts, Phase 1/2/3 results, study news)
- Earnings     (quarterly results, revenue, guidance, layoffs, financial moves)
- Pipeline     (drug development progress, new indications, internal R&D updates)
- Other        (anything else: policy, conferences, leadership changes)

Output format: just `1: M&A` then `2: Trials` etc., one per line. NO commentary.

Headlines:
{numbered}"""
        try:
            r = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                print(f"  claude categorize batch {start}: non-zero — {r.stderr[:120]}")
                continue
            for line in r.stdout.strip().splitlines():
                m = re.match(r"^\s*(\d+)\s*[:.\-]\s*(M&A|Approvals|Trials|Earnings|Pipeline|Other)", line, re.I)
                if not m:
                    continue
                idx = int(m.group(1)) - 1
                cat = m.group(2)
                # Normalize case
                cat_map = {"m&a": "M&A", "approvals": "Approvals", "trials": "Trials",
                           "earnings": "Earnings", "pipeline": "Pipeline", "other": "Other"}
                cat = cat_map.get(cat.lower(), cat)
                if 0 <= idx < len(batch):
                    batch[idx]["category"] = cat
        except Exception as e:
            print(f"  claude categorize error: {e}")

    # Default leftover
    for it in items:
        it.setdefault("category", "Other")
    return items


def main():
    no_categorize = "--no-categorize" in sys.argv
    with open(COMPANIES) as f:
        companies = json.load(f)

    print(f"Aggregating business news for {len(companies)} companies (last 7 days)...")
    print()

    all_items = []

    # 1. NewsAPI: one broad antibody-business query
    print("→ NewsAPI: antibody/biologics business query")
    newsapi_q = "(antibody OR biologic OR monoclonal) AND (acquisition OR merger OR FDA OR approval OR clinical OR earnings)"
    items = fetch_newsapi(newsapi_q, days=7)
    print(f"  {len(items)} items")
    all_items.extend(items)

    # 2. Google News RSS per source, with antibody-discovery scope
    rss_query_core = "(antibody OR biologic OR monoclonal OR ADC OR bispecific)"
    for site in RSS_SITES:
        q = f"{rss_query_core} site:{site}"
        items = fetch_google_news_rss(q, days=7)
        print(f"→ {site:>22}: {len(items)} items")
        all_items.extend(items)

    print()
    print(f"Total fetched: {len(all_items)}")

    # 3. Dedupe
    all_items = dedupe(all_items)
    print(f"After dedupe:  {len(all_items)}")

    # 4. Tag tickers
    all_items = tag_tickers(all_items, companies)
    tagged = sum(1 for i in all_items if i.get("tickers"))
    print(f"Items mentioning ≥1 tracked company: {tagged}")

    # 5. Filter to company-relevant items only (or keep top noise too?)
    relevant = [i for i in all_items if i.get("tickers")]

    # If we got very few hits, fall back to keeping items with strong biz keywords
    if len(relevant) < 8:
        keywords_rx = re.compile(r"\b(antibody|biologic|monoclonal|FDA|EMA|approval|acquisition|merger|Phase [123]|trial|earnings)\b", re.I)
        relevant = [i for i in all_items if keywords_rx.search(i["title"])]
        print(f"  (fallback to keyword filter — kept {len(relevant)})")

    # Sort newest first
    relevant.sort(key=lambda x: x.get("published") or "", reverse=True)

    # Cap at 60 — keep page tractable
    relevant = relevant[:60]

    # 6. Categorize via Claude
    if not no_categorize and relevant:
        print(f"\nCategorizing {len(relevant)} items with Claude (batched)...")
        relevant = categorize_with_claude(relevant)
    else:
        for it in relevant:
            it["category"] = "Other"

    # 7. Save
    payload = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "items": relevant,
    }
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n→ src/data/business-news.json  ({len(relevant)} items)")
    by_cat = {}
    for i in relevant:
        by_cat[i["category"]] = by_cat.get(i["category"], 0) + 1
    for cat, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"   {cat:<10}  {n}")


if __name__ == "__main__":
    main()
