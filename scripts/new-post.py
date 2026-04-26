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
import threading
import time
import urllib.request
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

REPO_ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR      = os.path.join(REPO_ROOT, "src/content/posts")
SOCIAL_DIR     = os.path.join(REPO_ROOT, "social")
NEWSLETTER_DIR = os.path.join(REPO_ROOT, "newsletter")


def _load_env_file():
    """Tiny .env loader — populates os.environ with KEY=VALUE pairs from <repo>/.env."""
    env_path = os.path.join(REPO_ROOT, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file()


# ───────── Progress / status helpers ─────────

_PIPELINE_START = time.monotonic()
_STEP_NUM = 0
_STEP_TOTAL = 8  # adjusted at runtime in main()


def _fmt_dt(seconds):
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = int(seconds // 60), seconds - int(seconds // 60) * 60
    return f"{m}m {s:.0f}s"


def step(label):
    global _STEP_NUM
    _STEP_NUM += 1
    print(f"\n\033[1;36m[{_STEP_NUM}/{_STEP_TOTAL}]\033[0m {label}", flush=True)


def ok(msg, dt=None):
    suffix = f" \033[2m({_fmt_dt(dt)})\033[0m" if dt is not None else ""
    print(f"      \033[1;32m✓\033[0m {msg}{suffix}", flush=True)


def warn(msg):
    print(f"      \033[1;33m⚠\033[0m {msg}", flush=True)


def info(msg):
    print(f"      \033[2m· {msg}\033[0m", flush=True)


@contextmanager
def stopwatch():
    start = time.monotonic()
    yield lambda: time.monotonic() - start


@contextmanager
def heartbeat(label="still working", interval=10):
    """Print elapsed time every `interval` seconds during long blocking calls."""
    stop = threading.Event()

    def _tick():
        start = time.monotonic()
        while not stop.wait(interval):
            elapsed = time.monotonic() - start
            print(f"      \033[2m… {label} ({_fmt_dt(elapsed)} elapsed)\033[0m", flush=True)

    t = threading.Thread(target=_tick, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()


# ─────────────────────────────────────────────

NEWSAPI_KEY       = "b2e9703e570b413e89697497b21acba9"
UNSPLASH_KEY      = "0MBMTensZyqr9zdNG5_2d5tQGKCdSAsukPsQg_6P8So"
DEFAULT_NEWS_Q    = "antibody discovery OR therapeutic antibody OR immunotherapy bioinformatics"
DEFAULT_PUBMED_Q  = "antibody discovery[Title/Abstract] AND (NGS OR single-cell OR bioinformatics OR immunogenomics)"
UNSPLASH_DEFAULT  = "antibody molecular biology"

CATEGORIES = ["Science", "Antibody Engineering"]


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def fetch_news_digest(news_q=None, pubmed_q=None):
    """Returns (digest_text, source_map) where source_map keys are SOURCE_N / PAPER_N."""
    today = datetime.now(timezone.utc)
    month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    params = urllib.parse.urlencode({
        "q": news_q or DEFAULT_NEWS_Q, "from": month_ago, "to": today_str,
        "language": "en", "sortBy": "relevancy", "pageSize": "12",
        "apiKey": NEWSAPI_KEY,
    })
    news = fetch_json(f"https://newsapi.org/v2/everything?{params}")
    articles = news.get("articles", [])[:8]

    pubmed_params = urllib.parse.urlencode({
        "db": "pubmed", "term": pubmed_q or DEFAULT_PUBMED_Q, "reldate": "30",
        "datetype": "pdat", "retmax": "8", "retmode": "json", "sort": "relevance",
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
    """Replace [SOURCE_N]/[PAPER_N] tags with numbered inline citations [1], [2],
    and append a bullet-point references section with URLs."""
    # Drop any References section the model wrote despite instructions
    content = re.sub(r"##\s+References[\s\S]*$", "", content, flags=re.IGNORECASE).rstrip()

    tag_re = re.compile(r"\[(SOURCE_\d+|PAPER_\d+)\]")
    # Unique tags in order of first appearance → each gets a sequential number
    ordered_tags = []
    seen = set()
    for m in tag_re.finditer(content):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            ordered_tags.append(m.group(1))

    tag_to_num = {tag: i + 1 for i, tag in enumerate(ordered_tags)}

    # Replace every tag occurrence (including repeats) with its number
    def replace(match):
        tag = match.group(1)
        n = tag_to_num.get(tag)
        return f"[{n}]" if n else ""
    content = tag_re.sub(replace, content)

    if not ordered_tags:
        return content

    # Build bullet-point references section
    lines = ["", "", "---", "", "## References", ""]
    for tag in ordered_tags:
        ref = source_map.get(tag)
        if not ref:
            continue
        n = tag_to_num[tag]
        if "authors" in ref and ref["authors"]:
            year = ""
            if ref.get("date"):
                m = re.search(r"\d{4}", ref["date"])
                if m:
                    year = m.group(0)
            author_str = ref["authors"].rstrip(" .")
            if author_str.count(",") >= 2:
                author_str = author_str.split(",")[0].strip() + " et al"
            title = ref["title"].rstrip(" .")
            year_suffix = f" ({year})" if year else ""
            lines.append(
                f"- **[{n}]** {author_str}. *{title}*. {ref['journal']}{year_suffix}. <{ref['url']}>"
            )
        else:
            title = ref["title"].rstrip(" .")
            date_suffix = f" ({ref['date']})" if ref.get("date") else ""
            lines.append(
                f"- **[{n}]** {ref['source']}. *{title}*{date_suffix}. <{ref['url']}>"
            )

    return content.rstrip() + "\n".join(lines) + "\n"


def build_prompt(digest_or_topic, is_topic=False):
    week_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if is_topic:
        input_section = f"TOPIC: {digest_or_topic}\n\nWrite a post on this topic in Sukhi's voice without needing to cite digest sources."
    else:
        input_section = f"""Here is the last 30 days of industry news and PubMed papers (as of {week_of}):
{digest_or_topic}

Pick 3 compelling angles from the digest. Connect them into a coherent narrative. Have an opinion about each.

CITATION CONTRACT (important):
- Cite at least 3 different sources using the tag format [SOURCE_N] or [PAPER_N] exactly as they appear in the digest.
- These tags will be auto-replaced with numbered citations like [1], [2] in the final post, and a bullet-point References section with URLs will be appended automatically. DO NOT write your own References section.
- Do NOT invent sources, author names, or URLs.
- Do NOT write out full author names or paper titles inline — just the tag."""

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


def build_topic_prompt_with_sources(topic, digest):
    """Prompt that anchors the post on a specific topic but grounds claims in real sources."""
    week_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""You are ghostwriting for Sukhi Singh aka Rad. Product Manager at ENPICOM (Dutch bioinformatics company behind the IGX Platform — therapeutic antibody discovery from NGS). PhD in Bioinformatics, Wharton MBA.

VOICE & STYLE:
- Smart peer talking over coffee. Short, declarative sentences. One idea per sentence.
- Open with a bold observation or contrarian take. Never "This week..." or "Exciting developments..."
- Banned words: "exciting", "groundbreaking", "cutting-edge", "thrilled", "game-changing", "delve", "landscape", "realm", "revolutionize", "leverage"
- No emoji. Specific. Opinionated. First person where natural.
- Paragraphs of 2-3 sentences max.

STRUCTURE:
1. First line MUST be a markdown H1: # Short Title Here (under 100 chars)
2. Opening hook (1-2 sentences on the topic angle)
3. 2-4 body sections with H2 headings that build an argument
4. Personal take that connects the dots
5. Closing: "Working on something similar? I'd love to hear about it — or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com)"

LENGTH: 500-700 words. Markdown only, no frontmatter, no References section.

TOPIC (write specifically about this): {topic}

CITATION CONTRACT:
- You MUST cite at least 3 different sources from the digest below using the exact tag format [SOURCE_N] or [PAPER_N].
- Tags will be auto-replaced with numbered citations [1], [2] in the final post, and a References section will be appended.
- Do NOT invent sources, author names, or URLs. Do NOT write out full titles inline.
- Ground any concrete claim in a citation where a digest item supports it.

Digest of relevant sources from the last 30 days (as of {week_of}):
{digest}

Write the post on the topic "{topic}", weaving in at least 3 of the digest sources as citations. If a digest item doesn't fit the topic, skip it — don't force it."""


def fetch_hero_image(query=None):
    """Returns (image_url, photographer_name, photographer_url, unsplash_url) or None."""
    q = query or UNSPLASH_DEFAULT
    params = urllib.parse.urlencode({"query": q, "per_page": "5", "orientation": "landscape"})
    url = f"https://api.unsplash.com/search/photos?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if not results:
            return None
        photo = results[0]
        return (
            photo["urls"]["regular"],
            photo["user"]["name"],
            photo["user"]["links"]["html"],
            photo["links"]["html"],
        )
    except Exception as e:
        warn(f"Unsplash fetch failed: {e}")
        return None


def generate_social_variants(blog_content, blog_title, slug):
    """Ask Claude to spin the post into 4 LinkedIn variants + 1 Twitter thread.
    Saves to social/<slug>.md so the user can copy-paste each one across the week."""
    prompt = f"""You are repurposing one blog post into 5 social-media artifacts for Sukhi Singh aka Rad (Project Lead at ENPICOM, antibody discovery + AI). The goal: drive traffic back to the post, build an audience over time, and book speaking/consulting opportunities.

VOICE RULES (apply to ALL outputs):
- Smart practitioner talking to peers. Short declarative sentences.
- Open with a hook, never "Excited to share..." or "I'm thrilled..."
- Banned words: "exciting", "thrilled", "groundbreaking", "game-changing", "delve", "leverage", "landscape", "realm"
- Maximum ONE emoji per post, used functionally (👇 or →)
- Have an opinion. Specificity > generality.

Output EXACTLY this structure (use these headings verbatim):

## LinkedIn — Day 1: The Hook
80–120 words. The strongest contrarian/observational angle from the post. End with: "Full breakdown: [BLOG_URL] 👇"
4 hashtags max.

## LinkedIn — Day 3: The Specifics
80–120 words. Pick ONE specific paper, method, or claim from the post. Go deep on why it matters. Reference one citation by short tag (e.g., "a recent Nature Communications paper").
End with link.

## LinkedIn — Day 5: The Question
60–100 words. Provocative open question that invites comments. Tease the post's answer.
End with link.

## LinkedIn — Day 7: The Personal Take
80–120 words. First-person reflection — "What I keep coming back to this week is..." Connect the post topic to working life as a Project Lead in antibody discovery.
End with link.

## Twitter Thread (5–7 tweets)
Each tweet 240 chars max. Number them like 1/, 2/, etc. Tweet 1 must be a strong hook standing alone. Last tweet must end with: "Full post → [BLOG_URL]".

## Bluesky Post
ONE post, **240 characters MAX including the URL** (hard cap — Bluesky truncates at 300 and the URL eats ~110 chars). Count your characters carefully. Stand-alone hook. End with "→ [BLOG_URL]". No hashtags. Bluesky audience skews technical and science-leaning, so be direct and substantive.

The blog post title: {blog_title}
The slug (use in [BLOG_URL] = https://sukhdeepsingh.eu/blog/{slug}):

POST CONTENT:
{blog_content}

Write all 5 artifacts now. No commentary, just the headings and content."""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode != 0:
            warn(f"social generation: claude returned non-zero — {result.stderr[:200]}")
            return None
        social = result.stdout.strip()
        # Replace [BLOG_URL] with the actual URL
        blog_url = f"https://sukhdeepsingh.eu/blog/{slug}"
        social = social.replace("[BLOG_URL]", blog_url)

        os.makedirs(SOCIAL_DIR, exist_ok=True)
        path = os.path.join(SOCIAL_DIR, f"{slug}.md")
        header = f"# Social variants for: {blog_title}\n\nBlog URL: {blog_url}\n\nGenerated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\nCopy-paste each section into LinkedIn or Twitter on the suggested day. Spread over a week.\n\n---\n\n"
        with open(path, "w") as f:
            f.write(header + social + "\n")
        return path
    except Exception as e:
        warn(f"social variants error: {e}")
        return None


def generate_newsletter(blog_content, blog_title, blog_description, slug, digest):
    """Generate a Buttondown-ready newsletter draft from the blog post + same digest.
    Saves to newsletter/<slug>.md.
    Returns (path, subject, body_markdown) or None."""
    blog_url = f"https://sukhdeepsingh.eu/blog/{slug}"
    digest_section = (digest or "").strip()
    if digest_section:
        digest_section = f"\n\nADDITIONAL ITEMS FROM THIS WEEK'S DIGEST (use 3 for the 'Three things' block — pick items that did NOT get a full treatment in the blog post):\n\n{digest_section}"

    prompt = f"""You are ghostwriting a newsletter issue for Sukhi Singh aka Rad. Project Lead at ENPICOM, antibody discovery + AI. Audience: ~practitioners (bioinformaticians, scientists, biotech PMs, science-curious tech people). Sent via Buttondown.

GOAL: drive readers back to the blog post, build long-term trust, surface speaking + consulting opportunities through reply conversations.

VOICE:
- Smart peer over coffee. Personal, not corporate. First person.
- Banned words: "exciting", "thrilled", "groundbreaking", "game-changing", "delve", "leverage", "landscape", "realm"
- Short sentences. Plain English. NEVER "Welcome to this week's edition of..."
- Have an opinion. Have a stake. Specific > general.

LENGTH: 500–800 words TOTAL. Reads in 3–4 minutes.

OUTPUT FORMAT (use these exact section headings, verbatim — they will be parsed):

SUBJECT: <50–65 char subject line. Specific, hook-driven. NEVER "Weekly digest" or "This week".>
PREVIEW: <90–120 char preview text. Continues the subject's hook.>

---BODY---

[Opener — 2–3 sentences, no heading. Personal observation, anecdote, or a thing you noticed this week. NOT a recap.]

[Lead paragraph — 100–150 words. Introduce the blog post in newsletter voice. Tease the contrarian angle. End with: "Read the full post → {blog_url}"]

## Three things that caught my eye

→ **[Item 1 — short title]**
[2–3 sentences. What it is, what it means.]

→ **[Item 2 — short title]**
[2–3 sentences.]

→ **[Item 3 — short title]**
[2–3 sentences.]

## One thought

[A single standalone observation, 2–3 sentences. The thing a reader would screenshot. Should connect to the post's theme but stand alone.]

## What I'm working on

[1–2 sentences. Behind-the-scenes signal — current project at ENPICOM, an upcoming talk, a side build, a hike. Concrete, low-key. Avoid humble-bragging.]

[Sign-off — 1 line invitation to reply, e.g. "If any of this resonates, hit reply. I read every one." then "— Sukhi"]

[OPTIONAL P.S. — one line. Topical aside, link to /talks page, or specific ask if relevant.]

---END---

CONTEXT:
- Blog post title: {blog_title}
- Blog post description: {blog_description}
- Blog URL: {blog_url}

BLOG POST CONTENT (your reference for voice and lead-paragraph teaser — do NOT just paste it):
{blog_content}{digest_section}

Write the newsletter now. Output ONLY the SUBJECT, PREVIEW, and the BODY between ---BODY--- and ---END--- markers. Nothing else."""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode != 0:
            warn(f"newsletter generation: claude returned non-zero — {result.stderr[:200]}")
            return None
        raw = result.stdout.strip()

        # Parse subject + preview + body
        subj_m  = re.search(r"^SUBJECT:\s*(.+)$", raw, re.MULTILINE)
        prev_m  = re.search(r"^PREVIEW:\s*(.+)$", raw, re.MULTILINE)
        body_m  = re.search(r"---BODY---\s*\n([\s\S]+?)\n\s*---END---", raw)
        if not (subj_m and body_m):
            warn("newsletter parse failed (no SUBJECT or BODY markers)")
            return None

        subject = subj_m.group(1).strip().strip('"').strip("'")
        preview = (prev_m.group(1).strip().strip('"').strip("'") if prev_m else "")
        body    = body_m.group(1).strip()

        os.makedirs(NEWSLETTER_DIR, exist_ok=True)
        path = os.path.join(NEWSLETTER_DIR, f"{slug}.md")
        header = (
            f"# Newsletter draft — {blog_title}\n\n"
            f"**Subject:** {subject}\n\n"
            f"**Preview text:** {preview}\n\n"
            f"**Blog URL:** {blog_url}\n\n"
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            "_Word count target 500–800. Review, then either copy into Buttondown manually or auto-publish via API._\n\n"
            "---\n\n"
        )
        with open(path, "w") as f:
            f.write(header + body + "\n")
        return path, subject, preview, body
    except Exception as e:
        warn(f"newsletter generation error: {e}")
        return None


def send_to_buttondown(subject, body, preview="", as_draft=True):
    """Create the newsletter in Buttondown.
    By default creates a DRAFT (status=draft) so the user can review + send manually.
    Set as_draft=False to publish immediately (NOT recommended for first runs).
    Requires BUTTONDOWN_API_KEY env var. Get one at: https://buttondown.com/settings/programming"""
    api_key = os.getenv("BUTTONDOWN_API_KEY")
    if not api_key:
        warn("BUTTONDOWN_API_KEY not set, skipping (newsletter draft saved to file only)")
        return False

    payload = {
        "subject": subject,
        "body": body,
        "email_type": "public",
        "status": "draft" if as_draft else "about_to_send",
    }
    if preview:
        payload["description"] = preview  # Buttondown calls preview text "description"

    body_bytes = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.buttondown.com/v1/emails",
        data=body_bytes,
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        edit_url = f"https://buttondown.com/emails/{resp.get('id', '')}"
        info(f"draft created: {edit_url}")
        return True
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        warn(f"Buttondown failed: HTTP {e.code} — {body_text or e.reason}")
        return False
    except Exception as e:
        warn(f"Buttondown failed: {e}")
        return False


def extract_bluesky_text(social_path):
    """Pull the '## Bluesky Post' section from the social variants file."""
    try:
        with open(social_path) as f:
            data = f.read()
        # Match the Bluesky section content (between heading and next ## or EOF)
        m = re.search(r"##\s*Bluesky Post\s*\n([\s\S]+?)(?=\n##\s|\Z)", data)
        if not m:
            return None
        return m.group(1).strip()
    except Exception as e:
        warn(f"Bluesky extract failed: {e}")
        return None


def post_to_bluesky(text, blog_url=None, blog_title=None):
    """Post to Bluesky via AT Protocol.
    Requires env vars: BSKY_HANDLE (e.g. 'sukhi.bsky.social') and BSKY_APP_PASSWORD
    (generated at https://bsky.app/settings/app-passwords — DO NOT use main password)."""
    handle = os.getenv("BSKY_HANDLE")
    app_pass = os.getenv("BSKY_APP_PASSWORD")
    if not handle or not app_pass:
        warn("BSKY_HANDLE / BSKY_APP_PASSWORD not set, skipping")
        return False

    pds = "https://bsky.social"

    # Bluesky enforces 300 graphemes. Truncate while preserving the trailing URL.
    MAX_LEN = 290  # safety margin
    text = text.strip()
    if len(text) > MAX_LEN:
        # Find the last URL in the text — we want to keep it (it's the CTA)
        url_match = list(re.finditer(r"https?://\S+", text))
        if url_match:
            last_url = url_match[-1].group(0).rstrip(".,)")
            body = text[: url_match[-1].start()].rstrip(" →")
            budget = MAX_LEN - len(last_url) - 4  # " → " + 1 buffer
            if budget < 40:
                # URL is enormous — drop it, keep body
                body = text[:MAX_LEN].rsplit(" ", 1)[0] + "…"
                text = body
            else:
                if len(body) > budget:
                    body = body[:budget].rsplit(" ", 1)[0] + "…"
                text = f"{body} → {last_url}"
        else:
            # No URL in text — append blog_url if provided
            if blog_url:
                budget = MAX_LEN - len(blog_url) - 4
                body = text[:budget].rsplit(" ", 1)[0] + "…"
                text = f"{body} → {blog_url}"
            else:
                text = text[:MAX_LEN].rsplit(" ", 1)[0] + "…"
    info(f"posting {len(text)} chars to bsky")

    # 1. Create session
    session_body = json.dumps({"identifier": handle, "password": app_pass}).encode()
    req = urllib.request.Request(
        f"{pds}/xrpc/com.atproto.server.createSession",
        data=session_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            session = json.loads(r.read())
    except Exception as e:
        warn(f"Bluesky auth failed: {e}")
        return False

    access_jwt = session.get("accessJwt")
    did = session.get("did")
    if not access_jwt or not did:
        warn("Bluesky session missing token/did")
        return False

    # 2. Build post record. Detect URLs and hashtags as clickable facets.
    facets = []
    for m in re.finditer(r"https?://\S+", text):
        url = m.group(0).rstrip(".,)")
        prefix = text[: m.start()].encode("utf-8")
        target = url.encode("utf-8")
        facets.append({
            "index": {"byteStart": len(prefix), "byteEnd": len(prefix) + len(target)},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
        })
    # Hashtag facets — make #foo clickable + discoverable in topic feeds
    for m in re.finditer(r"(?<!\w)#([A-Za-z][A-Za-z0-9_]{1,63})", text):
        full_match = m.group(0)  # includes the '#'
        tag = m.group(1)         # without '#'
        prefix = text[: m.start()].encode("utf-8")
        target = full_match.encode("utf-8")
        facets.append({
            "index": {"byteStart": len(prefix), "byteEnd": len(prefix) + len(target)},
            "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag}],
        })

    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "langs": ["en"],
    }
    if facets:
        record["facets"] = facets

    # Optional: attach blog URL as embed card
    if blog_url and blog_title:
        record["embed"] = {
            "$type": "app.bsky.embed.external",
            "external": {
                "uri": blog_url,
                "title": blog_title,
                "description": "sukhdeepsingh.eu",
            },
        }

    create_body = json.dumps({
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": record,
    }).encode()

    req = urllib.request.Request(
        f"{pds}/xrpc/com.atproto.repo.createRecord",
        data=create_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_jwt}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        post_uri = resp.get("uri", "")
        m = re.match(r"at://([^/]+)/app\.bsky\.feed\.post/(.+)", post_uri)
        if m:
            web = f"https://bsky.app/profile/{handle}/post/{m.group(2)}"
            info(web)
        else:
            info(post_uri)
        return True
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        warn(f"Bluesky publish failed: HTTP {e.code} — {body or e.reason}")
        return False
    except Exception as e:
        warn(f"Bluesky publish failed: {e}")
        return False


def run_claude(prompt):
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=180
    )
    if result.returncode != 0:
        warn(f"claude returned non-zero — {result.stderr[:300]}")
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


def save_post(content, dry_run=False, image_query=None):
    title = extract_title(content)
    description = extract_description(content)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    # Strip the H1 from the body since it goes into frontmatter
    body = re.sub(r"^#\s+.+\n?", "", content, count=1).lstrip()

    # Fetch a header image from Unsplash and inject after the first paragraph
    image_line = ""
    if not dry_run:
        img = fetch_hero_image(image_query or title)
        if img:
            url, photographer, photographer_url, unsplash_url = img
            image_line = f'image: "{url}"\n'
            # Also embed photo credit at the bottom of the body
            credit = f"\n\n*Header photo by [{photographer}]({photographer_url}) on [Unsplash]({unsplash_url}).*\n"
            body = body.rstrip() + credit

    frontmatter = f"""---
title: "{title.replace('"', "'")}"
description: "{description.replace('"', "'")}"
date: {date_str}
{image_line}categories: {json.dumps(CATEGORIES)}
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
    global _STEP_TOTAL
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    no_social = "--no-social" in args
    args = [a for a in args if a not in ("--dry-run", "--no-social")]

    no_newsletter = "--no-newsletter" in args
    args = [a for a in args if a != "--no-newsletter"]
    has_bsky = bool(os.getenv("BSKY_HANDLE") and os.getenv("BSKY_APP_PASSWORD"))
    has_buttondown = bool(os.getenv("BUTTONDOWN_API_KEY"))

    # Compute total steps based on flags
    # Always: fetch sources, generate post, save
    # Conditional: process refs (if sources), Unsplash (unless dry-run), social (unless --no-social/dry-run),
    #              Bluesky (only if creds and not dry-run), commit (unless dry-run)
    _STEP_TOTAL = (
        2  # fetch + generate
        + (0 if dry_run else 1)  # save
        + (1 if not dry_run else 0)  # Unsplash (inside save_post but worth its own banner — handled there)
        + (0 if (no_social or dry_run) else 1)  # social variants
        + (1 if (has_bsky and not dry_run and not no_social) else 0)  # bluesky
        + (1 if not dry_run else 0)  # commit
    )
    # ^ Unsplash is a sub-step of save_post; we keep the count simple by folding save+image into one banner.
    _STEP_TOTAL = (
        1  # fetch sources
        + 1  # generate post
        + 1  # process refs / dry-render (always shown, even if no refs)
        + (1 if not dry_run else 0)  # save (with Unsplash inline)
        + (0 if (no_social or dry_run) else 1)  # social variants
        + (1 if (has_bsky and not dry_run and not no_social) else 0)  # bluesky
        + (0 if (no_newsletter or dry_run) else 1)  # newsletter draft
        + (1 if (has_buttondown and not dry_run and not no_newsletter) else 0)  # buttondown push
        + (1 if not dry_run else 0)  # commit
    )

    print(f"\033[1;35m▸ new-post.py\033[0m  pipeline of {_STEP_TOTAL} steps", flush=True)
    if dry_run:
        info("--dry-run: nothing will be saved or pushed")
    if no_social:
        info("--no-social: skipping social variants + Bluesky")
    if no_newsletter:
        info("--no-newsletter: skipping newsletter draft")
    if not has_bsky and not dry_run and not no_social:
        info("BSKY_HANDLE/BSKY_APP_PASSWORD not set — Bluesky step will be skipped")
    if not has_buttondown and not dry_run and not no_newsletter:
        info("BUTTONDOWN_API_KEY not set — newsletter saved to file only (no auto-draft to Buttondown)")

    source_map = {}
    digest = None
    topic = args[0] if args else None

    # ── 1. Fetch sources ──────────────────────────────────────
    step(f"Fetching sources (NewsAPI + PubMed, last 30d){' for topic: ' + topic if topic else ''}")
    if topic:
        news_q = topic
        pubmed_q = f"{topic}[Title/Abstract]"
    else:
        news_q = None
        pubmed_q = None

    try:
        with stopwatch() as t:
            digest, source_map = fetch_news_digest(news_q=news_q, pubmed_q=pubmed_q)
            n_news   = sum(1 for k in source_map if k.startswith("SOURCE"))
            n_papers = sum(1 for k in source_map if k.startswith("PAPER"))
            if topic and not source_map:
                warn(f"no sources matched topic '{topic}', retrying with default antibody query")
                digest, source_map = fetch_news_digest()
                n_news   = sum(1 for k in source_map if k.startswith("SOURCE"))
                n_papers = sum(1 for k in source_map if k.startswith("PAPER"))
        ok(f"{n_news} news + {n_papers} papers fetched", t())
    except Exception as e:
        warn(f"source fetch failed: {e}")

    # ── 2. Generate blog post ─────────────────────────────────
    step("Generating blog post via claude -p (this is the slow one)")
    if topic and digest:
        prompt = build_topic_prompt_with_sources(topic, digest)
    elif digest:
        prompt = build_prompt(digest, is_topic=False)
    else:
        prompt = build_prompt(topic or "Latest developments in antibody discovery and AI-driven drug design", is_topic=True)

    info(f"prompt length: {len(prompt):,} chars")
    with stopwatch() as t, heartbeat("claude is thinking", interval=10):
        content = run_claude(prompt)
    if not content:
        warn("no output from claude — aborting")
        sys.exit(1)
    ok(f"{len(content):,} chars generated", t())

    # ── 3. Process references ─────────────────────────────────
    step("Processing references (replace tags → numbered, append bullet list)")
    with stopwatch() as t:
        if source_map:
            content = process_references(content, source_map)
            cited = len(re.findall(r"\[\d+\]", content))
            ok(f"{cited} citation marker(s) inserted, references list appended", t())
        else:
            ok("no source map — skipping reference processing", t())

    # ── 4. Dry-run exit OR save post + Unsplash ───────────────
    if dry_run:
        print(f"\n\033[1;35m▸ dry-run output\033[0m", flush=True)
        save_post(content, dry_run=True)
        print(f"\n\033[1;35m▸ done\033[0m  total: \033[1m{_fmt_dt(time.monotonic() - _PIPELINE_START)}\033[0m", flush=True)
        return

    step("Saving post file (with Unsplash hero image)")
    with stopwatch() as t:
        result = save_post(content, dry_run=False, image_query=topic)
    if not result:
        warn("save_post returned nothing — aborting")
        sys.exit(1)
    filepath, filename = result
    slug = filename.replace(".md", "")
    title = extract_title(content)
    ok(f"src/content/posts/{filename}", t())

    # ── 5. Social variants ────────────────────────────────────
    social_path = None
    nl_result = None
    nl_subject = None
    if not no_social:
        step("Generating social variants (LinkedIn ×4 + Twitter thread + Bluesky)")
        info("another claude -p call, expect 30–60s")
        with stopwatch() as t, heartbeat("generating social copy", interval=10):
            social_path = generate_social_variants(content, title, slug)
        if social_path:
            ok(f"social/{slug}.md", t())
        else:
            warn("social variants generation failed (post still saved)")

    # ── 6. Bluesky cross-post ─────────────────────────────────
    if has_bsky and not no_social and social_path:
        step("Cross-posting to Bluesky")
        bsky_text = extract_bluesky_text(social_path)
        if bsky_text:
            with stopwatch() as t:
                posted = post_to_bluesky(bsky_text, blog_url=f"https://sukhdeepsingh.eu/blog/{slug}", blog_title=title)
            if posted:
                ok("posted to Bluesky", t())
            else:
                warn("Bluesky post failed (see error above)")
        else:
            warn("no Bluesky section found in social file — skipping")

    # ── 7. Newsletter draft ───────────────────────────────────
    nl_result = None
    if not no_newsletter:
        step("Generating newsletter draft (500–800 words, Buttondown-ready)")
        info("another claude -p call, expect 30–60s")
        with stopwatch() as t, heartbeat("drafting newsletter", interval=10):
            nl_result = generate_newsletter(content, title, extract_description(content), slug, digest)
        if nl_result:
            nl_path, nl_subject, nl_preview, nl_body = nl_result
            ok(f"newsletter/{slug}.md  ·  subject: \"{nl_subject}\"", t())
            wc = len(nl_body.split())
            info(f"~{wc} words")
        else:
            warn("newsletter generation failed (post still saved)")

    # ── 8. Push newsletter draft to Buttondown ────────────────
    if has_buttondown and not no_newsletter and nl_result:
        step("Pushing newsletter as DRAFT to Buttondown")
        with stopwatch() as t:
            sent = send_to_buttondown(nl_subject, nl_body, preview=nl_preview, as_draft=True)
        if sent:
            ok("draft created in Buttondown — review at buttondown.com/emails", t())
        else:
            warn("Buttondown push failed (newsletter saved locally)")

    # ── 9. Commit (UUID system) ───────────────────────────────
    step("Committing to git with UUID")
    with stopwatch() as t:
        commit_post(filepath, f"Add post: {title[:60]}")
    ok("committed", t())

    # ── Summary ───────────────────────────────────────────────
    total = time.monotonic() - _PIPELINE_START
    print(f"\n\033[1;35m▸ done\033[0m  total: \033[1m{_fmt_dt(total)}\033[0m", flush=True)
    print(f"  push with: \033[36mGIT_CONFIG_GLOBAL=/dev/null git push origin main\033[0m")
    print(f"  url after deploy: \033[36mhttps://sukhdeepsingh.eu/blog/{slug}/\033[0m")
    if social_path:
        print(f"  social copy: \033[36msocial/{slug}.md\033[0m")
    if nl_result:
        print(f"  newsletter:  \033[36mnewsletter/{slug}.md\033[0m  (subject: \"{nl_subject}\")")


if __name__ == "__main__":
    main()
