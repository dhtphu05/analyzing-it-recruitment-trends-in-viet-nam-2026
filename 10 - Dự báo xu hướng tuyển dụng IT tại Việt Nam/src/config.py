from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

EXPECTED_COLUMNS = [
    "job_id",
    "source",
    "crawl_date",
    "job_title",
    "job_title_group",
    "company_name",
    "location",
    "primary_city",
    "location_bucket",
    "company_type",
    "level",
    "experience_years",
    "experience_band",
    "salary_min",
    "salary_max",
    "salary_avg",
    "salary_currency",
    "has_salary",
]
