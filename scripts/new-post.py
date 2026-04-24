#!/usr/bin/env python3
"""
Generate a blog post using Claude Code CLI.
Usage:
  python3 scripts/new-post.py                  # auto-fetch this week's news
  python3 scripts/new-post.py "topic override" # force a topic instead of news digest
  python3 scripts/new-post.py --dry-run        # print the generated post, don't save

Requires: claude CLI authenticated (Claude Code), curl available.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO_ROOT, "src/content/posts")

NEWSAPI_KEY   = "b2e9703e570b413e89697497b21acba9"
NEWS_QUERY    = "antibody discovery OR therapeutic antibody OR immunotherapy bioinformatics"
PUBMED_QUERY  = "antibody discovery[Title/Abstract] AND (NGS OR single-cell OR bioinformatics OR immunogenomics)"

CATEGORIES = ["Science", "Antibody Engineering"]


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def fetch_news_digest():
    """Returns (digest_text, source_map) where source_map keys are SOURCE_N / PAPER_N."""
    today = datetime.now(timezone.utc)
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    params = urllib.parse.urlencode({
        "q": NEWS_QUERY, "from": week_ago, "to": today_str,
        "language": "en", "sortBy": "relevancy", "pageSize": "8",
        "apiKey": NEWSAPI_KEY,
    })
    news = fetch_json(f"https://newsapi.org/v2/everything?{params}")
    articles = news.get("articles", [])[:6]

    pubmed_params = urllib.parse.urlencode({
        "db": "pubmed", "term": PUBMED_QUERY, "reldate": "7",
        "datetype": "pdat", "retmax": "6", "retmode": "json", "sort": "relevance",
    })
    ids_data = fetch_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{pubmed_params}")
    ids = ids_data.get("esearchresult", {}).get("idlist", [])

    papers = []
    if ids:
        sum_params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
        summary = fetch_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{sum_params}")
        result = summary.get("result", {})
        for uid in (result.get("uids") or ids)[:4]:
            p = result.get(str(uid), {})
            if p.get("title"):
                authors = [a.get("name", "") for a in p.get("authors", [])][:3]
                papers.append({
                    "title": p["title"],
                    "authors": ", ".join(authors),
                    "journal": p.get("fulljournalname") or p.get("source", "PubMed"),
                    "date": p.get("pubdate", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                })

    source_map = {}
    digest = ""
    if articles:
        digest += "=== INDUSTRY NEWS (Last 7 days) ===\n\n"
        for i, a in enumerate(articles, 1):
            tag = f"SOURCE_{i}"
            src_name = a.get("source", {}).get("name", "Unknown")
            url = a.get("url", "")
            pub_date = (a.get("publishedAt") or "").split("T")[0]
            digest += f"[{tag}] {a.get('title','')}\n"
            digest += f"   Source: {src_name} | {pub_date}\n"
            digest += f"   {a.get('description','')}\n"
            digest += f"   URL: {url}\n\n"
            source_map[tag] = {
                "title": a.get("title", ""),
                "source": src_name,
                "url": url,
                "date": pub_date,
            }
    if papers:
        digest += "\n=== RECENT SCIENTIFIC PAPERS (PubMed) ===\n\n"
        for i, p in enumerate(papers, 1):
            tag = f"PAPER_{i}"
            digest += f"[{tag}] {p['title']}\n"
            digest += f"   Authors: {p['authors']}\n"
            digest += f"   Journal: {p['journal']} ({p['date']})\n"
            digest += f"   PubMed: {p['url']}\n\n"
            source_map[tag] = p

    return digest, source_map


def process_references(content, source_map):
    """Replace [SOURCE_N]/[PAPER_N] tags with inline links, append a References section."""
    # Drop any References section the model wrote despite instructions
    content = re.sub(r"##\s+References[\s\S]*$", "", content, flags=re.IGNORECASE).rstrip()

    tag_re = re.compile(r"\[(SOURCE_\d+|PAPER_\d+)\]")
    # Order of first appearance
    used = []
    seen = set()
    for m in tag_re.finditer(content):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            used.append(m.group(1))

    # Inline replacement
    for tag in used:
        ref = source_map.get(tag)
        if not ref:
            content = re.sub(rf"\[{tag}\]", "", content)
            continue
        if "authors" in ref and ref["authors"]:
            first_author = ref["authors"].split(",")[0].strip()
            link = f"[{first_author} et al., *{ref['journal']}*]({ref['url']})"
        else:
            link = f"[{ref['source']}]({ref['url']})"
        content = re.sub(rf"\[{tag}\]", link, content)

    # Build References section
    if used:
        lines = ["", "", "---", "", "## References", ""]
        n = 0
        for tag in used:
            ref = source_map.get(tag)
            if not ref:
                continue
            n += 1
            if "authors" in ref and ref["authors"]:
                lines.append(
                    f"{n}. {ref['authors']}. \"{ref['title']}\" *{ref['journal']}* ({ref['date']}). [PubMed]({ref['url']})"
                )
            else:
                lines.append(
                    f"{n}. {ref['source']}. \"{ref['title']}\" ({ref['date']}). [Link]({ref['url']})"
                )
            lines.append("")
        content = content.rstrip() + "\n".join(lines)

    return content


def build_prompt(digest_or_topic, is_topic=False):
    week_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if is_topic:
        input_section = f"TOPIC: {digest_or_topic}\n\nWrite a post on this topic in Sukhi's voice without needing to cite digest sources."
    else:
        input_section = f"Here is this week's digest (week of {week_of}):\n{digest_or_topic}\n\nPick 3 compelling angles. Connect them into a coherent narrative. Have an opinion."

    return f"""You are ghostwriting for Sukhi Singh aka Rad. He's a Product Manager at ENPICOM (Dutch bioinformatics company behind the IGX Platform — leading SaaS for therapeutic antibody discovery from NGS sequencing data). PhD in Bioinformatics, Wharton MBA.

