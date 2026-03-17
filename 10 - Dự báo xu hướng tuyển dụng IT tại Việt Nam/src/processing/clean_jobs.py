from __future__ import annotations

import argparse
import hashlib
import logging
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config import EXPECTED_COLUMNS
from src.processing.utils import normalize_text, slugify_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SALARY_EXCHANGE_RATES = {
    "VND": 1.0,
    "USD": 25_000.0,
}

CORE_COLUMNS = [
    "source",
    "crawl_date",
    "job_title",
    "tech_stack",
    "experience_years",
    "location",
    "company_name",
    "company_type",
    "company_industry",
    "remote_option",
    "salary_min",
    "salary_max",
    "currency",
    "posted_date",
    "deadline",
    "job_description",
]

LOCATION_MAP = {
    "ha noi": "Ha Noi",
    "hanoi": "Ha Noi",
    "hn": "Ha Noi",
    "ha noi city": "Ha Noi",
    "thanh pho ha noi": "Ha Noi",
    "tp ha noi": "Ha Noi",
    "ho chi minh": "Ho Chi Minh",
    "hcm": "Ho Chi Minh",
    "hcmc": "Ho Chi Minh",
    "ho chi minh city": "Ho Chi Minh",
    "saigon": "Ho Chi Minh",
    "sai gon": "Ho Chi Minh",
    "thanh pho ho chi minh": "Ho Chi Minh",
    "tp hcm": "Ho Chi Minh",
    "tp ho chi minh": "Ho Chi Minh",
    "da nang": "Da Nang",
    "danang": "Da Nang",
    "tp da nang": "Da Nang",
    "thanh pho da nang": "Da Nang",
    "can tho": "Can Tho",
    "tp can tho": "Can Tho",
    "hai phong": "Hai Phong",
    "haiphong": "Hai Phong",
    "tp hai phong": "Hai Phong",
    "dong nai": "Dong Nai",
    "bien hoa": "Dong Nai",
    "binh duong": "Binh Duong",
    "thu dau mot": "Binh Duong",
    "hung yen": "Hung Yen",
    "lam dong": "Lam Dong",
    "da lat": "Lam Dong",
    "bac ninh": "Bac Ninh",
    "quang ninh": "Quang Ninh",
    "ha long": "Quang Ninh",
    "tay ninh": "Tay Ninh",
    "thanh hoa": "Thanh Hoa",
    "vung tau": "Ba Ria Vung Tau",
    "ba ria vung tau": "Ba Ria Vung Tau",
    "nha trang": "Khanh Hoa",
    "khanh hoa": "Khanh Hoa",
    "viet nam": "Others",
    "vietnam": "Others",
    "noi khac": "Others",
}

HUB_CITIES = {"Ha Noi", "Ho Chi Minh", "Da Nang", "Can Tho", "Hai Phong"}

REMOTE_MAP = {
    "onsite": "onsite",
    "on site": "onsite",
    "on-site": "onsite",
    "office": "onsite",
    "hybrid": "hybrid",
    "remote": "remote",
    "work from home": "remote",
    "wfh": "remote",
}

LEVEL_MAP = {
    "intern": "Intern/Fresher",
    "thuc tap": "Intern/Fresher",
    "fresher": "Intern/Fresher",
    "entry level": "Intern/Fresher",
    "entrylevel": "Intern/Fresher",
    "junior": "Junior",
    "middle": "Middle",
    "mid": "Middle",
    "senior": "Senior",
    "lead": "Lead",
    "principal": "Lead",
    "staff": "Lead",
    "architect": "Lead",
    "expert": "Senior",
    "specialist": "Senior",
    "manager": "Manager",
    "head": "Manager",
    "director": "Director/C-level",
    "cto": "Director/C-level",
    "cio": "Director/C-level",
    "vpoe": "Director/C-level",
    "vp engineering": "Director/C-level",
    "c level": "Director/C-level",
    "c-level": "Director/C-level",
}

JOB_TITLE_GROUP_RULES = [
    ("Full-stack Developer", ["fullstack", "full stack", "full-stack"]),
    ("Back-end Developer", ["backend", "back end", "api developer", "java developer", "python developer", "golang", "go developer", ".net developer", "net developer", "node.js developer", "nodejs developer", "php developer", "ruby developer", "application developer"]),
    ("Front-end Developer", ["frontend", "front end", "fontend", "react developer", "vue developer", "angular developer", "ui developer"]),
    ("Mobile Developer", ["android", "ios", "mobile developer", "flutter", "react native", "swift", "kotlin", "xamarin"]),
    ("Game Developer", ["game developer", "unity", "unreal", "gameplay"]),
    ("Embedded Engineer", ["embedded", "firmware", "hardware", "iot engineer", "automotive software"]),
    ("Product Owner/Product Manager", ["product owner", "product manager", "po ", "pm product"]),
    ("Business Analyst", ["business analyst", "system analyst", "it ba", "business intelligence analyst"]),
    ("Project Leader/Project Manager", ["project manager", "project leader", "delivery manager", "program manager", "scrum master"]),
    ("Tech Lead", ["tech lead", "technical lead", "engineering lead", "team lead", "lead developer", "architect", "architecture lead"]),
    ("IT Manager", ["it manager", "head of engineering", "head of technology", "cto", "cio", "vp engineering", "vpoe"]),
    ("Tester", ["tester", "test engineer", "manual test"]),
    ("QA-QC", ["qa", "qc", "quality assurance", "quality control", "automation test", "automation qa"]),
    ("Data Engineer", ["data engineer", "etl", "big data", "data ware", "spark engineer", "airflow"]),
    ("Data Analyst/Data Scientist/BI", ["data analyst", "data scientist", "machine learning", "ml engineer", "ai engineer", "ai scientist", "ai analyst", "ai developer", "ai automation", "ai workflow", "llm", "genai", "bi analyst", "business intelligence", "nlp engineer", "computer vision"]),
    ("ERP Engineer/ERP Consultant", ["erp", "sap", "odoo", "oracle ebs", "dynamics 365"]),
    ("IT Support/Helpdesk", ["it support", "helpdesk", "service desk", "desktop support", "technical support"]),
    ("DevOps/Cloud/Security", ["devops", "devsecops", "cloud engineer", "platform engineer", "site reliability", "sre", "security engineer", "cyber security", "cybersecurity", "soc analyst", "pentest", "penetration tester", "system administrator", "system admin", "sysadmin", "network engineer", "network administrator", "infrastructure engineer", "application operations"]),
]

