from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


SKILL_KEYWORDS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "ReactJS",
    "Node.js",
    "SQL",
    "Docker",
    "AWS",
    "Spring Boot",
    "Django",
]


def extract_skills(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    matches = []
    for keyword in SKILL_KEYWORDS:
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        if pattern.search(text):
            matches.append(keyword)
    return sorted(set(matches))


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    source_text = (
        df.get("job_description", "").fillna("").astype(str)
        + " "
        + df.get("job_title", "").fillna("").astype(str)
    )
    df["skills_extracted"] = source_text.apply(extract_skills)
    for keyword in SKILL_KEYWORDS:
        column_name = f"skill_{keyword.lower().replace('.', '').replace(' ', '_')}"
        df[column_name] = df["skills_extracted"].apply(lambda values: int(keyword in values))
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract skills and create dummy features.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    featured = build_features(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    featured.to_csv(args.output, index=False)
    print(f"Saved feature dataset with {len(featured.columns)} columns to {args.output}")


if __name__ == "__main__":
    main()