VOICE & STYLE RULES:
- Write like a smart person talking to peers over coffee. Not a press release. Not a LinkedIn influencer.
- Short sentences. Declarative. One idea per sentence.
- Start with a bold observation or contrarian take — never "This week in..." or "Exciting developments..."
- Never use: "exciting", "groundbreaking", "cutting-edge", "thrilled", "game-changing", "delve", "landscape", "realm", "revolutionize", "leverage"
- No emoji in the body text
- Be specific. Name papers. Name methods. Name what changed and why it matters.
- Have an opinion. Say what's interesting AND what's missing or overhyped.
- Write in first person where natural.
- Paragraphs of 2-3 sentences max. White space matters.

STRUCTURE:
1. First line MUST be a markdown H1 heading: # Your Short Title Here (under 100 chars)
2. Opening hook (1-2 sentences — bold claim, question, or observation)
3. Body — 3 connected sections of 2-3 paragraphs each, weaving the sources into a narrative
4. Personal take (2-3 sentences connecting the dots from Rad's perspective)
5. Closing: "Working on something similar? I'd love to hear about it — or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com)"

LENGTH: 500-700 words
FORMAT: Markdown only. No frontmatter. No "References" section.

{input_section}"""


def run_claude(prompt):
    print("Calling claude -p ...", flush=True)
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print("claude stderr:", result.stderr[:500])
        sys.exit(1)
    return result.stdout.strip()


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    if len(text) <= 70:
        return text.rstrip("-")
    # Cut at last word boundary before 70 chars
    cut = text[:70].rsplit("-", 1)[0]
    return cut.rstrip("-")


def extract_title(content):
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # Fallback: first non-empty line
    for line in content.splitlines():
        if line.strip():
            return line.strip()[:80]
    return "Untitled"


def extract_description(content):
    lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
    if lines:
        return lines[0].strip()[:200]
    return ""


def save_post(content, dry_run=False):
    title = extract_title(content)
    description = extract_description(content)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    # Strip the H1 from the body since it goes into frontmatter
    body = re.sub(r"^#\s+.+\n?", "", content, count=1).lstrip()

    frontmatter = f"""---
title: "{title.replace('"', "'")}"
description: "{description.replace('"', "'")}"
date: {date_str}
categories: {json.dumps(CATEGORIES)}
tags: []
authors: ["Sukhi Singh"]
draft: false
---

{body}"""

    if dry_run:
        print("\n" + "="*60)
        print(f"FILE: {filename}")
        print("="*60)
        print(frontmatter)
        return None

    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(filepath, "w") as f:
        f.write(frontmatter)
    print(f"Saved: src/content/posts/{filename}")
    return filepath, filename


def commit_post(filepath, description):
    filename = os.path.basename(filepath)
    os.chdir(REPO_ROOT)
    subprocess.run(["git", "add", f"src/content/posts/{filename}"], check=True)
    result = subprocess.run(
        ["bash", "scripts/commit.sh", description],
        capture_output=False
    )
    return result.returncode == 0


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    source_map = {}
    if args:
        print(f"Using topic: {args[0]}")
        prompt = build_prompt(args[0], is_topic=True)
    else:
        print("Fetching news digest from NewsAPI + PubMed...")
        try:
            digest, source_map = fetch_news_digest()
            print(f"Digest: {len(source_map)} sources ({sum(1 for k in source_map if k.startswith('SOURCE'))} news, {sum(1 for k in source_map if k.startswith('PAPER'))} papers)")
        except Exception as e:
            print(f"News fetch failed: {e}")
            print("Falling back to general antibody/AI topic")
            digest = None

        if digest:
            prompt = build_prompt(digest, is_topic=False)
        else:
            prompt = build_prompt("Latest developments in antibody discovery and AI-driven drug design", is_topic=True)

    content = run_claude(prompt)

    if not content:
        print("No output from claude")
        sys.exit(1)

    if source_map:
        content = process_references(content, source_map)

    result = save_post(content, dry_run=dry_run)

    if not dry_run and result:
        filepath, filename = result
        slug = filename.replace(".md", "")
        commit_post(filepath, f"Add post: {extract_title(content)[:60]}")
        print(f"\nDone. Push with: GIT_CONFIG_GLOBAL=/dev/null git push origin main")
        print(f"URL after deploy: https://sukhdeepsingh.eu/blog/{slug}/")


if __name__ == "__main__":
    main()