RAW_COMPANY_TYPE_MAP = {
    "it product": "Product",
    "product": "Product",
    "software products and web services": "Product",
    "it outsourcing": "Outsource",
    "software development outsourcing": "Outsource",
    "outsource": "Outsource",
    "it service and it consulting": "Service/Consulting",
    "it services and it consulting": "Service/Consulting",
    "service": "Service/Consulting",
    "consulting": "Service/Consulting",
    "non-it": "Non-IT",
    "non it": "Non-IT",
}

NON_IT_KEYWORDS = [
    "bank", "banking", "finance", "fintech", "insurance", "securities", "consumer finance",
    "hospital", "benh vien", "medical", "pharma", "healthcare",
    "logistics", "delivery", "shipping", "warehouse", "giao hang", "van tai",
    "education", "university", "academy", "school",
    "real estate", "property", "retail", "manufacturing", "telecom", "truyen hinh",
]
PRODUCT_KEYWORDS = [
    "product company", "product based", "our product", "company product", "platform", "saas", "app", "studio",
]
SERVICE_KEYWORDS = [
    "consulting", "service", "services", "solution", "solutions", "agency", "system integration",
]
OUTSOURCE_KEYWORDS = [
    "outsource", "outsourcing", "offshore", "gia cong", "software outsourcing",
]
STARTUP_KEYWORDS = [
    "startup", "start-up",
]
KNOWN_PRODUCT_COMPANIES = {
    "momo", "m service", "zalopay", "zalo", "vng", "shopee", "tiki", "grab", "one mount", "onemount", "elsa", "flodesk",
}
KNOWN_SERVICE_COMPANIES = {
    "fpt software", "cmc global", "nashtech", "lg cns", "capgemini", "saigon technology", "elca", "pasona", "devoteam",
    "rikkeisoft", "hpt", "tinh van", "bosch global software", "eurofins gsc it", "dirox",
}
KNOWN_OUTSOURCE_COMPANIES = {
    "kms technology", "nashtech", "saigon technology", "fpt software", "lg cns", "cmc global", "orient software",
}
KNOWN_NON_IT_COMPANIES = {
    "mb bank", "mbbank", "tpbank", "ocb", "vietinbank", "vietbank", "pvcombank", "vpbank", "techcombank", "abbank",
    "mobifone", "novaland", "home credit", "sacombank", "ssi securities",
}

MAJOR_LANGUAGE_HINTS = ["python", "java", "javascript", "typescript", "c#", "php", "go", "kotlin", "swift", "sql"]


