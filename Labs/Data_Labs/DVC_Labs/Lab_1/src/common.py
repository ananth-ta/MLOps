"""Paths and helpers shared by the pipeline stages."""
from pathlib import Path

import yaml

LAB_DIR = Path(__file__).resolve().parent.parent

RAW_DATA = LAB_DIR / "data" / "raw" / "CC_GENERAL.csv"
FEATURES = LAB_DIR / "data" / "processed" / "features.csv"
MODEL = LAB_DIR / "models" / "kmeans.pkl"
METRICS = LAB_DIR / "metrics" / "metrics.yaml"
ELBOW = LAB_DIR / "metrics" / "elbow.csv"
CLUSTER_SIZES = LAB_DIR / "metrics" / "cluster_sizes.csv"


def load_params(section):
    with open(LAB_DIR / "params.yaml") as f:
        return yaml.safe_load(f)[section]


def write_csv(df, path, **kwargs):
    # Fixed "\n" line endings and float format, so the same data produces the same bytes
    # (and therefore the same DVC hash) on Windows and Linux
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n", **kwargs)
