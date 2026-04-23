#!/usr/bin/env python3
"""Vacancy board web app — carousel UI with analysis scores."""

import re
import os
import sys
import json
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from config import WEB_PORT, WEB_HOST
except ImportError:
    WEB_PORT = 8080
    WEB_HOST = "0.0.0.0"
MD_FILE = os.path.join(BASE_DIR, "vacancies.md")
ANALYSES_FILE = os.path.join(BASE_DIR, "analyses.json")
CHANGELOG_FILE = os.path.join(BASE_DIR, "changelog.md")


def load_analyses():
    if os.path.exists(ANALYSES_FILE):
        with open(ANALYSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_analyses(data):
    with open(ANALYSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Section names to exclude entirely from the UI
_SKIP_SECTIONS = {"Search URLs", "Пошукові запити для самостійного моніторингу"}
# Item titles that are search-page placeholders, not real vacancies
_SKIP_TITLES = {"All vacancies"}


def parse_vacancies():
    if not os.path.exists(MD_FILE):
        return []
    with open(MD_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    analyses = load_analyses()
    sections = []
    current_section = None
    lines = content.split("\n")

    for line in lines:
        h2 = re.match(r"^## (.+)", line)
        if h2:
            section_name = h2.group(1).strip()
            if section_name in _SKIP_SECTIONS:
                current_section = None
                continue
            current_section = {"name": section_name, "items": []}
            sections.append(current_section)
            continue

        if current_section is None:
            continue

        m = re.match(r"^- \[(.+?)\]\((.+?)\)\s*(\*\((.+?)\)\*)?", line)
        if m:
            title = m.group(1).strip()
            if title in _SKIP_TITLES:
                continue
            url = m.group(2)
            analysis = analyses.get(url, {})
            current_section["items"].append({
                "title": title,
                "url": url,
                "date": m.group(4) or "",
                "score": analysis.get("score", None),
                "summary": analysis.get("summary", ""),
                "type": analysis.get("type", ""),
                "salary": analysis.get("salary", ""),
                "remote": analysis.get("remote", ""),
                "published": analysis.get("published", ""),
                "status": analysis.get("status", ""),
            })

    # Remove empty sections
    sections = [s for s in sections if s["items"]]
    return sections


def remove_vacancy(url):
    with open(MD_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = [l for l in lines if url not in l]

    if len(new_lines) < len(lines):
        with open(MD_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        # Also remove from analyses
        analyses = load_analyses()
        if url in analyses:
            del analyses[url]
            save_analyses(analyses)
        return True
    return False


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/changelog")
def changelog_page():
    return send_file("changelog.html")


@app.route("/api/config")
def api_config():
    try:
        from config import PAGE_TITLE
    except ImportError:
        PAGE_TITLE = "Вакансії"
    return jsonify({"page_title": PAGE_TITLE})


@app.route("/api/changelog")
def api_changelog():
    if os.path.exists(CHANGELOG_FILE):
        with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
            return jsonify({"content": f.read()})
    return jsonify({"content": ""})


@app.route("/api/vacancies")
def api_vacancies():
    return jsonify(parse_vacancies())


@app.route("/api/status")
def api_status():
    """Return info about the last vacancy check run (from check.log)."""
    log_file = os.path.join(BASE_DIR, "check.log")
    if not os.path.exists(log_file):
        return jsonify({"last_check": None, "added": None, "sources": {}, "errors": []})

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    last_check = None
    added = None
    sources = {}   # {source_key: count_new}
    errors = []    # list of short error descriptions

    # Scan backwards to find the most recent run info
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        ts = re.match(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
        if ts and last_check is None:
            last_check = ts.group(1)
        done = re.search(r'Done\. Added (\d+) vacanc', line)
        if done and added is None:
            added = int(done.group(1))
        # Newer format: "Found N new on TYPE (SOURCE_KEY)"
        src_new = re.search(r'Found (\d+) new on \S+ \(([^)]+)\)', line)
        if src_new:
            sources[src_new.group(2)] = int(src_new.group(1))
        # Older format: "Found N new on SOURCE_NAME"
        elif re.search(r'Found (\d+) new on (\S+)$', line):
            m = re.search(r'Found (\d+) new on (\S+)$', line)
            if m and m.group(2) not in sources:
                sources[m.group(2)] = int(m.group(1))
        # Fetch errors: "Fetch error for URL: message"
        err = re.search(r'Fetch error for (https?://\S+):\s*(.+)$', line)
        if err:
            short_err = err.group(2)[:60]
            if short_err not in errors:
                errors.append(short_err)
        if 'Starting vacancy check' in line and last_check is not None:
            break

    return jsonify({"last_check": last_check, "added": added,
                    "sources": sources, "errors": errors})


@app.route("/api/vacancies", methods=["DELETE"])
def api_delete():
    url = request.json.get("url", "")
    if remove_vacancy(url):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "not found"}), 404


_check_running = False


@app.route("/api/check", methods=["POST"])
def api_check():
    """Trigger check_new.py in a background thread. Idempotent — ignores if already running."""
    global _check_running
    if _check_running:
        return jsonify({"ok": True, "msg": "already running"})

    import subprocess
    import threading

    def run():
        global _check_running
        _check_running = True
        try:
            subprocess.run(
                [sys.executable, os.path.join(BASE_DIR, "check_new.py")],
                capture_output=True,
                timeout=300,
            )
        except Exception:
            pass
        finally:
            _check_running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"ok": True, "msg": "started"})


@app.route("/api/check/status", methods=["GET"])
def api_check_status():
    """Return whether check_new.py is currently running."""
    return jsonify({"running": _check_running})


if __name__ == "__main__":
    app.run(host=WEB_HOST, port=WEB_PORT)
