"""
=== JOB SEARCH CONFIGURATION ===

Edit this file to customize the job search for YOUR profile.
Everything else works automatically.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. YOUR PROFILE — fill in your details
# ============================================================

PROFILE = {
    "name": "Nikita",
    "title": "BI Developer / Looker Developer",
    "experience_years": 4,               # years of experience
    "salary_min": 4000,                  # minimum salary USD/month
    "salary_max": 8000,                  # desired salary USD/month
    "remote_only": True,                 # only remote positions
    "language": "en",                    # "uk" = Ukrainian, "en" = English
}

# ============================================================
# 2. WHAT YOU'RE LOOKING FOR
# ============================================================

TARGET = [
    "BI Developer",
    "Looker Developer",
    "BI Engineer",
    "Business Intelligence Developer",
    "LookML Developer",
    "BI Analyst",
]

NOT_INTERESTED = [
    "Junior/intern positions",
    "Gambling, adult content",
    "Office-only positions",
    "Pure data engineering without BI focus",
    "Power BI only (no Looker)",
    "Tableau only (no Looker)",
]

# ============================================================
# 3. FIT CRITERIA — customize scoring
# ============================================================

FIT_CRITERIA = """
| Signal | Good fit | Poor fit |
|---|---|---|
| Tools | Looker, LookML | Power BI only, Tableau only |
| Data warehouse | BigQuery, Snowflake | No cloud DWH |
| Cloud | GCP, Snowflake ecosystem | AWS/Azure only with no relevant DWH |
| Role type | BI Developer, BI Engineer, Looker Developer, BI Analyst | Pure data engineer, pure analyst |
| Remote | Fully remote | Office-required |
| Employment | Full-time or part-time | On-site only |
| Salary | $4000-8000+/month or 100+ PLN/h | Below range |
| Company | Product or consulting | Pure outsource body shop |
"""

# ============================================================
# 4. YOUR KEY EXPERIENCE — for AI matching
# ============================================================

KEY_EXPERIENCE = [
    "4+ years in BI development with Looker and LookML",
    "Experience with GCP ecosystem: BigQuery, GCS, Dataform",
    "Experience with Snowflake as a data warehouse",
    "Designed and maintained semantic layers and dimensional models",
    "Built dashboards and self-service analytics for business stakeholders",
    "Proficient in BigQuery and Snowflake SQL including analytical functions and performance tuning",
    "Experience with role-based access control and user attributes in Looker",
    "Git version control for Looker projects",
    # Add your specific achievements here
]

# ============================================================
# 5. SEARCH KEYWORDS — what to search for on job boards
# ============================================================

SEARCH_KEYWORDS = [
    "looker developer",
    "BI developer",
    "BI engineer",
    "business intelligence developer",
    "lookml developer",
    "looker snowflake",
    "looker bigquery",
]

# Keywords that vacancy titles must contain (at least one)
TITLE_KEYWORDS = [
    "looker",
    "lookml",
    "bi developer",
    "bi engineer",
    "bi analyst",
    "business intelligence",
]

# Vacancy titles containing ANY of these keywords are skipped WITHOUT calling
# the Groq API — unless the title also contains a POSITIVE_OVERRIDE keyword.
# This saves API quota and avoids rate-limit waits on clearly irrelevant jobs.
NEGATIVE_TITLE_KEYWORDS = [
    "power bi",
    "powerbi",
    "ms sql",
    "microsoft sql",
    "microsoft fabric",
    "azure synapse",
    "qlik",
    "ssrs",
    "ssis",
    "ssas",
    "tableau",
    "microstrategy",
    "cognos",
    "sap bo",
    "sap bw",
    "spotfire",
]

# If the title contains ANY of these, the negative-keyword check is bypassed
# (e.g. a job requiring both Looker AND Tableau is still worth checking).
POSITIVE_OVERRIDE_KEYWORDS = [
    "looker",
    "lookml",
    "bigquery",
    "snowflake",
    "dbt",
]

# ============================================================
# 6. JOB BOARD URLS — customize search queries
# ============================================================

SOURCES = {
    # --- Ukrainian job boards ---
    "Djinni_looker": {
        "enabled": True,
        "url": "https://djinni.co/jobs/?all_keywords=looker&search_type=basic-search",
        "link_pattern": r'/jobs/(\d+)-',
    },
    "Djinni_bi": {
        "enabled": True,
        "url": "https://djinni.co/jobs/?all_keywords=BI&search_type=basic-search",
        "link_pattern": r'/jobs/(\d+)-',
    },
    "DOU.ua": {
        "enabled": True,
        "url": "https://jobs.dou.ua/vacancies/?search=BI+Developer",
        "link_pattern": r'/companies/[^/]+/vacancies/\d+/',
    },
    "Work.ua": {
        "enabled": True,
        "url": "https://www.work.ua/en/jobs-bi+developer/",
        "link_pattern": r'/en/jobs/\d+/',
    },

    # --- Polish / European job boards ---
    "NoFluffJobs_looker": {
        "enabled": True,
        "url": "https://nofluffjobs.com/pl/jobs/looker",
        "link_pattern": r'/pl/job/[a-z0-9-]+',
    },
    "NoFluffJobs_bi": {
        "enabled": True,
        "url": "https://nofluffjobs.com/pl/jobs/bi-developer",
        "link_pattern": r'/pl/job/[a-z0-9-]+',
    },
    "JustJoin_bi": {
        "enabled": True,
        "url": "https://justjoin.it/job-offers/all-locations?keyword=BI+Developer&orderBy=DESC&sortBy=published",
        "link_pattern": r'/offers/[a-z0-9-]+',
    },
    "JustJoin_looker": {
        "enabled": True,
        "url": "https://justjoin.it/job-offers/all-locations?keyword=Looker+Developer&orderBy=DESC&sortBy=published",
        "link_pattern": r'/offers/[a-z0-9-]+',
    },
}

# ============================================================
# 7. GROQ API KEY — loaded from .env file
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ============================================================
# 8. WEB SERVER
# ============================================================

WEB_PORT = 8080
WEB_HOST = "0.0.0.0"

# ============================================================
# 9. PAGE TITLE
# ============================================================

PAGE_TITLE = "BI / Looker Job Search"