def ensure_core_columns(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    for column in CORE_COLUMNS:
        if column not in enriched.columns:
            enriched[column] = np.nan
    return enriched


def normalize_source_name(value: object) -> object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan
    key = slugify_key(text)
    if "itviec" in key:
        return "itviec"
    if "topcv" in key:
        return "topcv"
    if "topdev" in key:
        return "topdev"
    return key or np.nan


def normalize_free_text(value: object) -> object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan
    text = re.sub(r"[\r\n\t]+", " ", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return text or np.nan


def split_locations(value: object) -> list[str]:
    text = normalize_text(value)
    if pd.isna(text):
        return []

    normalized_parts: list[str] = []
    for raw_part in re.split(r"[,&/|]+|\s+-\s+", str(text)):
        sanitized_part = re.sub(r"\([^)]*\)", " ", str(raw_part))
        key = slugify_key(sanitized_part)
        key = re.sub(r"\b(moi|new)\b", " ", key)
        key = re.sub(r"\b(thanh pho|tp)\b", " ", key)
        key = re.sub(r"\s+", " ", key).strip()
        if not key or key == ".":
            continue
        if any(keyword in key for keyword in ["remote", "hybrid", "work depending on project", "work remotely"]):
            cleaned = "Others"
            if cleaned not in normalized_parts:
                normalized_parts.append(cleaned)
            continue
        cleaned = LOCATION_MAP.get(key)
        if cleaned is None and re.fullmatch(r"\d+\s+noi\s+khac", key):
            cleaned = "Others"
        if cleaned is None:
            cleaned = " ".join(token.capitalize() for token in key.split())
        if cleaned not in normalized_parts:
            normalized_parts.append(cleaned)
    return normalized_parts


def normalize_location(value: object) -> object:
    parts = split_locations(value)
    if not parts:
        return np.nan
    return " | ".join(parts)


def get_primary_city(value: object) -> object:
    parts = split_locations(value)
    if not parts:
        return np.nan
    for city in parts:
        if city in HUB_CITIES:
            return city
    return parts[0]


def get_location_bucket(primary_city: object) -> object:
    if pd.isna(primary_city):
        return np.nan
    return primary_city if primary_city in HUB_CITIES else "Others"


def normalize_remote_option(
    value: object,
    job_title: object = np.nan,
    location: object = np.nan,
    job_description: object = np.nan,
) -> object:
    text = normalize_text(value)
    if pd.notna(text):
        key = slugify_key(text)
        normalized = REMOTE_MAP.get(key)
        if normalized is not None:
            return normalized
        if "hybrid" in key:
            return "hybrid"
        if "remote" in key or "wfh" in key:
            return "remote"
        if any(token in key for token in ["office", "onsite", "on site"]):
            return "onsite"

    search_space = " ".join(
        [
            str(normalize_text(job_title) or ""),
            str(normalize_text(job_description) or ""),
        ]
    )
    key = slugify_key(search_space)
    if "hybrid" in key:
        return "hybrid"
    if "remote" in key or "work from home" in key or "wfh" in key:
        return "remote"
    return "unknown"


def parse_salary_number(value: object) -> float | object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan

    candidate = str(text).strip().upper().replace(",", "").replace(" ", "")
    candidate = candidate.replace("VND", "").replace("USD", "")
    candidate = candidate.replace("TRIEU", "M").replace("TRIỆU", "M")
    if not candidate:
        return np.nan

    million_match = re.fullmatch(r"(\d+(?:\.\d+)?)M", candidate)
    if million_match:
        return float(million_match.group(1)) * 1_000_000

    thousand_match = re.fullmatch(r"(\d+(?:\.\d+)?)K", candidate)
    if thousand_match:
        return float(thousand_match.group(1)) * 1_000

    try:
        return float(candidate)
    except ValueError:
        numbers = re.findall(r"\d+(?:\.\d+)?", candidate)
        if not numbers:
            return np.nan
        return float(numbers[0])


def infer_currency(value: object, source: object, salary_min: object, salary_max: object) -> object:
    text = normalize_text(value)
    if pd.notna(text):
        key = str(text).upper().strip()
        if key in SALARY_EXCHANGE_RATES:
            return key

    amounts = [amount for amount in [salary_min, salary_max] if pd.notna(amount)]
    if not amounts:
        return np.nan

    max_amount = max(abs(float(amount)) for amount in amounts)
    if max_amount <= 10_000:
        return "USD"
    if max_amount >= 1_000_000:
        return "VND"

    if source == "itviec":
        return "USD"
    if source in {"topcv", "topdev"}:
        return "VND"
    return np.nan


def repair_salary_scale(amount: object, currency: object) -> float | object:
    if pd.isna(amount):
        return np.nan
    amount = float(amount)
    if pd.isna(currency):
        return amount
    if str(currency).upper() == "VND" and amount >= 1_000_000_000:
        while amount >= 1_000_000_000:
            amount /= 1_000_000
    return amount


def convert_salary_to_vnd(amount: object, currency: object) -> float | object:
    if pd.isna(amount) or pd.isna(currency):
        return np.nan
    rate = SALARY_EXCHANGE_RATES.get(str(currency).upper())
    if rate is None:
        return np.nan
    return float(amount) * rate


def get_salary_band(value: object) -> object:
    if pd.isna(value):
        return np.nan
    amount = float(value)
    if amount < 15_000_000:
        return "<15M"
    if amount < 30_000_000:
        return "15M-30M"
    if amount < 50_000_000:
        return "30M-50M"
    return ">=50M"


def compute_salary_fields(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["salary_min_original"] = enriched["salary_min"].apply(parse_salary_number)
    enriched["salary_max_original"] = enriched["salary_max"].apply(parse_salary_number)
    enriched["currency_original"] = enriched["currency"].apply(normalize_text)

    enriched["salary_currency"] = enriched.apply(
        lambda row: infer_currency(
            row.get("currency"),
            row.get("source"),
            row.get("salary_min_original"),
            row.get("salary_max_original"),
        ),
        axis=1,
    )

    enriched["salary_min_original"] = enriched.apply(
        lambda row: repair_salary_scale(row["salary_min_original"], row["salary_currency"]),
        axis=1,
    )
    enriched["salary_max_original"] = enriched.apply(
        lambda row: repair_salary_scale(row["salary_max_original"], row["salary_currency"]),
        axis=1,
    )

    enriched["salary_min"] = enriched.apply(
        lambda row: convert_salary_to_vnd(row["salary_min_original"], row["salary_currency"]),
        axis=1,
    )
    enriched["salary_max"] = enriched.apply(
        lambda row: convert_salary_to_vnd(row["salary_max_original"], row["salary_currency"]),
        axis=1,
    )

    swap_mask = (
        enriched["salary_min"].notna()
        & enriched["salary_max"].notna()
        & (enriched["salary_min"] > enriched["salary_max"])
    )
    if swap_mask.any():
        min_values = enriched.loc[swap_mask, "salary_min"].copy()
        max_values = enriched.loc[swap_mask, "salary_max"].copy()
        min_original = enriched.loc[swap_mask, "salary_min_original"].copy()
        max_original = enriched.loc[swap_mask, "salary_max_original"].copy()
        enriched.loc[swap_mask, "salary_min"] = max_values
        enriched.loc[swap_mask, "salary_max"] = min_values
        enriched.loc[swap_mask, "salary_min_original"] = max_original
        enriched.loc[swap_mask, "salary_max_original"] = min_original
        log.info("Swapped salary bounds for %d rows", int(swap_mask.sum()))

    enriched["salary_is_estimated"] = 0
    only_min_mask = enriched["salary_min"].notna() & enriched["salary_max"].isna()
    only_max_mask = enriched["salary_min"].isna() & enriched["salary_max"].notna()
    enriched.loc[only_min_mask, "salary_max"] = enriched.loc[only_min_mask, "salary_min"]
    enriched.loc[only_max_mask, "salary_min"] = enriched.loc[only_max_mask, "salary_max"]
    enriched.loc[only_min_mask, "salary_max_original"] = enriched.loc[only_min_mask, "salary_min_original"]
    enriched.loc[only_max_mask, "salary_min_original"] = enriched.loc[only_max_mask, "salary_max_original"]
    enriched.loc[only_min_mask | only_max_mask, "salary_is_estimated"] = 1

    enriched["salary_avg"] = enriched[["salary_min", "salary_max"]].mean(axis=1)
    invalid_mask = (
        enriched["salary_avg"].notna()
        & ((enriched["salary_avg"] < 1_000_000) | (enriched["salary_avg"] > 500_000_000))
    )
    if invalid_mask.any():
        enriched.loc[
            invalid_mask,
            [
                "salary_min",
                "salary_max",
                "salary_avg",
                "salary_min_original",
                "salary_max_original",
                "salary_currency",
                "currency_original",
            ],
        ] = np.nan
        enriched.loc[invalid_mask, "salary_is_estimated"] = 0
        log.warning("Removed %d rows with invalid salary scale", int(invalid_mask.sum()))

    enriched["has_salary"] = enriched["salary_avg"].notna().astype(int)
    enriched["salary_currency"] = enriched["salary_avg"].apply(lambda value: "VND" if pd.notna(value) else np.nan)
    enriched["salary_band"] = enriched["salary_avg"].apply(get_salary_band)
    return enriched


def parse_experience_years(value: object) -> float | object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan
    numbers = re.findall(r"\d+(?:\.\d+)?", str(text))
    if not numbers:
        return np.nan
    values = [float(number) for number in numbers]
    if len(values) >= 2:
        return round((min(values) + max(values)) / 2, 1)
    return values[0]


def get_experience_band(value: object) -> object:
    if pd.isna(value):
        return np.nan
    years = float(value)
    if years < 1:
        return "<1 year"
    if years < 3:
        return "1-2 years"
    if years < 5:
        return "3-4 years"
    if years <= 8:
        return "5-8 years"
    return ">8 years"


def normalize_level(raw_level: object, job_title: object, experience_years: object) -> object:
    text = normalize_text(raw_level)
    if pd.notna(text):
        key = slugify_key(text)
        for keyword, level in LEVEL_MAP.items():
            if keyword in key:
                return level

    title_key = slugify_key(job_title)
    title_key = title_key.replace(" sr ", " senior ").replace(" jr ", " junior ")
    if title_key.startswith("sr "):
        title_key = f"senior {title_key[3:]}"
    if title_key.startswith("jr "):
        title_key = f"junior {title_key[3:]}"
    if "truong phong" in title_key or "head of" in title_key:
        return "Manager"
    if "chuyen gia" in title_key or "expert" in title_key:
        return "Senior"
    if "specialist" in title_key and pd.isna(experience_years):
        return "Senior"
    for keyword, level in LEVEL_MAP.items():
        if keyword in title_key:
            return level

    if pd.notna(experience_years):
        years = float(experience_years)
        if years < 1:
            return "Intern/Fresher"
        if years < 3:
            return "Junior"
        if years < 5:
            return "Middle"
        if years <= 8:
            return "Senior"
        return "Lead"

    return "Unknown"


def normalize_job_title_group(job_title: object, tech_stack: object = np.nan, job_description: object = np.nan) -> object:
    text = normalize_text(job_title)
    if pd.isna(text):
        return np.nan

    key = f" {slugify_key(text)} "
    stack_key = slugify_key(tech_stack)
    desc_key = slugify_key(job_description)
    combined_key = f" {key} {stack_key} {desc_key} "
    for group_name, patterns in JOB_TITLE_GROUP_RULES:
        if any(pattern in combined_key for pattern in patterns):
            return group_name

    if any(pattern in combined_key for pattern in ["ui ux", "ux ui", "product designer", "ui designer", "ux designer", "web designer", "artist"]):
        return "Other IT Roles"
    if any(pattern in combined_key for pattern in ["dba", "database administrator", "system engineer", "system admin", "windows engineer", "monitoring engineer", "server operator", "network operation", "network engineer", "cloud consultant", "site reliability"]):
        return "DevOps/Cloud/Security"
    if any(pattern in combined_key for pattern in ["software engineer", "software developer", "java engineer", "java developer", "dot net", ".net", "c#", "spring boot", "laravel", "ruby on rails", "php", "golang", "python"]) and not any(pattern in combined_key for pattern in ["react", "vue", "angular", "frontend", "fontend", "front end"]):
        return "Back-end Developer"
    if any(pattern in combined_key for pattern in ["react", "vue", "next", "angular", "html css", "frontend", "fontend", "front end", "javascript", "typescript"]) and not any(pattern in combined_key for pattern in ["backend", "back end", "api", "spring", ".net", "java", "php", "golang", "python"]):
        return "Front-end Developer"
    if any(pattern in combined_key for pattern in ["ai", "llm", "genai", "machine learning", "computer vision", "data science", "mlops"]):
        return "Data Analyst/Data Scientist/BI"
    if any(pattern in combined_key for pattern in ["power bi", "tableau", "business intelligence", "bi publisher", "reporting", "analytics"]) and not any(pattern in combined_key for pattern in ["project manager", "product manager"]):
        return "Data Analyst/Data Scientist/BI"
    if any(pattern in combined_key for pattern in ["scrum master", "technical pm", "delivery lead"]):
        return "Project Leader/Project Manager"
    if any(pattern in combined_key for pattern in ["engineering manager", "software engineering manager", "delivery manager"]):
        return "IT Manager"
    if any(pattern in combined_key for pattern in ["salesforce", "power platform", "dynamics 365"]):
        return "ERP Engineer/ERP Consultant"
    if any(pattern in combined_key for pattern in ["corebanking", "it support", "helpdesk", "appops", "van hanh ung dung", "khai thac ung dung"]):
        return "IT Support/Helpdesk"
    if "developer" in combined_key or "engineer" in combined_key or "programmer" in combined_key:
        return "Other IT Roles"
    return "Other IT Roles"


def normalize_company_type(
    raw_company_type: object = np.nan,
    company_name: object = np.nan,
    company_industry: object = np.nan,
    job_description: object = np.nan,
) -> object:
    raw_text = normalize_text(raw_company_type)
    if pd.notna(raw_text):
        raw_key = slugify_key(raw_text)
        for key, value in RAW_COMPANY_TYPE_MAP.items():
            if key in raw_key:
                return value

    company_name_key = slugify_key(company_name)
    company_industry_key = slugify_key(company_industry)
    description_key = slugify_key(job_description)

    if any(name in company_name_key for name in KNOWN_PRODUCT_COMPANIES):
        return "Product"
    if any(name in company_name_key for name in KNOWN_OUTSOURCE_COMPANIES):
        return "Outsource"
    if any(name in company_name_key for name in KNOWN_SERVICE_COMPANIES):
        return "Service/Consulting"
    if any(name in company_name_key for name in KNOWN_NON_IT_COMPANIES):
        return "Non-IT"

    search_key = f"{company_name_key} {company_industry_key} {description_key}".strip()
    if any(keyword in search_key for keyword in STARTUP_KEYWORDS):
        return "Startup"
    if any(keyword in search_key for keyword in OUTSOURCE_KEYWORDS):
        return "Outsource"
    if any(keyword in search_key for keyword in PRODUCT_KEYWORDS):
        return "Product"
    if any(keyword in company_name_key or keyword in company_industry_key for keyword in NON_IT_KEYWORDS):
        return "Non-IT"
    if any(keyword in company_name_key for keyword in SERVICE_KEYWORDS):
        return "Service/Consulting"
    service_matches = sum(keyword in search_key for keyword in SERVICE_KEYWORDS)
    if service_matches >= 2:
        return "Service/Consulting"
    return np.nan


def is_company_type_inferred(raw_company_type: object, normalized_company_type: object) -> int:
    return int(pd.isna(normalize_text(raw_company_type)) and pd.notna(normalized_company_type))


def parse_posted_date(value: object, source: object) -> object:
    text = normalize_text(value)
    if pd.isna(text):
        return pd.NaT
    key = str(source or "")
    if key == "topcv":
        return pd.to_datetime(text, errors="coerce", dayfirst=False)
    return pd.to_datetime(text, errors="coerce", dayfirst=False)


def parse_deadline(value: object) -> object:
    text = normalize_text(value)
    if pd.isna(text):
        return pd.NaT
    return pd.to_datetime(text, errors="coerce", dayfirst=True)


def extract_crawl_date_from_path(path: Path) -> object:
    match = re.search(r"(\d{8})_(\d{6})", path.stem)
    if not match:
        return pd.NaT
    return pd.to_datetime("".join(match.groups()), format="%Y%m%d%H%M%S", errors="coerce")


def make_title_key(value: object) -> str:
    key = slugify_key(value)
    key = re.sub(r"\b(junior|middle|mid|senior|lead|principal|staff|intern|fresher|manager)\b", " ", key)
    return re.sub(r"\s+", " ", key).strip()


def build_job_id(row: pd.Series) -> str:
    date_value = row.get("posted_date")
    if pd.isna(date_value):
        date_value = row.get("deadline")
    key_parts = [
        str(row.get("source", "")),
        str(row.get("title_key", "")),
        str(row.get("company_key", "")),
        str(row.get("location", "")),
        str(date_value or ""),
        str(row.get("salary_min_original", "")),
        str(row.get("salary_max_original", "")),
    ]
    digest = hashlib.md5("||".join(key_parts).encode("utf-8")).hexdigest()
    return digest[:16]


def build_dedup_key(row: pd.Series) -> str:
    key_parts = [
        str(row.get("source", "")),
        str(row.get("title_key", "")),
        str(row.get("company_key", "")),
        str(row.get("location", "")),
    ]
    return "||".join(key_parts)


def build_fuzzy_group_key(row: pd.Series) -> str:
    key_parts = [
        str(row.get("source", "")),
        str(row.get("company_key", "")),
        str(row.get("location", "")),
    ]
    return "||".join(key_parts)


def should_merge_fuzzy_duplicate(left: pd.Series, right: pd.Series) -> bool:
    left_title = str(left.get("title_key", ""))
    right_title = str(right.get("title_key", ""))
    if not left_title or not right_title:
        return False

    similarity = SequenceMatcher(None, left_title, right_title).ratio()
    if similarity < 0.92:
        return False

    left_date = left.get("posted_date")
    right_date = right.get("posted_date")
    if pd.notna(left_date) and pd.notna(right_date):
        if abs((pd.Timestamp(left_date) - pd.Timestamp(right_date)).days) > 14:
            return False

    left_salary = left.get("salary_avg")
    right_salary = right.get("salary_avg")
    if pd.notna(left_salary) and pd.notna(right_salary):
        base = max(float(left_salary), float(right_salary), 1.0)
        if abs(float(left_salary) - float(right_salary)) / base > 0.3:
            return False

    return True


def drop_fuzzy_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    kept_indices: list[int] = []
    dropped_count = 0

    for _, group in df.groupby("fuzzy_group_key", sort=False):
        kept_rows: list[pd.Series] = []
        for row in group.itertuples(index=True):
            row_series = df.loc[row.Index]
            if any(should_merge_fuzzy_duplicate(row_series, kept_row) for kept_row in kept_rows):
                dropped_count += 1
                continue
            kept_indices.append(row.Index)
            kept_rows.append(row_series)

    deduped = df.loc[kept_indices].copy().reset_index(drop=True)
    return deduped, dropped_count


def compute_row_quality(row: pd.Series) -> float:
    score = 0.0
    score += float(pd.notna(row.get("salary_avg"))) * 4.0
    score += float(pd.notna(row.get("posted_date"))) * 2.0
    score += float(pd.notna(row.get("deadline"))) * 1.0
    score += float(pd.notna(row.get("company_industry"))) * 1.0
    score += float(pd.notna(row.get("job_description"))) * 2.0
    score += float(pd.notna(row.get("tech_stack"))) * 1.0
    score += min(len(str(row.get("job_description") or "")), 5_000) / 5_000
    return score


def load_raw_files(input_paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in input_paths:
        source = "itviec" if "itviec" in path.stem.lower() else "topcv" if "topcv" in path.stem.lower() else "topdev" if "topdev" in path.stem.lower() else path.stem.lower()
        frame = pd.read_csv(path)
        frame["source"] = source
        frame["crawl_date"] = extract_crawl_date_from_path(path)
        log.info("Loaded %-30s rows=%d source=%s", path.name, len(frame), source)
        frames.append(frame)

    if not frames:
        raise ValueError("No input CSV files found to clean.")

    merged = pd.concat(frames, ignore_index=True, sort=False)
    merged = ensure_core_columns(merged)
    log.info("Total rows after merge: %d", len(merged))
    return merged


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = ensure_core_columns(df).copy()
    n_original = len(cleaned)

    for column in ["source", "job_title", "company_name", "location", "remote_option", "tech_stack", "company_type", "company_industry", "job_description"]:
        cleaned[column] = cleaned[column].apply(normalize_free_text)

    cleaned["source"] = cleaned["source"].apply(normalize_source_name)
    cleaned["crawl_date"] = pd.to_datetime(cleaned["crawl_date"], errors="coerce")
    cleaned["job_title_raw"] = cleaned["job_title"]
    cleaned["location_raw"] = cleaned["location"]
    cleaned["remote_option_raw"] = cleaned["remote_option"]
    cleaned["company_type_raw"] = cleaned["company_type"]
    cleaned["experience_raw"] = cleaned["experience_years"]

    cleaned["location_list"] = cleaned["location"].apply(normalize_location)
    cleaned["primary_city"] = cleaned["location"].apply(get_primary_city)
    cleaned["is_multi_location"] = cleaned["location"].apply(lambda value: int(len(split_locations(value)) > 1))
    cleaned["location_bucket"] = cleaned["primary_city"].apply(get_location_bucket)
    cleaned["location"] = cleaned["primary_city"]

    cleaned["remote_option"] = cleaned.apply(
        lambda row: normalize_remote_option(
            row.get("remote_option_raw"),
            row.get("job_title"),
            row.get("location_raw"),
            row.get("job_description"),
        ),
        axis=1,
    )

    cleaned["experience_years"] = cleaned["experience_years"].apply(parse_experience_years)
    cleaned["experience_band"] = cleaned["experience_years"].apply(get_experience_band)
    cleaned["job_title_group"] = cleaned.apply(
        lambda row: normalize_job_title_group(
            row.get("job_title"),
            row.get("tech_stack"),
            row.get("job_description"),
        ),
        axis=1,
    )

    raw_level = cleaned["level"] if "level" in cleaned.columns else pd.Series(np.nan, index=cleaned.index)
    cleaned["level"] = cleaned.apply(
        lambda row: normalize_level(raw_level[row.name], row.get("job_title"), row.get("experience_years")),
        axis=1,
    )
    cleaned["level_inferred"] = raw_level.apply(normalize_text).isna().astype(int)

    cleaned["company_type"] = cleaned.apply(
        lambda row: normalize_company_type(
            row.get("company_type_raw"),
            row.get("company_name"),
            row.get("company_industry"),
            row.get("job_description"),
        ),
        axis=1,
    )
    cleaned["company_type_inferred"] = cleaned.apply(
        lambda row: is_company_type_inferred(row.get("company_type_raw"), row.get("company_type")),
        axis=1,
    )

    cleaned = compute_salary_fields(cleaned)

    cleaned["posted_date"] = cleaned.apply(
        lambda row: parse_posted_date(row.get("posted_date"), row.get("source")),
        axis=1,
    )
    cleaned["deadline"] = cleaned["deadline"].apply(parse_deadline)

    cleaned["title_key"] = cleaned["job_title"].apply(make_title_key)
    cleaned["company_key"] = cleaned["company_name"].apply(slugify_key)
    cleaned["row_quality_score"] = cleaned.apply(compute_row_quality, axis=1)
    cleaned["dedup_key"] = cleaned.apply(build_dedup_key, axis=1)
    cleaned["fuzzy_group_key"] = cleaned.apply(build_fuzzy_group_key, axis=1)

    cleaned = (
        cleaned.sort_values(
            by=["dedup_key", "row_quality_score", "salary_avg"],
            ascending=[True, False, False],
            na_position="last",
        )
        .drop_duplicates(subset=["dedup_key"], keep="first")
        .reset_index(drop=True)
    )

    cleaned, fuzzy_dropped = drop_fuzzy_duplicates(cleaned)
    if fuzzy_dropped:
        log.info("Dropped %d fuzzy duplicate rows", fuzzy_dropped)

    cleaned["job_id"] = cleaned.apply(build_job_id, axis=1)
    cleaned = cleaned.drop_duplicates(subset=["job_id"]).reset_index(drop=True)

    cleaned["primary_language_hint"] = cleaned["job_title"].apply(
        lambda value: next((lang for lang in MAJOR_LANGUAGE_HINTS if lang in slugify_key(value)), np.nan)
    )

    cleaned = cleaned.drop(columns=["title_key", "company_key", "dedup_key", "fuzzy_group_key", "row_quality_score"], errors="ignore")

    ordered_columns = EXPECTED_COLUMNS + [
        "crawl_date",
        "experience_band",
        "location_bucket",
        "location_list",
        "primary_city",
        "is_multi_location",
        "remote_option",
        "remote_option_raw",
        "tech_stack",
        "company_type_raw",
        "company_type_inferred",
        "company_industry",
        "job_description",
        "posted_date",
        "deadline",
        "has_salary",
        "salary_band",
        "salary_is_estimated",
        "salary_min_original",
        "salary_max_original",
        "currency_original",
        "location_raw",
        "experience_raw",
        "level_inferred",
        "primary_language_hint",
        "job_title_raw",
    ]
    ordered_columns = unique_preserve_order(ordered_columns)
    remaining_columns = [column for column in cleaned.columns if column not in ordered_columns]
    cleaned = cleaned[ordered_columns + remaining_columns]

    log.info("Cleaning done: %d -> %d rows", n_original, len(cleaned))
    return cleaned


def build_qa_summary(cleaned: pd.DataFrame, n_raw: int) -> pd.DataFrame:
    rows = [
        ("raw_rows", n_raw),
        ("clean_rows", len(cleaned)),
        ("dropped_rows", n_raw - len(cleaned)),
        ("rows_with_salary", int(cleaned["has_salary"].sum())),
        ("salary_coverage", round(float(cleaned["has_salary"].mean()), 4)),
        ("unique_locations", int(cleaned["location"].nunique(dropna=True))),
        ("unique_location_buckets", int(cleaned["location_bucket"].nunique(dropna=True))),
        ("unique_job_title_groups", int(cleaned["job_title_group"].nunique(dropna=True))),
        ("unique_levels", int(cleaned["level"].nunique(dropna=True))),
        ("multi_location_rows", int(cleaned["is_multi_location"].sum())),
        ("company_type_inferred_rows", int(cleaned["company_type_inferred"].sum())),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def build_missingness_summary(raw_df: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    raw_missing = raw_df.isna().mean().rename("missing_ratio_raw")
    clean_missing = cleaned.isna().mean().rename("missing_ratio_clean")
    missing = pd.concat([raw_missing, clean_missing], axis=1).reset_index()
    return missing.rename(columns={"index": "column"})


def build_category_summary(raw_df: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    raw_location = raw_df["location"].apply(normalize_location).fillna("Missing")
    clean_location = cleaned["location_bucket"].fillna("Missing")
    raw_remote = raw_df.apply(
        lambda row: normalize_remote_option(
            row.get("remote_option"),
            row.get("job_title"),
            np.nan,
            row.get("job_description"),
        ),
        axis=1,
    ).fillna("Missing")
    clean_remote = cleaned["remote_option"].fillna("Missing")

    if "level" in raw_df.columns:
        raw_level = raw_df.apply(
            lambda row: normalize_level(row.get("level"), row.get("job_title"), parse_experience_years(row.get("experience_years"))),
            axis=1,
        ).fillna("Missing")
    else:
        raw_level = pd.Series("Missing", index=raw_df.index)
    clean_level = cleaned["level"].fillna("Missing")

    raw_role = raw_df["job_title"].fillna("Missing")
    clean_role = cleaned["job_title_group"].fillna("Missing")

    category_frames = [
        raw_location.value_counts().rename_axis("category").reset_index(name="count").assign(field="location", stage="raw"),
        clean_location.value_counts().rename_axis("category").reset_index(name="count").assign(field="location", stage="clean"),
        raw_remote.value_counts().rename_axis("category").reset_index(name="count").assign(field="remote_option", stage="raw"),
        clean_remote.value_counts().rename_axis("category").reset_index(name="count").assign(field="remote_option", stage="clean"),
        raw_level.value_counts().rename_axis("category").reset_index(name="count").assign(field="level", stage="raw"),
        clean_level.value_counts().rename_axis("category").reset_index(name="count").assign(field="level", stage="clean"),
        raw_role.value_counts().head(25).rename_axis("category").reset_index(name="count").assign(field="job_title_group", stage="raw_title_top25"),
        clean_role.value_counts().rename_axis("category").reset_index(name="count").assign(field="job_title_group", stage="clean"),
    ]
    return pd.concat(category_frames, ignore_index=True)


def build_anomaly_report(cleaned: pd.DataFrame) -> pd.DataFrame:
    anomalies: list[dict[str, object]] = []

    weird_locations = cleaned.loc[
        cleaned["location"].fillna("").astype(str).str.len().gt(25),
        ["job_id", "job_title", "location_raw", "location"],
    ].head(20)
    for row in weird_locations.itertuples(index=False):
        anomalies.append({
            "anomaly_type": "long_location_label",
            "job_id": row.job_id,
            "job_title": row.job_title,
            "detail": f"{row.location_raw} -> {row.location}",
        })

    unknown_levels = cleaned.loc[cleaned["level"].eq("Unknown"), ["job_id", "job_title", "experience_raw"]].head(20)
    for row in unknown_levels.itertuples(index=False):
        anomalies.append({
            "anomaly_type": "unknown_level",
            "job_id": row.job_id,
            "job_title": row.job_title,
            "detail": row.experience_raw,
        })

    uncategorized_roles = cleaned.loc[cleaned["job_title_group"].eq("Other IT Roles"), ["job_id", "job_title"]].head(30)
    for row in uncategorized_roles.itertuples(index=False):
        anomalies.append({
            "anomaly_type": "other_it_role",
            "job_id": row.job_id,
            "job_title": row.job_title,
            "detail": "Review title taxonomy",
        })

    return pd.DataFrame(anomalies)


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def resolve_input_paths(inputs: list[str] | None, input_dir: Path | None) -> list[Path]:
    if inputs:
        return [Path(path) for path in inputs]
    search_dir = input_dir or Path("data/raw")
    return sorted(search_dir.glob("*.csv"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge and clean raw recruitment CSV files.")
    parser.add_argument("--inputs", nargs="*", help="One or more raw CSV files to merge and clean.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"), help="Directory containing raw CSV files.")
    parser.add_argument("--output", type=Path, default=Path("data/clean-data/jobs_cleaned.csv"), help="Output cleaned CSV file.")
    parser.add_argument("--salary-output", type=Path, default=Path("data/clean-data/jobs_salary_subset.csv"), help="Output CSV file containing only rows with usable salary.")
    parser.add_argument("--qa-output", type=Path, default=Path("data/clean-data/jobs_cleaned_qa.csv"), help="Output CSV file with quick QA metrics.")
    args = parser.parse_args()

    input_paths = resolve_input_paths(args.inputs, args.input_dir)
    merged = load_raw_files(input_paths)
    cleaned = clean_jobs(merged)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.output, index=False, na_rep="")

    salary_subset = cleaned.loc[cleaned["has_salary"] == 1].reset_index(drop=True)
    args.salary_output.parent.mkdir(parents=True, exist_ok=True)
    salary_subset.to_csv(args.salary_output, index=False, na_rep="")

    qa = build_qa_summary(cleaned, len(merged))
    args.qa_output.parent.mkdir(parents=True, exist_ok=True)
    qa.to_csv(args.qa_output, index=False)

    qa_missing_output = args.qa_output.with_name(f"{args.qa_output.stem}_missingness{args.qa_output.suffix}")
    qa_category_output = args.qa_output.with_name(f"{args.qa_output.stem}_categories{args.qa_output.suffix}")
    qa_anomaly_output = args.qa_output.with_name(f"{args.qa_output.stem}_anomalies{args.qa_output.suffix}")

    missingness = build_missingness_summary(merged, cleaned)
    category_summary = build_category_summary(merged, cleaned)
    anomalies = build_anomaly_report(cleaned)

    missingness.to_csv(qa_missing_output, index=False)
    category_summary.to_csv(qa_category_output, index=False)
    anomalies.to_csv(qa_anomaly_output, index=False)

    log.info("Saved cleaned dataset with %d rows to %s", len(cleaned), args.output)
    log.info("Saved salary subset with %d rows to %s", len(salary_subset), args.salary_output)
    log.info("Saved QA summary to %s", args.qa_output)
    log.info("Saved QA missingness to %s", qa_missing_output)
    log.info("Saved QA categories to %s", qa_category_output)
    log.info("Saved QA anomalies to %s", qa_anomaly_output)


if __name__ == "__main__":
    main()
