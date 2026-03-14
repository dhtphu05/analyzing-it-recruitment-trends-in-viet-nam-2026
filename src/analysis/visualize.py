from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_salary_distribution(df: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 5))
    sns.histplot(df["salary_avg"].dropna(), bins=30, kde=True)
    plt.title("Salary Distribution")
    plt.xlabel("Salary Average")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
