from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config import EXPECTED_COLUMNS
SALARY_EXCHANGE_RATES = {
    "VND": 1.0,
    "USD": 25_000.0,
}

DEFAULT_CURRENCY_BY_SOURCE = {
    "itviec": "USD",
    "topcv": "VND",
}

LOCATION_MAP = {
    "ha noi": "Ha Noi",
    "hanoi": "Ha Noi",
    "hn": "Ha Noi",
    "ha noi city": "Ha Noi",
    "tp ha noi": "Ha Noi",
    "hcm": "Ho Chi Minh",
    "hcmc": "Ho Chi Minh",
    "ho chi minh": "Ho Chi Minh",
    "ho chi minh city": "Ho Chi Minh",
    "tp hcm": "Ho Chi Minh",
    "tp. hcm": "Ho Chi Minh",
    "da nang": "Da Nang",
    "danang": "Da Nang",
}

REMOTE_MAP = {
    "onsite": "onsite",
    "on-site": "onsite",
    "office": "onsite",
    "hybrid": "hybrid",
    "remote": "remote",
    "work from home": "remote",
    "wfh": "remote",
}


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_text(value: object) -> object:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text or np.nan


def slugify_key(value: object) -> str:
    if pd.isna(value):
        return ""
    text = strip_accents(str(value).lower())
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_location(value: object) -> object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan

    normalized_parts: list[str] = []
    for raw_part in re.split(r"[,&/]+", str(text)):
        key = slugify_key(raw_part)
        if not key:
            continue
        cleaned = LOCATION_MAP.get(key)
        if cleaned is None:
            cleaned = raw_part.strip().title()
        if cleaned not in normalized_parts:
            normalized_parts.append(cleaned)

    if not normalized_parts:
        return np.nan
    return " | ".join(normalized_parts)


def normalize_remote_option(value: object) -> object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan
    key = slugify_key(text)
    return REMOTE_MAP.get(key, text.lower())


def parse_experience_years(value: object) -> float | object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan

    numbers = re.findall(r"\d+(?:\.\d+)?", str(text))
    if not numbers:
        return np.nan

    numbers_float = [float(number) for number in numbers]
    return max(numbers_float)


def normalize_currency(value: object, source: str, salary_min: object, salary_max: object) -> object:
    text = normalize_text(value)
    if pd.notna(text):
        upper = str(text).upper()
        if upper in SALARY_EXCHANGE_RATES:
            return upper

    if pd.notna(salary_min) or pd.notna(salary_max):
        return DEFAULT_CURRENCY_BY_SOURCE.get(source, np.nan)

    return np.nan


def convert_salary_to_vnd(amount: object, currency: object) -> float | object:
    if pd.isna(amount) or pd.isna(currency):
        return np.nan
    rate = SALARY_EXCHANGE_RATES.get(str(currency).upper())
    if rate is None:
        return np.nan
    return float(amount) * rate


