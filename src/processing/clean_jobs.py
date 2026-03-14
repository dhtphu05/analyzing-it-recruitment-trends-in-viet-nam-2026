from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "salary_avg" not in df.columns and {"salary_min", "salary_max"}.issubset(df.columns):
        df["salary_avg"] = (df["salary_min"].fillna(0) + df["salary_max"].fillna(0)) / 2

    if "salary_avg" in df.columns:
        df["salary_avg"] = pd.to_numeric(df["salary_avg"], errors="coerce")

    if "experience_years" in df.columns:
        df["experience_years"] = pd.to_numeric(df["experience_years"], errors="coerce")

    for column in ["job_title", "company_name", "location", "level", "company_type"]:
        if column in df.columns:
            df[column] = df[column].astype(str).str.strip()

    if "job_url" in df.columns:
        df = df.drop_duplicates(subset=["job_url"])
    else:
        df = df.drop_duplicates()

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean merged recruitment dataset.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    cleaned = clean_jobs(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.output, index=False)
    print(f"Saved cleaned dataset with {len(cleaned)} rows to {args.output}")


if __name__ == "__main__":
    main()
