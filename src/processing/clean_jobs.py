from __future__ import annotations

import argparse
import hashlib
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config import EXPECTED_COLUMNS
from src.processing.utils import normalize_text, slugify_key, strip_accents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Constants
SALARY_EXCHANGE_RATES = {
    "VND": 1.0,
    "USD": 25_000.0,
}

# (#1) Thêm TopDev default currency
DEFAULT_CURRENCY_BY_SOURCE = {
    "itviec": "USD",
    "topcv": "VND",
    "topdev": "VND",
}

# (#9) Bổ sung thêm nhiều tỉnh thành phổ biến
LOCATION_MAP = {
    # Ha Noi
    "ha noi": "Ha Noi",
    "hanoi": "Ha Noi",
    "hn": "Ha Noi",
    "ha noi city": "Ha Noi",
    "tp ha noi": "Ha Noi",
    "thanh pho ha noi": "Ha Noi",
    # Ho Chi Minh
    "hcm": "Ho Chi Minh",
    "hcmc": "Ho Chi Minh",
    "ho chi minh": "Ho Chi Minh",
    "ho chi minh city": "Ho Chi Minh",
    "tp hcm": "Ho Chi Minh",
    "tp. hcm": "Ho Chi Minh",
    "tp ho chi minh": "Ho Chi Minh",
    "thanh pho ho chi minh": "Ho Chi Minh",
    "sai gon": "Ho Chi Minh",
    "saigon": "Ho Chi Minh",
    # Da Nang
    "da nang": "Da Nang",
    "danang": "Da Nang",
    "tp da nang": "Da Nang",
    "thanh pho da nang": "Da Nang",
    # Hai Phong
    "hai phong": "Hai Phong",
    "haiphong": "Hai Phong",
    "tp hai phong": "Hai Phong",
    # Binh Duong
    "binh duong": "Binh Duong",
    "tp binh duong": "Binh Duong",
    "thu dau mot": "Binh Duong",
    # Dong Nai
    "dong nai": "Dong Nai",
    "bien hoa": "Dong Nai",
    # Can Tho
    "can tho": "Can Tho",
    "tp can tho": "Can Tho",
    # Hue
    "hue": "Hue",
    "thua thien hue": "Hue",
    # Bac Ninh
    "bac ninh": "Bac Ninh",
    # Khanh Hoa / Nha Trang
    "nha trang": "Khanh Hoa",
    "khanh hoa": "Khanh Hoa",
    # Quang Ninh
    "quang ninh": "Quang Ninh",
    "ha long": "Quang Ninh",
    # Other provinces
    "vinh phuc": "Vinh Phuc",
    "hung yen": "Hung Yen",
    "ha nam": "Ha Nam",
    "thai nguyen": "Thai Nguyen",
    "lam dong": "Lam Dong",
    "da lat": "Lam Dong",
    "vung tau": "Ba Ria Vung Tau",
    "ba ria vung tau": "Ba Ria Vung Tau",
    "long an": "Long An",
    "tay ninh": "Tay Ninh",
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

# (#6) Danh sách công ty IT lớn tại VN để phân loại company_type chính xác hơn
KNOWN_TECH_COMPANIES = {
    "fpt",
    "vng",
    "tiki",
    "shopee",
    "momo",
    "vnpay",
    "viettel",
    "cmcglobal",
    "cmc global",
    "cmc",
    "kms technology",
    "kms",
    "nashtech",
    "nfq",
    "axon",
    "fossil",
    "tpbank",
    "zalopay",
    "zalo",
    "being",
    "saigon technology",
    "co well asia",
    "rikkeisoft",
    "ntt data",
    "grab",
    "lazada",
    "bosch",
    "samsung",
    "lg",
    "fujitsu",
    "nec",
    "line",
    "tencent",
    "money forward",
    "sun asterisk",
    "vti",
    "nal",
    "sendo",
    "onemount",
    "one mount",
    "vnlife",
    "ekoios",
    "devoteam",
    "logigear",
    "orient software",
    "techcombank",
    "mbbank",
    "mb bank",
    "vpbank",
    "vpn bank",
}


# ---------------------------------------------------------------------------
# Normalization helpers (dùng utils chung — #10)
# ---------------------------------------------------------------------------


def normalize_location(value: object) -> object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan

    normalized_parts: list[str] = []
    for raw_part in re.split(r"[,&/|]+|\s+-\s+", str(text)):
        sanitized_part = re.sub(r"\([^)]*\)", " ", str(raw_part))
        key = slugify_key(sanitized_part)
        key = re.sub(r"\b(moi|new)\b", " ", key)
        key = re.sub(r"\b(thanh pho|tp)\b", " ", key)
        key = re.sub(r"\s+", " ", key).strip()
        if not key:
            continue
        cleaned = LOCATION_MAP.get(key)
        if cleaned is None and (key == "noi khac" or re.fullmatch(r"\d+\s+noi\s+khac", key)):
            cleaned = "Others"
        if cleaned is None:
            cleaned = " ".join(token.capitalize() for token in key.split())
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


# (#7) Đổi sang trung bình thay vì max
def parse_experience_years(value: object) -> float | object:
    text = normalize_text(value)
    if pd.isna(text):
        return np.nan

    numbers = re.findall(r"\d+(?:\.\d+)?", str(text))
    if not numbers:
        return np.nan

    numbers_float = [float(number) for number in numbers]
    if len(numbers_float) >= 2:
        return round((min(numbers_float) + max(numbers_float)) / 2, 1)
    return numbers_float[0]


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
        n_swapped = int(swap_mask.sum())
        log.info("Swapped salary_min/salary_max for %d rows", n_swapped)
        min_values = enriched.loc[swap_mask, "salary_min"].copy()
        enriched.loc[swap_mask, "salary_min"] = enriched.loc[swap_mask, "salary_max"]
        enriched.loc[swap_mask, "salary_max"] = min_values

    enriched["salary_is_estimated"] = 0
    only_min_mask = enriched["salary_min"].notna() & enriched["salary_max"].isna()
    only_max_mask = enriched["salary_min"].isna() & enriched["salary_max"].notna()

    enriched.loc[only_min_mask, "salary_max"] = enriched.loc[only_min_mask, "salary_min"]
    enriched.loc[only_max_mask, "salary_min"] = enriched.loc[only_max_mask, "salary_max"]
    enriched.loc[only_min_mask | only_max_mask, "salary_is_estimated"] = 1
    n_estimated = int((only_min_mask | only_max_mask).sum())
    if n_estimated:
        log.info("Estimated missing salary bound for %d rows", n_estimated)

    enriched["salary_avg"] = enriched[["salary_min", "salary_max"]].mean(axis=1)

    invalid_salary_mask = (
        enriched["salary_avg"].notna()
        & ((enriched["salary_avg"] < 1_000_000) | (enriched["salary_avg"] > 500_000_000))
    )
    n_invalid = int(invalid_salary_mask.sum())
    if n_invalid:
        log.warning("Removed %d rows with salary_avg outside [1M, 500M] VND range", n_invalid)
    enriched.loc[invalid_salary_mask, ["salary_min", "salary_max", "salary_avg"]] = np.nan
    enriched.loc[invalid_salary_mask, "salary_is_estimated"] = 0

    return enriched


# (#5) Ưu tiên dùng level gốc, chỉ suy luận khi level gốc là NaN
def normalize_level(raw_level: object, job_title: object, experience_years: object) -> object:
    # Ưu tiên level gốc nếu đã có sẵn
    if pd.notna(raw_level):
        key = slugify_key(raw_level)
        level_keywords_map = {
            "intern": "Intern",
            "thuc tap": "Intern",
            "fresher": "Junior",
            "junior": "Junior",
            "entry level": "Junior",
            "middle": "Middle",
            "mid": "Middle",
            "senior": "Senior",
            "lead": "Lead",
            "principal": "Lead",
            "manager": "Manager",
            "head": "Manager",
            "architect": "Senior",
            "director": "Manager",
        }
        for keyword, level in level_keywords_map.items():
            if keyword in key:
                return level

    # Fallback: suy luận từ job_title
    title_text = slugify_key(job_title)

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

    # Fallback: suy luận từ experience_years
    years = float(experience_years) if pd.notna(experience_years) else np.nan
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


# (#6) Cải thiện phân loại company_type
def normalize_company_type(company_name: object) -> object:
    text = normalize_text(company_name)
    if pd.isna(text):
        return np.nan

    key = slugify_key(text)

    # Ưu tiên check danh sách công ty IT lớn đã biết
    for known in KNOWN_TECH_COMPANIES:
        if known in key:
            return "Technology"

    if any(keyword in key for keyword in ["ngan hang", "bank", "chung khoan", "bao hiem", "finance", "fintech"]):
        return "Finance"
    if any(keyword in key for keyword in ["giao duc", "education", "university", "academy", "school"]):
        return "Education"
    if any(keyword in key for keyword in ["health", "benh vien", "medical", "pharma"]):
        return "Healthcare"
    if any(keyword in key for keyword in ["solution", "software", "technology", "tech", "system", "digital",
                                           "it", "data", "cloud", "cyber", "ai"]):
        return "Technology"
    if any(keyword in key for keyword in ["logistics", "shipping", "delivery", "giao hang", "van tai"]):
        return "Logistics"
    if any(keyword in key for keyword in ["real estate", "bat dong san", "property"]):
        return "Real Estate"
    if any(keyword in key for keyword in ["game", "gaming", "entertainment", "giai tri"]):
        return "Entertainment"
    if any(keyword in key for keyword in ["ecommerce", "e commerce", "thuong mai dien tu", "san thuong mai"]):
        return "E-Commerce"
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
        source = "itviec" if "itviec" in path.stem.lower() else "topcv" if "topcv" in path.stem.lower() else "topdev" if "topdev" in path.stem.lower() else path.stem.lower()
        frame = pd.read_csv(path)
        frame["source"] = source
        log.info("Loaded %-30s  rows=%d  source=%s", path.name, len(frame), source)
        frames.append(frame)

    if not frames:
        raise ValueError("No input CSV files found to clean.")

    merged = pd.concat(frames, ignore_index=True)
    log.info("Total rows after merge: %d", len(merged))
    return merged


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    n_original = len(cleaned)

    for column in ["job_title", "company_name", "location", "remote_option", "tech_stack"]:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].apply(normalize_text)

    cleaned["location"] = cleaned["location"].apply(normalize_location)
    cleaned["remote_option"] = cleaned["remote_option"].apply(normalize_remote_option)
    cleaned["experience_years"] = cleaned["experience_years"].apply(parse_experience_years)

    cleaned = compute_salary_fields(cleaned)

    # (#5) Truyền thêm raw level nếu có
    raw_level_series = cleaned["level"] if "level" in cleaned.columns else pd.Series(np.nan, index=cleaned.index)
    cleaned["level"] = cleaned.apply(
        lambda row: normalize_level(
            raw_level_series[row.name],
            row.get("job_title"),
            row.get("experience_years"),
        ),
        axis=1,
    )
    cleaned["company_type"] = cleaned["company_name"].apply(normalize_company_type)

    cleaned["job_id"] = cleaned.apply(build_job_id, axis=1)

    n_before_dedup = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=["job_id"]).reset_index(drop=True)
    n_dropped = n_before_dedup - len(cleaned)
    if n_dropped:
        log.info("Dropped %d duplicate rows (by job_id)", n_dropped)

    ordered_columns = EXPECTED_COLUMNS + [
        "remote_option",
        "tech_stack",
        "salary_is_estimated",
        "salary_min_original",
        "salary_max_original",
    ]
    remaining_columns = [column for column in cleaned.columns if column not in ordered_columns]
    cleaned = cleaned[[column for column in ordered_columns if column in cleaned.columns] + remaining_columns]

    log.info("Cleaning done: %d → %d rows", n_original, len(cleaned))
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
    # (#11) Dùng na_rep="" thay vì "NaN" để tránh nhầm lẫn string/NaN
    cleaned.to_csv(args.output, index=False, na_rep="")

    n_salary_known = int(cleaned["salary_avg"].notna().sum())
    log.info("Saved cleaned dataset with %d rows to %s", len(cleaned), args.output)
    log.info("Rows with usable salary_avg: %d", n_salary_known)
    log.info("Rows with missing salary_avg: %d", len(cleaned) - n_salary_known)


if __name__ == "__main__":
    main()
