"""Download CC_GENERAL.csv from Kaggle and write it (or an earlier snapshot of it) to data/raw/.

The dataset is a single 8,950-customer export. To demonstrate data versioning, `--rows N` writes
only the first N customers, simulating an earlier export before more customers were added.

Usage:
    python scripts/fetch_data.py               # full dataset (version v2)
    python scripts/fetch_data.py --rows 4500   # first 4,500 customers (version v1)

Needs a Kaggle API token (see README): the token string saved in ~/.kaggle/access_token, or in the
KAGGLE_API_TOKEN environment variable (older kaggle.json credentials also work).
The dataset is CC0 (public domain).
"""
import argparse
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent.parent
RAW_DATA = LAB_DIR / "data" / "raw" / "CC_GENERAL.csv"
KAGGLE_DATASET = "arjunbhasin2013/ccdata"


def take_rows(source_bytes, rows):
    """Header plus the first `rows` data lines, copied byte-for-byte (no re-formatting)."""
    lines = source_bytes.splitlines(keepends=True)
    if rows is None:
        return source_bytes
    if rows < 1 or rows > len(lines) - 1:
        raise ValueError(f"--rows must be between 1 and {len(lines) - 1}")
    return b"".join(lines[: rows + 1])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rows", type=int, help="only keep the first N customers")
    args = parser.parse_args()

    import kagglehub  # imported here so --help works without credentials

    download_dir = Path(kagglehub.dataset_download(KAGGLE_DATASET))
    csvs = sorted(download_dir.glob("*.csv"))
    if len(csvs) != 1:
        sys.exit(f"Expected one CSV in {download_dir}, found: {[c.name for c in csvs]}")

    data = take_rows(csvs[0].read_bytes(), args.rows)
    RAW_DATA.parent.mkdir(parents=True, exist_ok=True)
    RAW_DATA.write_bytes(data)
    n_customers = len(data.splitlines()) - 1
    print(f"Wrote {n_customers} customers to {RAW_DATA.relative_to(LAB_DIR)}")


if __name__ == "__main__":
    main()