def compute_salary_fields(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["salary_min"] = pd.to_numeric(enriched["salary_min"], errors="coerce")
    enriched["salary_max"] = pd.to_numeric(enriched["salary_max"], errors="coerce")

    enriched["salary_currency"] = enriched.apply(
        lambda row: normalize_currency(row.get("currency"), row["source"], row["salary_min"], row["salary_max"]),
        axis=1,
    )

    enriched["salary_min_original"] = enriched["salary_min"]
    enriched["salary_max_original"] = enriched["salary_max"]

    enriched["salary_min"] = enriched.apply(
        lambda row: convert_salary_to_vnd(row["salary_min"], row["salary_currency"]),
        axis=1,
    )
    enriched["salary_max"] = enriched.apply(
        lambda row: convert_salary_to_vnd(row["salary_max"], row["salary_currency"]),
        axis=1,
    )

    swap_mask = (
        enriched["salary_min"].notna()
        & enriched["salary_max"].notna()
        & (enriched["salary_min"] > enriched["salary_max"])
    )
    if swap_mask.any():
        min_values = enriched.loc[swap_mask, "salary_min"].copy()
        enriched.loc[swap_mask, "salary_min"] = enriched.loc[swap_mask, "salary_max"]
        enriched.loc[swap_mask, "salary_max"] = min_values

    enriched["salary_is_estimated"] = 0
    only_min_mask = enriched["salary_min"].notna() & enriched["salary_max"].isna()
    only_max_mask = enriched["salary_min"].isna() & enriched["salary_max"].notna()

    enriched.loc[only_min_mask, "salary_max"] = enriched.loc[only_min_mask, "salary_min"]
    enriched.loc[only_max_mask, "salary_min"] = enriched.loc[only_max_mask, "salary_max"]
    enriched.loc[only_min_mask | only_max_mask, "salary_is_estimated"] = 1

    enriched["salary_avg"] = enriched[["salary_min", "salary_max"]].mean(axis=1)

    invalid_salary_mask = (
        enriched["salary_avg"].notna()
        & ((enriched["salary_avg"] < 1_000_000) | (enriched["salary_avg"] > 500_000_000))
    )
    enriched.loc[invalid_salary_mask, ["salary_min", "salary_max", "salary_avg"]] = np.nan
    enriched.loc[invalid_salary_mask, "salary_is_estimated"] = 0

    return enriched


def normalize_level(job_title: object, experience_years: object) -> object:
    title_text = slugify_key(job_title)
    years = float(experience_years) if pd.notna(experience_years) else np.nan

    if any(keyword in title_text for keyword in ["intern", "thuc tap"]):
        return "Intern"
    if any(keyword in title_text for keyword in ["fresher", "junior", "entry level", "entrylevel"]):
        return "Junior"
    if any(keyword in title_text for keyword in ["senior", "lead", "principal", "manager", "architect", "head"]):
        if "lead" in title_text:
            return "Lead"
        if "manager" in title_text or "head" in title_text:
            return "Manager"
        return "Senior"

    if pd.notna(years):
        if years < 1:
            return "Intern"
        if years <= 2:
            return "Junior"
        if years <= 4:
            return "Middle"
        if years <= 6:
            return "Senior"
        return "Lead"

    return np.nan


def normalize_company_type(company_name: object) -> object:
    text = normalize_text(company_name)
    if pd.isna(text):
        return np.nan

    key = slugify_key(text)
    if any(keyword in key for keyword in ["ngan hang", "bank", "chung khoan", "bao hiem", "finance", "fintech"]):
        return "Finance"
    if any(keyword in key for keyword in ["giao duc", "education", "university", "academy", "school"]):
        return "Education"
    if any(keyword in key for keyword in ["health", "benh vien", "medical", "pharma"]):
        return "Healthcare"
    if any(keyword in key for keyword in ["solution", "software", "technology", "tech", "system", "digital"]):
        return "Technology"
    if any(keyword in key for keyword in ["logistics", "shipping", "delivery", "giao hang"]):
        return "Logistics"
    if any(keyword in key for keyword in ["real estate", "bat dong san", "property"]):
        return "Real Estate"
    return "Other"


def build_job_id(row: pd.Series) -> str:
    key_parts = [
        str(row.get("source", "")),
        str(row.get("job_title", "")),
        str(row.get("company_name", "")),
        str(row.get("location", "")),
        str(row.get("salary_min", "")),
        str(row.get("salary_max", "")),
    ]
    digest = hashlib.md5("||".join(key_parts).encode("utf-8")).hexdigest()
    return digest[:16]


def load_raw_files(input_paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for path in input_paths:
        source = "itviec" if "itviec" in path.stem.lower() else "topcv" if "topcv" in path.stem.lower() else path.stem.lower()
        frame = pd.read_csv(path)
        frame["source"] = source
        frames.append(frame)

    if not frames:
        raise ValueError("No input CSV files found to clean.")

    return pd.concat(frames, ignore_index=True)


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    for column in ["job_title", "company_name", "location", "remote_option", "tech_stack"]:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].apply(normalize_text)

    cleaned["location"] = cleaned["location"].apply(normalize_location)
    cleaned["remote_option"] = cleaned["remote_option"].apply(normalize_remote_option)
    cleaned["experience_years"] = cleaned["experience_years"].apply(parse_experience_years)

    cleaned = compute_salary_fields(cleaned)

    cleaned["level"] = cleaned.apply(
        lambda row: normalize_level(row.get("job_title"), row.get("experience_years")),
        axis=1,
    )
    cleaned["company_type"] = cleaned["company_name"].apply(normalize_company_type)

    cleaned["job_id"] = cleaned.apply(build_job_id, axis=1)

    cleaned = cleaned.drop_duplicates(subset=["job_id"]).reset_index(drop=True)
    ordered_columns = EXPECTED_COLUMNS + [
        "remote_option",
        "tech_stack",
        "salary_is_estimated",
        "salary_min_original",
        "salary_max_original",
    ]
    remaining_columns = [column for column in cleaned.columns if column not in ordered_columns]
    cleaned = cleaned[[column for column in ordered_columns if column in cleaned.columns] + remaining_columns]

    return cleaned


def resolve_input_paths(inputs: list[str] | None, input_dir: Path | None) -> list[Path]:
    if inputs:
        return [Path(path) for path in inputs]

    search_dir = input_dir or Path("data/raw")
    return sorted(search_dir.glob("*.csv"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge and clean raw recruitment CSV files.")
    parser.add_argument("--inputs", nargs="*", help="One or more raw CSV files to merge and clean.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"), help="Directory containing raw CSV files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/clean-data/jobs_cleaned.csv"),
        help="Output cleaned CSV file.",
    )
    args = parser.parse_args()

    input_paths = resolve_input_paths(args.inputs, args.input_dir)
    merged = load_raw_files(input_paths)
    cleaned = clean_jobs(merged)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.output, index=False, na_rep="NaN")

    n_salary_known = int(cleaned["salary_avg"].notna().sum())
    print(f"Saved cleaned dataset with {len(cleaned)} rows to {args.output}")
    print(f"Rows with usable salary_avg: {n_salary_known}")
    print(f"Rows with missing salary_avg: {len(cleaned) - n_salary_known}")


if __name__ == "__main__":
    main()
