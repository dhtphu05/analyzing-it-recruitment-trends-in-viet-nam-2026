from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.processing.utils import strip_accents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SKILL_ALIAS_MAP = {
    "c sharp": "c#",
    "c# .net": "c#",
    "dot net": ".net",
    "nodejs": "node.js",
    "node js": "node.js",
    "reactjs": "react",
    "react js": "react",
    "vuejs": "vue",
    "vue js": "vue",
    "nextjs": "next.js",
    "next js": "next.js",
    "nestjs": "nestjs",
    "nest js": "nestjs",
    "expressjs": "express",
    "express js": "express",
    "javascript": "js",
    "typescript": "ts",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "golang": "go",
    "artificial intelligence": "ai",
    "machine learning": "ml",
    "deep learning": "dl",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "ci cd": "ci/cd",
    "dev sec ops": "devsecops",
    "quality assurance": "qa",
    "business intelligence": "bi",
    "power bi": "powerbi",
    "hrm": "hr",
}

COMMON_SKILLS = {
    "python",
    "java",
    "js",
    "ts",
    "php",
    "go",
    "c++",
    "c#",
    ".net",
    "react",
    "vue",
    "angular",
    "node.js",
    "nestjs",
    "next.js",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "linux",
    "git",
    "jira",
    "figma",
    "photoshop",
    "spark",
    "hadoop",
    "kafka",
    "airflow",
    "bi",
    "powerbi",
    "tableau",
    "excel",
    "ai",
    "ml",
    "dl",
    "nlp",
    "cv",
    "qa",
    "tester",
    "automation test",
    "manual test",
    "security",
    "devops",
    "devsecops",
    "ci/cd",
    "rest api",
    "graphql",
    "firebase",
    "flutter",
    "android",
    "ios",
    "swift",
    "kotlin",
    "hcm",
    "erp",
    "sap",
}

SKILL_INDICATORS = {
    "has_python": {"python"},
    "has_java": {"java"},
    "has_js_ts": {"js", "ts", "node.js", "react", "vue", "angular", "next.js", "nestjs"},
    "has_sql": {"sql", "mysql", "postgresql", "mongodb", "redis"},
    "has_cloud": {"aws", "azure", "gcp"},
    "has_data": {"spark", "hadoop", "kafka", "airflow", "bi", "powerbi", "tableau", "excel", "ai", "ml", "dl"},
    "has_devops": {"docker", "kubernetes", "linux", "devops", "devsecops", "ci/cd"},
    "has_mobile": {"flutter", "android", "ios", "swift", "kotlin"},
    "has_testing": {"qa", "tester", "automation test", "manual test"},
}

SEPARATOR_PATTERN = re.compile(r"[,;/|]+")
TOKEN_CLEAN_PATTERN = re.compile(r"[^a-z0-9+#./\-\s]")


def normalize_token(token: str) -> str:
    token = strip_accents(token.lower())
    token = token.replace("&", " ")
    token = TOKEN_CLEAN_PATTERN.sub(" ", token)
    token = re.sub(r"\s+", " ", token).strip(" .-_")
    return SKILL_ALIAS_MAP.get(token, token)


def split_skill_candidates(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return []

    raw_parts = SEPARATOR_PATTERN.split(text)
    candidates: list[str] = []
    for part in raw_parts:
        normalized = normalize_token(part)
        if not normalized:
            continue
        if len(normalized) < 2 and normalized not in {"c#", "c++", "r"}:
            continue
        candidates.append(normalized)
    return candidates


def extract_skills_from_row(row: pd.Series) -> list[str]:
    source_columns = ["tech_stack", "job_title"]
    if "job_description" in row.index:
        source_columns.append("job_description")

    candidates: list[str] = []
    for col in source_columns:
        candidates.extend(split_skill_candidates(row.get(col, "")))

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        if candidate in COMMON_SKILLS or len(candidate.split()) <= 3:
            deduped.append(candidate)
            seen.add(candidate)

    return deduped


def enrich_with_skill_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    skill_lists = enriched.apply(extract_skills_from_row, axis=1)
    enriched["skills_extracted"] = skill_lists.apply(lambda items: ", ".join(items))
    enriched["skills_count"] = skill_lists.apply(len)

    # (#3) Sửa bug late-binding closure — dùng default argument
    for column_name, matched_skills in SKILL_INDICATORS.items():
        enriched[column_name] = skill_lists.apply(
            lambda items, ms=matched_skills: int(bool(set(items) & ms))
        )

    log.info("Extracted skills for %d rows, avg skills per row: %.1f",
             len(enriched), enriched["skills_count"].mean())

    return enriched


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract skills and create skill-based features.")
    parser.add_argument("--input", type=Path, required=True, help="Input cleaned CSV file.")
    parser.add_argument("--output", type=Path, required=True, help="Output CSV file with skill features.")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    log.info("Loaded %d rows from %s", len(df), args.input)

    enriched = enrich_with_skill_features(df)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # (#11) Dùng na_rep="" thay vì "NaN"
    enriched.to_csv(args.output, index=False, na_rep="")
    log.info("Saved skill-enriched dataset with %d rows to %s", len(enriched), args.output)


if __name__ == "__main__":
    main()
