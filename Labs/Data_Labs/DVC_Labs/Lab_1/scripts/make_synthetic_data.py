"""Write a synthetic CC_GENERAL.csv with the real schema, for running the pipeline without the
private dataset (CI smoke test). The values are random and the results mean nothing.

Usage: python scripts/make_synthetic_data.py [--rows 500]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB_DIR / "src"))
from common import RAW_DATA, write_csv  # noqa: E402
from prepare import EXPECTED_COLUMNS, ID_COLUMN  # noqa: E402

FREQUENCY_COLUMNS = {c for c in EXPECTED_COLUMNS if c.endswith("FREQUENCY")} | {"PRC_FULL_PAYMENT"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=500)
    args = parser.parse_args()

    rng = np.random.default_rng(0)
    df = pd.DataFrame({ID_COLUMN: [f"S{i:05d}" for i in range(args.rows)]})
    for col in EXPECTED_COLUMNS:
        if col in FREQUENCY_COLUMNS:
            df[col] = rng.uniform(0, 1, args.rows)
        elif col == "TENURE":
            df[col] = rng.integers(6, 13, args.rows)
        else:
            df[col] = rng.lognormal(6, 1.5, args.rows)  # skewed, like the real money columns
    df.loc[rng.choice(args.rows, args.rows // 30, replace=False), "MINIMUM_PAYMENTS"] = np.nan

    write_csv(df, RAW_DATA)
    print(f"Wrote {args.rows} synthetic customers to {RAW_DATA.relative_to(LAB_DIR)}")


if __name__ == "__main__":
    main()
