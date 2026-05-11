#!/usr/bin/env python3
"""
Check multiple job boards for new UI/UX vacancies.
If found, analyze with Groq and add to vacancies.md.
Run via cron every 2 hours.
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
MD_FILE = os.path.join(BASE_DIR, "vacancies.md")
ANALYSES_FILE = os.path.join(BASE_DIR, "analyses.json")
LOG_FILE = os.path.join(BASE_DIR, "check.log")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Load config — keywords and sources come from config.py
try:
    from config import TITLE_KEYWORDS, SOURCES
    from config import NEGATIVE_TITLE_KEYWORDS as _NEG_KW
    from config import POSITIVE_OVERRIDE_KEYWORDS as _POS_OVERRIDE
except ImportError:
    TITLE_KEYWORDS = ['design', 'ux', 'ui', 'product design', 'дизайн']
    SOURCES = {}
    _NEG_KW = []
    _POS_OVERRIDE = []

KEYWORDS = [k.lower() for k in TITLE_KEYWORDS]
NEGATIVES = [k.lower() for k in _NEG_KW]
POSITIVE_OVERRIDES = [k.lower() for k in _POS_OVERRIDE]


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        log(f"  Fetch error for {url}: {e}")
        return ""


def get_existing_urls():
    if not os.path.exists(MD_FILE):
        return set()
    with open(MD_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    return set(re.findall(r'\((https?://[^)]+)\)', content))


def normalize_title(title):
    """Normalize a vacancy title for near-duplicate detection.
    Lowercases, strips punctuation, collapses whitespace.
    Example: "Senior BI Engineer (XTB) — Remote" → "senior bi engineer xtb remote"
    """
    t = title.lower().strip()
    t = re.sub(r'[^\w\s]', ' ', t)
    t = ' '.join(t.split())
    return t


def get_existing_normalized_titles():
    """Return a set of normalized titles already present in vacancies.md."""
    if not os.path.exists(MD_FILE):
        return set()
    with open(MD_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    return {normalize_title(m.group(1)) for m in re.finditer(r'^\- \[(.+?)\]', content, re.MULTILINE)}


def is_relevant(title):
    """Check if vacancy title is relevant based on positive/negative keywords.

    Returns False if:
    - No positive keyword matches, OR
    - A negative keyword matches AND no positive-override keyword is present
      (e.g. 'Power BI Developer' is skipped, but 'Looker + Tableau Engineer' is kept).
    """
    t = title.lower()
    if not any(kw in t for kw in KEYWORDS):
        return False
    if NEGATIVES:
        has_neg = any(neg in t for neg in NEGATIVES)
        if has_neg:
            has_override = any(pos in t for pos in POSITIVE_OVERRIDES)
            if not has_override:
                return False
    return True


# ============================================================
# PARSERS FOR EACH JOB BOARD
# ============================================================

def check_djinni(source_key="Djinni"):
    """Djinni.co — Ukrainian tech job board."""
    source = SOURCES.get(source_key, {})
    if not source.get("enabled", True):
        return []
    source_url = source.get("url", "https://djinni.co/jobs/keyword-ui_ux/")

    log(f"Checking Djinni ({source_key})...")
    html = fetch_html(source_url)
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    for m in re.finditer(r'<a[^>]*href="(/jobs/(\d+)-[^"]*?)"[^>]*>', html):
        path = m.group(1)
        job_url = f"https://djinni.co{path}"
        if job_url in existing:
            continue

        start = m.end()
        chunk = html[start:start + 500]
        title_m = re.search(r'>([^<]{10,})<', chunk)
        if title_m:
            title = title_m.group(1).strip()
            if is_relevant(title):
                results.append({"title": title, "url": job_url, "section": source_key})

    log(f"  Found {len(results)} new on Djinni ({source_key})")
    return results


def check_dou(source_key="DOU"):
    """DOU.ua — Ukrainian developer community job board."""
    source = SOURCES.get(source_key, {})
    if not source.get("enabled", True):
        return []
    source_url = source.get("url", "https://jobs.dou.ua/vacancies/?search=UI/UX+Designer")

    log(f"Checking DOU ({source_key})...")
    html = fetch_html(source_url)
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    def _clean_dou_title(t):
        t = t.strip()
        t = re.sub(r'&amp;', '&', t)
        t = re.sub(r'&lt;', '<', t)
        t = re.sub(r'&gt;', '>', t)
        t = re.sub(r'&quot;', '"', t)
        t = re.sub(r'&#039;', "'", t)
        return t

    # Pattern: <a href="/companies/SLUG/vacancies/ID/">TITLE</a>
    for m in re.finditer(
        r'<a[^>]*href="(https://jobs\.dou\.ua/companies/[^/]+/vacancies/\d+/)[^"]*"[^>]*>\s*([^<]+)',
        html
    ):
        url = m.group(1)
        title = _clean_dou_title(m.group(2))
        if url in existing or not is_relevant(title):
            continue
        results.append({"title": title, "url": url, "section": source_key})

    # Also try relative URLs
    for m in re.finditer(
        r'href="(/companies/([^/]+)/vacancies/(\d+)/)[^"]*"[^>]*>\s*([^<]{5,})',
        html
    ):
        url = f"https://jobs.dou.ua{m.group(1)}"
        title = _clean_dou_title(m.group(4))
        if url in existing or not is_relevant(title):
            continue
        if not any(r["url"] == url for r in results):
            results.append({"title": title, "url": url, "section": source_key})

    log(f"  Found {len(results)} new on DOU ({source_key})")
    return results


def check_workua(source_key="Work.ua"):
    """Work.ua — Ukrainian job board."""
    source = SOURCES.get(source_key, {})
    if not source.get("enabled", True):
        return []
    source_url = source.get("url", "https://www.work.ua/en/jobs-ui+ux+designer/")

    log(f"Checking Work.ua ({source_key})...")
    html = fetch_html(source_url)
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    def _clean_workua_title(t):
        t = t.strip()
        t = re.sub(r'&amp;', '&', t)
        t = re.sub(r'&lt;', '<', t)
        t = re.sub(r'&gt;', '>', t)
        t = re.sub(r'&quot;', '"', t)
        t = re.sub(r'&#039;', "'", t)
        return t

    # Pattern: <a href="/en/jobs/ID/" ...>TITLE</a>
    for m in re.finditer(r'<a[^>]*href="(/en/jobs/(\d+)/)"[^>]*>\s*([^<]{10,})', html):
        path = m.group(1)
        job_url = f"https://www.work.ua{path}"
        title = _clean_workua_title(m.group(3))
        if job_url in existing or not is_relevant(title):
            continue
        results.append({"title": title, "url": job_url, "section": source_key})

    log(f"  Found {len(results)} new on Work.ua ({source_key})")
    return results


def check_linkedin():
    """LinkedIn — public job search (no auth needed for basic listing)."""
    log("Checking LinkedIn...")
    html = fetch_html(
        "https://www.linkedin.com/jobs/search/?keywords=Senior+UI+UX+Designer&location=Ukraine"
    )
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    # Pattern: href="https://XX.linkedin.com/jobs/view/SLUG-ID"
    for m in re.finditer(
        r'href="(https://[a-z]+\.linkedin\.com/jobs/view/([^"?]+))"',
        html
    ):
        url = m.group(1)
        slug = m.group(2)
        if url in existing:
            continue

        # Convert slug to title: "senior-ux-designer-at-company-12345" -> "Senior UX Designer at Company"
        title_parts = slug.rsplit('-', 1)[0]  # remove trailing ID
        title = title_parts.replace('-', ' ').title()
        if is_relevant(title):
            results.append({"title": title, "url": url, "section": "LinkedIn"})

    log(f"  Found {len(results)} new on LinkedIn")
    return results


def check_weworkremotely():
    """We Work Remotely — remote design jobs."""
    log("Checking WeWorkRemotely...")
    html = fetch_html("https://weworkremotely.com/categories/remote-design-jobs")
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    for m in re.finditer(
        r'<a[^>]*href="(/remote-jobs/[^"]+)"[^>]*>',
        html
    ):
        path = m.group(1)
        url = f"https://weworkremotely.com{path}"
        if url in existing:
            continue

        # Get title from nearby text
        start = m.end()
        chunk = html[start:start + 300]
        title_m = re.search(r'>([^<]{8,})<', chunk)
        if title_m:
            title = title_m.group(1).strip()
            if is_relevant(title):
                results.append({"title": title, "url": url, "section": "WeWorkRemotely"})

    results = results[:10]
    log(f"  Found {len(results)} new on WeWorkRemotely")
    return results


def check_uiuxjobsboard():
    """uiuxjobsboard.com — specialized UX/UI job board."""
    log("Checking UIUXJobsBoard...")
    html = fetch_html("https://uiuxjobsboard.com/design-jobs/remote")
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    for m in re.finditer(
        r'href="(/job/(\d+)-([^"]+))"',
        html
    ):
        path = m.group(1)
        slug = m.group(3)
        url = f"https://uiuxjobsboard.com{path}"
        if url in existing:
            continue

        # Derive title from URL slug: "remote-anywhere-senior-product-designer" -> "Senior Product Designer"
        parts = slug.replace('remote-', '').replace('anywhere-', '')
        # Remove country prefixes
        for prefix in ['united-states-', 'europe-', 'ireland-', 'uk-', 'canada-', 'germany-']:
            parts = parts.replace(prefix, '')
        title = parts.replace('-', ' ').title()

        if is_relevant(title):
            results.append({"title": title, "url": url, "section": "UIUXJobsBoard"})

    # Limit to 15 per source to avoid flooding
    results = results[:15]
    log(f"  Found {len(results)} new on UIUXJobsBoard")
    return results


def check_builtin():
    """Built In — remote design jobs."""
    log("Checking BuiltIn...")
    html = fetch_html("https://builtin.com/jobs/remote/design-ux/search/senior-ux-designer")
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    for m in re.finditer(r'href="(/job/[^"]+)"', html):
        path = m.group(1)
        url = f"https://builtin.com{path}"
        if url in existing:
            continue

        start = m.end()
        chunk = html[start:start + 300]
        title_m = re.search(r'>([^<]{8,})<', chunk)
        if title_m:
            title = title_m.group(1).strip()
            if is_relevant(title):
                results.append({"title": title, "url": url, "section": "BuiltIn"})

    log(f"  Found {len(results)} new on BuiltIn")
    return results


def check_remoterocketship():
    """Remote Rocketship — remote jobs aggregator."""
    log("Checking RemoteRocketship...")
    html = fetch_html("https://www.remoterocketship.com/country/ukraine/jobs/ui-ux-designer/")
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    for m in re.finditer(
        r'href="(/company/[^/]+/jobs/[^"]+)"',
        html
    ):
        path = m.group(1)
        url = f"https://www.remoterocketship.com{path}"
        if url in existing:
            continue

        start = m.end()
        chunk = html[start:start + 300]
        title_m = re.search(r'>([^<]{8,})<', chunk)
        if title_m:
            title = title_m.group(1).strip()
            if is_relevant(title):
                results.append({"title": title, "url": url, "section": "RemoteRocketship"})

    results = results[:10]
    log(f"  Found {len(results)} new on RemoteRocketship")
    return results


def check_glassdoor():
    """Glassdoor — job search."""
    log("Checking Glassdoor...")
    html = fetch_html(
        "https://www.glassdoor.com/Job/ukraine-ux-ui-designer-jobs-SRCH_IL.0,7_IN244_KO8,22.htm"
    )
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    for m in re.finditer(r'href="(/job-listing/[^"]+)"', html):
        path = m.group(1)
        url = f"https://www.glassdoor.com{path}"
        if url in existing:
            continue

        start = m.end()
        chunk = html[start:start + 300]
        title_m = re.search(r'>([^<]{8,})<', chunk)
        if title_m:
            title = title_m.group(1).strip()
            if is_relevant(title):
                results.append({"title": title, "url": url, "section": "Glassdoor"})

    log(f"  Found {len(results)} new on Glassdoor")
    return results


def check_nofluffjobs(source_key):
    """NoFluffJobs — European/Polish tech job board."""
    source = SOURCES.get(source_key, {})
    if not source.get("enabled", True):
        return []
    source_url = source.get("url", "")
    if not source_url:
        return []

    log(f"Checking NoFluffJobs ({source_key})...")
    html = fetch_html(source_url)
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    link_pattern = source.get("link_pattern", r'/pl/job/[a-z0-9-]+')
    for m in re.finditer(link_pattern, html):
        path = m.group(0)
        url = f"https://nofluffjobs.com{path}"
        if url in existing or any(r["url"] == url for r in results):
            continue

        # Derive title from URL slug: "/pl/job/bi-developer-company-city-abc123"
        slug = path.split("/")[-1]
        # Remove trailing hash-id (last segment after last hyphen if short/alphanumeric)
        slug_parts = slug.rsplit("-", 1)
        if len(slug_parts) == 2 and len(slug_parts[1]) <= 7 and slug_parts[1].isalnum():
            slug = slug_parts[0]
        title = slug.replace("-", " ").title()

        if is_relevant(title):
            results.append({"title": title, "url": url, "section": source_key})

    results = results[:15]
    log(f"  Found {len(results)} new on NoFluffJobs ({source_key})")
    return results


def check_justjoin(source_key):
    """JustJoin.it — Polish/European tech job board."""
    source = SOURCES.get(source_key, {})
    if not source.get("enabled", True):
        return []
    source_url = source.get("url", "")
    if not source_url:
        return []

    log(f"Checking JustJoin ({source_key})...")
    html = fetch_html(source_url)
    if not html:
        return []

    existing = get_existing_urls()
    results = []

    link_pattern = source.get("link_pattern", r'/offers/[a-z0-9-]+')
    for m in re.finditer(link_pattern, html):
        path = m.group(0)
        url = f"https://justjoin.it{path}"
        if url in existing:
            continue

        # Grab title from nearby HTML
        start = m.end()
        chunk = html[start:start + 400]
        title_m = re.search(r'>([^<]{8,80})<', chunk)
        if title_m:
            title = title_m.group(1).strip()
            # Clean up HTML entities
            title = re.sub(r'&amp;', '&', title)
            title = re.sub(r'&lt;', '<', title)
            title = re.sub(r'&gt;', '>', title)
            if is_relevant(title):
                if not any(r["url"] == url for r in results):
                    results.append({"title": title, "url": url, "section": source_key})

    results = results[:15]
    log(f"  Found {len(results)} new on JustJoin ({source_key})")
    return results


# ============================================================
# ANALYSIS & MD FILE MANAGEMENT
# ============================================================

def add_vacancy_to_md(section_name, title, url):
    """Add a new vacancy line to the appropriate section in vacancies.md."""
    with open(MD_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Deduplication guard: skip if URL already exists anywhere in the file
    if url in content:
        log(f"    Skipping duplicate URL: {url}")
        return

    # Title-based deduplication: skip if a vacancy with the same normalized title already exists
    norm_new = normalize_title(title)
    for m in re.finditer(r'^\- \[(.+?)\]', content, re.MULTILINE):
        if normalize_title(m.group(1)) == norm_new:
            log(f"    Skipping near-duplicate title: {title}")
            return

    lines = content.split("\n")
    lines = [l + "\n" for l in lines]
    if lines:
        lines[-1] = lines[-1].rstrip("\n") + ("\n" if content.endswith("\n") else "")

    today = datetime.now().strftime("%d.%m")
    new_line = f"- [{title}]({url}) *({today})*\n"

    # Find the section
    in_section = False
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {section_name}":
            in_section = True
            continue
        if in_section:
            if line.startswith("## ") or line.startswith("---"):
                insert_idx = i
                break
            if line.startswith("- ["):
                insert_idx = i + 1

    if insert_idx:
        lines.insert(insert_idx, new_line)
    else:
        # Section doesn't exist — create it before "---" separator or at end
        separator_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "---" and i > 5:
                separator_idx = i
                break

        new_section = f"\n## {section_name}\n\n{new_line}\n"
        if separator_idx:
            lines.insert(separator_idx, new_section)
        else:
            lines.append(new_section)

    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    update_date()


def update_date():
    with open(MD_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(r"Оновлено: \d{4}-\d{2}-\d{2}", f"Оновлено: {today}", content)
    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def analyze_vacancy(title, url):
    """Analyze vacancy with Groq API."""
    try:
        from analyze_new import fetch_page, analyze_with_groq, GROQ_KEY
        if not GROQ_KEY:
            return None
        profile_path = os.path.join(BASE_DIR, "profile.md")
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = f.read()
        page_text = fetch_page(url)
        return analyze_with_groq(title, url, page_text, profile)
    except Exception as e:
        log(f"  Analysis error: {e}")
        return None


def main():
    log("=" * 50)
    log("Starting vacancy check across all sources")
    log("=" * 50)

    # Run all checkers — dispatch every SOURCES entry by URL domain
    all_new = []
    dispatched = set()

    for source_key in SOURCES:
        if source_key in dispatched:
            continue
        src_url = SOURCES[source_key].get("url", "").lower()
        try:
            if "djinni" in src_url:
                results = check_djinni(source_key)
                all_new.extend(results)
                dispatched.add(source_key)
                time.sleep(2)
            elif "jobs.dou.ua" in src_url:
                results = check_dou(source_key)
                all_new.extend(results)
                dispatched.add(source_key)
                time.sleep(2)
            elif "work.ua" in src_url:
                results = check_workua(source_key)
                all_new.extend(results)
                dispatched.add(source_key)
                time.sleep(2)
            elif "nofluffjobs" in src_url or source_key.lower().startswith("nofluffjobs"):
                results = check_nofluffjobs(source_key)
                all_new.extend(results)
                dispatched.add(source_key)
                time.sleep(2)
            elif "justjoin" in src_url or source_key.lower().startswith("justjoin"):
                results = check_justjoin(source_key)
                all_new.extend(results)
                dispatched.add(source_key)
                time.sleep(2)
        except Exception as e:
            log(f"  ERROR in checker for {source_key}: {e}")

    # Deduplicate by URL and normalized title (within this run AND against existing MD file)
    existing_norm_titles = get_existing_normalized_titles()
    seen_urls = set()
    seen_titles = set()
    unique = []
    for v in all_new:
        norm_key = normalize_title(v["title"])
        if v["url"] not in seen_urls and norm_key not in seen_titles and norm_key not in existing_norm_titles:
            seen_urls.add(v["url"])
            seen_titles.add(norm_key)
            unique.append(v)
        elif norm_key in existing_norm_titles:
            log(f"  Skipping (title already in MD): {v['title']}")
    all_new = unique

    if not all_new:
        log(f"No new vacancies found.")
        return

    # Limit per run to avoid rate limits (Groq free: ~30 RPM)
    MAX_PER_RUN = 25
    if len(all_new) > MAX_PER_RUN:
        log(f"\nTotal: {len(all_new)} new, processing first {MAX_PER_RUN} (rest next run).\n")
        all_new = all_new[:MAX_PER_RUN]
    else:
        log(f"\nTotal: {len(all_new)} new vacancies to process.\n")

    # Load analyses
    analyses = {}
    if os.path.exists(ANALYSES_FILE):
        with open(ANALYSES_FILE, "r", encoding="utf-8") as f:
            analyses = json.load(f)

    added = 0
    for v in all_new:
        log(f"  [{v['section']}] {v['title']}")

        # Analyze before adding
        result = analyze_vacancy(v["title"], v["url"])
        if result:
            analyses[v["url"]] = result
            score = result.get('score', '?')
            log(f"    Score: {score}/10")

            # Skip very low scores (1-2) — don't clutter the list
            if isinstance(score, int) and score <= 2:
                log(f"    Skipping (score too low)")
                continue

        # Add to MD file
        add_vacancy_to_md(v["section"], v["title"], v["url"])
        added += 1

        # Rate limit for Groq free tier (30 RPM)
        time.sleep(6)

    # Save analyses
    with open(ANALYSES_FILE, "w", encoding="utf-8") as f:
        json.dump(analyses, f, ensure_ascii=False, indent=2)

    log(f"\nDone. Added {added} vacancies (skipped {len(all_new) - added} low-score).")
    log("=" * 50)


if __name__ == "__main__":
    main()
