from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def load_json_files(input_dir: Path) -> pd.DataFrame:
    frames = []
    for file_path in sorted(input_dir.glob("*.json")):
        records = json.loads(file_path.read_text())
        frames.append(pd.DataFrame(records))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge raw JSON job files into one CSV.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    df = load_json_files(args.input_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Merged {len(df)} rows into {args.output}")


if __name__ == "__main__":
    main()
