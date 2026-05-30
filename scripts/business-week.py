#!/usr/bin/env python3
"""
Weekly market-analysis post generator.

Reads:
  - src/data/companies.json
  - src/data/prices.json        (run scripts/fetch-prices.py first)
  - src/data/business-news.json (run scripts/fetch-business-news.py first)

Generates a 600–800 word "Week in antibody business" post via `claude -p`.
Saves as src/content/posts/business-<YYYY-MM-DD>-<slug>.md and commits via the
UUID commit script. The /business page picks it up automatically as the latest
market analysis card (it filters posts whose id starts with "business-").

Usage:
  python3 scripts/business-week.py
  python3 scripts/business-week.py --dry-run      # print, don't save
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

REPO_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANIES  = os.path.join(REPO_ROOT, "src/data/companies.json")
PRICES     = os.path.join(REPO_ROOT, "src/data/prices.json")
NEWS       = os.path.join(REPO_ROOT, "src/data/business-news.json")
POSTS_DIR  = os.path.join(REPO_ROOT, "src/content/posts")


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    text = re.sub(r"-+", "-", text)
    if len(text) <= 60:
        return text
    return text[:60].rsplit("-", 1)[0]


def build_digest(companies, prices, news):
    """Compose a structured digest the model can reason over."""
    name_by_ticker = {c["ticker"]: c["name"] for c in companies}
    cat_by_ticker  = {c["ticker"]: c["category"] for c in companies}

    # Movers: top 5 up and top 5 down on 5-day change
    rows = []
    for tick, p in prices.get("prices", {}).items():
        rows.append((tick, p.get("pct_change_5d", 0), p.get("pct_change_1d", 0), p.get("last_close", 0), p.get("currency", "USD")))
    rows.sort(key=lambda r: r[1])
    losers = rows[:5]
    winners = rows[-5:][::-1]

    movers_block = "TOP 5-DAY MOVERS:\n"
    movers_block += "  Up:\n"
    for tick, p5, p1, px, cur in winners:
        movers_block += f"    {tick:<10} {name_by_ticker.get(tick, '')}  +{p5:.2f}% 5d, {p1:+.2f}% 1d  ({px} {cur})\n"
    movers_block += "  Down:\n"
    for tick, p5, p1, px, cur in losers:
        movers_block += f"    {tick:<10} {name_by_ticker.get(tick, '')}  {p5:+.2f}% 5d, {p1:+.2f}% 1d  ({px} {cur})\n"

    # News by category
    items = news.get("items", [])
    by_cat = {}
    for it in items:
        by_cat.setdefault(it.get("category", "Other"), []).append(it)

    news_block = "NEWS HEADLINES (last 7 days, grouped by category):\n"
    cat_order = ["M&A", "Approvals", "Trials", "Earnings", "Pipeline", "Other"]
    for cat in cat_order:
        if not by_cat.get(cat):
            continue
        news_block += f"\n  [{cat}]\n"
        for it in by_cat[cat][:8]:
            tickers = " ".join(f"({t})" for t in it.get("tickers", [])[:3])
            news_block += f"    - {it['title']} {tickers} | {it.get('source','')} | {it.get('url','')}\n"

    return movers_block + "\n" + news_block


def build_prompt(digest, week_of):
    return f"""You are ghostwriting a weekly market analysis post for Sukhi Singh aka Rad. Project Lead at ENPICOM, antibody discovery + AI. The audience: bioinformaticians, biotech PMs, BD/strategy people at pharma. They want to know what just happened and what it means for antibody-drug R&D.

VOICE & STYLE:
- Smart practitioner over coffee. Short, declarative. One idea per sentence.
- Never "This week in pharma..." or "Here's a roundup..." Open with a real observation about the data.
- Banned words: "exciting", "thrilled", "groundbreaking", "game-changing", "delve", "leverage", "landscape", "realm"
- Specific. Opinionated. Connect dots, don't just list.
- No emoji.

