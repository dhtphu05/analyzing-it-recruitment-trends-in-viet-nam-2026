from __future__ import annotations

import pandas as pd


def summarize_dataset(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_by_column": df.isna().sum().to_dict(),
        "numeric_summary": df.describe(include="number").to_dict(),
    }
