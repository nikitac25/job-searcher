"""
=== JOB SEARCH CONFIGURATION ===

Edit this file to customize the job search for YOUR profile.
Everything else works automatically.
"""

# ============================================================
# 1. YOUR PROFILE — fill in your details
# ============================================================

PROFILE = {
    "name": "Your Name",
    "title": "Your Target Role",        # e.g. "Senior Python Developer", "Product Designer", "Data Analyst"
    "experience_years": 5,               # years of experience
    "salary_min": 3000,                  # minimum salary USD/month
    "salary_max": 6000,                  # desired salary USD/month
    "remote_only": True,                 # True = only remote, False = office OK too
    "language": "uk",                    # "uk" = Ukrainian, "en" = English
}

# ============================================================
# 2. WHAT YOU'RE LOOKING FOR
# ============================================================

TARGET = [
    "Senior Python Developer, remote full-time",
    "Stable product company, not outsource",
    "Good engineering culture",
]

NOT_INTERESTED = [
    "Outsource/outstaffing agencies",
    "Gambling, adult content",
    "Office-only positions",
    "Junior/intern positions",
]

# ============================================================
# 3. FIT CRITERIA — customize scoring
# ============================================================

FIT_CRITERIA = """
| Signal | Good fit | Poor fit |
|---|---|---|
| Role type | Senior/Lead | Junior, mid-level |
| Company type | Product company | Outsource/agency |
| Remote | Fully remote | Office-required |
| Salary | $3000-6000+/month | Below range |
"""

# ============================================================
# 4. YOUR KEY EXPERIENCE — for AI matching
# ============================================================

KEY_EXPERIENCE = [
    "5 years in Python/Django development",
    "Built microservices architecture for fintech startup",
    "Team lead experience, mentoring 3 developers",
    # Add your key achievements here
]

# ============================================================
# 5. SEARCH KEYWORDS — what to search for on job boards
# ============================================================

SEARCH_KEYWORDS = [
    "python developer",
    "backend developer",
    "django developer",
]

# Keywords that vacancy titles must contain (at least one)
TITLE_KEYWORDS = ["python", "backend", "django", "developer", "engineer", "розробник"]

# ============================================================
# 6. JOB BOARD URLS — customize search queries
# ============================================================

SOURCES = {
    "Djinni": {
        "enabled": True,
        "url": "https://djinni.co/jobs/keyword-python/",
        "link_pattern": r'/jobs/(\d+)-',
    },
    "DOU": {
        "enabled": True,
        "url": "https://jobs.dou.ua/vacancies/?search=Python+Developer",
        "link_pattern": r'/companies/[^/]+/vacancies/\d+/',
    },
    "Work.ua": {
        "enabled": True,
        "url": "https://www.work.ua/en/jobs-python+developer/",
        "link_pattern": r'/en/jobs/\d+/',
    },
}

# ============================================================
# 7. GROQ API KEY (free) — get yours at console.groq.com
# ============================================================

GROQ_API_KEY = ""  # Paste your key here, e.g. "gsk_abc123..."

# ============================================================
# 8. WEB SERVER
# ============================================================

WEB_PORT = 8080
WEB_HOST = "0.0.0.0"

# ============================================================
# 9. PAGE TITLE
# ============================================================

PAGE_TITLE = "Job Search"  # Shown in browser tab and header
