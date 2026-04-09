#!/bin/bash
# Nightly autonomous improvement cycle — runs via cron at 3:03 AM
# Claude Code analyzes the project, picks one improvement, implements it, and logs to changelog.

export HOME=/home/kvm1
export PATH="/home/kvm1/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
# Load secrets from .env (not tracked by git)
[ -f /home/kvm1/job-searcher/.env ] && export $(grep -v '^#' /home/kvm1/job-searcher/.env | xargs)

cd /home/kvm1/job-searcher || exit 1

PROMPT='You are running an autonomous nightly maintenance and improvement cycle for the job-searcher project at /home/kvm1/job-searcher/. The user has given you FULL autonomy to make decisions and implement changes without asking.

Follow these steps IN ORDER:

## Step 1: Health Check
- Read the current state of all project files (app.py, check_new.py, analyze_new.py, index.html, changelog.html, vacancies.md, analyses.json)
- Try running the Flask app briefly to check for import/syntax errors: `cd /home/kvm1/job-searcher && venv/bin/python3 -c "import app; print('\''OK'\'')"`
- Run check_new.py to verify it works: `cd /home/kvm1/job-searcher && timeout 120 venv/bin/python3 check_new.py 2>&1 | tail -30`
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

Pick ONE concrete improvement that adds the most value. Prefer user-facing improvements. Do NOT repeat improvements that are already logged in changelog.html.

## Step 3: Implement the Improvement
Make the code changes needed. Keep changes focused and clean.

## Step 4: Verify
- Run `cd /home/kvm1/job-searcher && venv/bin/python3 -c "import app; print('\''OK'\'')"` to verify no import errors
- Check that all modified files have valid syntax
- If you changed HTML/JS, verify the structure is valid

## Step 5: Log to Changelog
Append an entry to /home/kvm1/job-searcher/changelog.html in this format:

<article>
  <h2>YYYY-MM-DD HH:MM</h2>
  <h3>[Short title of what was done]</h3>
  <p><strong>Problem/Opportunity:</strong> [What you identified]</p>
  <p><strong>Solution:</strong> [What you implemented]</p>
  <p><strong>Files changed:</strong> [List of files]</p>
  <p><strong>Verification:</strong> [How you verified it works]</p>
</article>

Be specific and descriptive in the changelog. Write in Ukrainian.

## Step 6: Commit & Push to dev
After implementing and verifying:
- `cd /home/kvm1/job-searcher && git add -A && git commit -m "[brief description of what was done]"`
- `git push origin dev`

IMPORTANT: Do NOT ask the user anything. Make all decisions yourself. You have full autonomy.'

claude --dangerously-skip-permissions -p "$PROMPT" \
  --output-format text \
  >> /home/kvm1/job-searcher/nightly.log 2>&1
