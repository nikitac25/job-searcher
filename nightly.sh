#!/bin/bash
# Nightly autonomous improvement cycle — runs via cron at 3:03 AM
# Claude Code analyzes the project, picks one improvement, implements it, and logs to changelog.

export HOME=/home/den
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
# Load secrets from .env (not tracked by git)
[ -f /home/den/job-search/.env ] && export $(grep -v '^#' /home/den/job-search/.env | xargs)

cd /home/den/job-search || exit 1

PROMPT='You are running an autonomous nightly maintenance and improvement cycle for the job-search project at /home/den/job-search/. The user has given you FULL autonomy to make decisions and implement changes without asking.

Follow these steps IN ORDER:

## Step 1: Health Check
- Read the current state of all project files (app.py, check_new.py, analyze_new.py, index.html, changelog.html, vacancies.md, analyses.json, changelog.md)
- Try running the Flask app briefly to check for import/syntax errors: `cd /home/den/job-search && python3 -c "import app; print('\''OK'\'')"`
- Run check_new.py to verify it works: `cd /home/den/job-search && timeout 120 python3 check_new.py 2>&1 | tail -30`
- If there are errors, fix them. After fixing, verify the fix works.

## Step 2: Analyze & Pick One Improvement
Think about what would make this project better. Consider areas like:
- UI/UX improvements to index.html or changelog.html
- Better vacancy parsing/deduplication in check_new.py
- New job board sources
- Better scoring/filtering in analyze_new.py
- Performance, code quality, error handling
- New features (e.g., statistics page, trends, charts)
- Better data visualization
- Mobile responsiveness improvements
- Remove duplicate vacancies from vacancies.md
- Improve the changelog page design

Pick ONE concrete improvement that adds the most value. Prefer user-facing improvements. Do NOT repeat improvements that are already logged in changelog.md.

## Step 3: Implement the Improvement
Make the code changes needed. Keep changes focused and clean.

## Step 4: Verify
- Run `cd /home/den/job-search && python3 -c "import app; print('\''OK'\'')"` to verify no import errors
- Check that all modified files have valid syntax
- If you changed HTML/JS, verify the structure is valid

## Step 5: Log to Changelog
Append an entry to /home/den/job-search/changelog.md in this format:

---

## YYYY-MM-DD HH:MM

### [Short title of what was done]

**Problem/Opportunity:** [What you identified]

**Solution:** [What you implemented]

**Files changed:** [List of files]

**Verification:** [How you verified it works]

---

Be specific and descriptive in the changelog. Write in Ukrainian.

IMPORTANT: Do NOT ask the user anything. Make all decisions yourself. You have full autonomy.'

claude --dangerously-skip-permissions -p "$PROMPT" \
  --output-format text \
  >> /home/den/job-search/nightly.log 2>&1
