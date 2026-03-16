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
    "artificial intelligence": "ai",
    "machine learning": "ml",
    "deep learning": "dl",
    "computer vision": "cv",
    "large language model": "llm",
    "large language models": "llm",
    "generative ai": "genai",
    "retrieval augmented generation": "rag",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "c sharp": "c#",
    "c# .net": "c#",
    "asp net": ".net",
    "asp.net": ".net",
    "dot net": ".net",
    "dotnet": ".net",
    "java script": "js",
    "nodejs": "node.js",
    "node js": "node.js",
    "node": "node.js",
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
    "ci cd": "ci/cd",
    "ci/cd": "ci/cd",
    "dev sec ops": "devsecops",
    "quality assurance": "qa",
    "business intelligence": "bi",
    "power bi": "powerbi",
    "micro services": "microservices",
    "micro-service": "microservices",
    "micro service": "microservices",
    "react native js": "react native",
    "hrm": "hr",
}

SKILL_VOCABULARY = {
    "python",
    "r",
    "java",
    "js",
    "ts",
    "php",
    "go",
    "c++",
    "c#",
    ".net",
    "spring",
    "spring boot",
    "django",
    "flask",
    "fastapi",
    "laravel",
    "ruby",
    "rails",
    "scala",
    "rust",
    "matlab",
    "react",
    "react native",
    "vue",
    "angular",
    "node.js",
    "express",
    "nestjs",
    "next.js",
    "sql",
    "mysql",
    "postgresql",
    "oracle",
    "sql server",
    "mongodb",
    "redis",
    "elasticsearch",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "ansible",
    "jenkins",
    "gitlab",
    "github actions",
    "linux",
    "git",
    "jira",
    "figma",
    "photoshop",
    "sap",
    "odoo",
    "erp",
    "crm",
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
    "llm",
    "genai",
    "rag",
    "cv",
    "qa",
    "tester",
    "automation test",
    "manual test",
    "security",
    "penetration testing",
    "pentest",
    "devops",
    "devsecops",
    "ci/cd",
    "microservices",
    "rest api",
    "graphql",
    "firebase",
    "flutter",
    "android",
    "ios",
    "swift",
    "kotlin",
}

SKILL_PATTERNS = {
    skill: re.compile(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])")
    for skill in sorted(SKILL_VOCABULARY, key=len, reverse=True)
}

NON_SKILL_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\bnghi\b",
        r"\bthu\s*7\b",
        r"\bt7\b",
        r"\bfull[\s-]?time\b",
        r"\bpart[\s-]?time\b",
        r"\bremote\b",
        r"\bhybrid\b",
        r"\bonsite\b",
        r"\bon[\s-]?site\b",
        r"\bluong\b",
        r"\bthu nhap\b",
        r"\bco muc\b",
        r"\bjunior\b",
        r"\bsenior\b",
        r"\bfresher\b",
        r"\bintern\b",
        r"\blead\b",
        r"\bmanager\b",
        r"\benglish\b",
        r"\bjapanese\b",
    ]
]

SKILL_INDICATORS = {
    "has_ai": {"ai", "ml", "dl", "nlp", "llm", "genai", "rag", "cv"},
    "has_python": {"python"},
    "has_java": {"java"},
    "has_js_ts": {"js", "ts", "node.js", "react", "react native", "vue", "angular", "next.js", "nestjs", "express"},
    "has_sql": {"sql", "mysql", "postgresql", "mongodb", "redis", "oracle", "sql server"},
    "has_cloud": {"aws", "azure", "gcp", "terraform", "ansible"},
    "has_data": {"spark", "hadoop", "kafka", "airflow", "bi", "powerbi", "tableau", "excel", "ai", "ml", "dl", "rag", "cv"},
    "has_devops": {"docker", "kubernetes", "linux", "devops", "devsecops", "ci/cd", "jenkins", "gitlab", "github actions"},
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


def build_search_text(row: pd.Series) -> str:
    values = [str(row.get("tech_stack", "")), str(row.get("job_title", ""))]
    if "job_description" in row.index:
        values.append(str(row.get("job_description", "")))
    combined = " | ".join(values).lower()
    combined = strip_accents(combined)
    combined = TOKEN_CLEAN_PATTERN.sub(" ", combined)
    combined = re.sub(r"\s+", " ", combined)
    return f" {combined.strip()} "


def extract_skills_from_row(row: pd.Series) -> list[str]:
    search_text = build_search_text(row)
    matched: list[str] = []

    for skill, pattern in SKILL_PATTERNS.items():
        if pattern.search(search_text):
            matched.append(skill)

    for raw_value in [row.get("tech_stack", ""), row.get("job_title", ""), row.get("job_description", "")]:
        for candidate in split_skill_candidates(str(raw_value)):
            if candidate in SKILL_VOCABULARY:
                matched.append(candidate)

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in matched:
        if candidate in seen:
            continue
        if any(pattern.search(candidate) for pattern in NON_SKILL_PATTERNS):
            continue
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