STRUCTURE:
1. First line MUST be: # Title  (a real headline, 70 chars max, hook-driven, no "Weekly Roundup")
2. Opening hook (1–2 sentences) tying together the week's most consequential signal
3. THREE sections (use ## H2 headings):
   - One on the biggest market move and why
   - One on the biggest news/M&A/approval and what it tells us about the strategic direction of the field
   - One on a contrarian or under-covered angle (something most people will miss)
4. A short "What I'm watching" bullet list — 3 specific things to track next week
5. Close: "Working on something similar? I'd love to hear about it — or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com)"

LENGTH: 600–800 words. Markdown. NO frontmatter. Cite specific tickers in parentheses, e.g. "(MRK)". Reference real headlines from the digest where they support a point. Don't invent numbers.

Week of: {week_of}

{digest}

Write the post now."""


def run_claude(prompt):
    r = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=240)
    if r.returncode != 0:
        print(f"claude failed: {r.stderr[:300]}")
        sys.exit(1)
    return r.stdout.strip()


def extract_title(content):
    m = re.match(r"^#\s+(.+?)$", content.split("\n", 1)[0])
    return m.group(1).strip() if m else "Weekly antibody business"


def extract_description(content):
    body = re.sub(r"^#\s+.+\n", "", content, count=1).strip()
    p = re.search(r"^([^#\n][^\n]{40,}\.)", body, re.MULTILINE)
    return (p.group(1).replace('"', "'")[:200] if p else "Weekly market analysis on antibody discovery business.")


def save(content, dry_run):
    title = extract_title(content)
    desc  = extract_description(content)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug  = f"business-{today}-{slugify(title)}"
    filename = f"{slug}.md"
    body = re.sub(r"^#\s+.+\n?", "", content, count=1).lstrip()

    fm = (
        "---\n"
        f'title: "{title.replace(chr(34), chr(39))}"\n'
        f'description: "{desc}"\n'
        f"date: {today}\n"
        'categories: ["Business", "Antibody Engineering"]\n'
        'tags: ["weekly-business", "market-analysis"]\n'
        'authors: ["Sukhi Singh"]\n'
        "draft: false\n"
        "---\n\n"
        f"{body}\n"
    )

    if dry_run:
        print("\n" + "=" * 60)
        print(f"FILE: {filename}")
        print("=" * 60)
        print(fm)
        return None

    os.makedirs(POSTS_DIR, exist_ok=True)
    path = os.path.join(POSTS_DIR, filename)
    with open(path, "w") as f:
        f.write(fm)
    return path, slug, title


def commit(path, title):
    os.chdir(REPO_ROOT)
    subprocess.run(["git", "add", os.path.relpath(path, REPO_ROOT)], check=True)
    subprocess.run(["bash", "scripts/commit.sh", f"Business week: {title[:60]}"])


def main():
    dry_run = "--dry-run" in sys.argv

    if not os.path.exists(PRICES):
        sys.exit(f"Missing {PRICES}. Run scripts/fetch-prices.py first.")
    if not os.path.exists(NEWS):
        sys.exit(f"Missing {NEWS}. Run scripts/fetch-business-news.py first.")

    with open(COMPANIES) as f:
        companies = json.load(f)
    with open(PRICES) as f:
        prices = json.load(f)
    with open(NEWS) as f:
        news = json.load(f)

    week_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print("Building digest from prices + news...")
    digest = build_digest(companies, prices, news)
    print(f"  digest length: {len(digest):,} chars")

    print("Generating market analysis via claude -p (~30–60s)...")
    prompt = build_prompt(digest, week_of)
    content = run_claude(prompt)
    print(f"  generated: {len(content):,} chars")

    result = save(content, dry_run=dry_run)
    if dry_run or not result:
        return
    path, slug, title = result
    print(f"Saved: src/content/posts/{slug}.md")
    commit(path, title)
    print(f"\nDone. Push: GIT_CONFIG_GLOBAL=/dev/null git push origin main")
    print(f"Will appear at: https://radtech.nl/blog/{slug}/")
    print(f"And as latest analysis on: https://radtech.nl/business/")


if __name__ == "__main__":
    main()
