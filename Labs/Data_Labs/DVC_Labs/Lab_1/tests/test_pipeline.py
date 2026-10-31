import numpy as np
import pandas as pd
import pytest

import check_lock
import compare_metrics
import fetch_data
from prepare import EXPECTED_COLUMNS, ID_COLUMN, LOG_COLUMNS, build_features


@pytest.fixture
def raw():
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.uniform(0, 1000, size=(50, len(EXPECTED_COLUMNS))), columns=EXPECTED_COLUMNS)
    df.insert(0, ID_COLUMN, [f"C{i:05d}" for i in range(50)])
    df.loc[3, "MINIMUM_PAYMENTS"] = np.nan  # gaps like the real data
    df.loc[7, "CREDIT_LIMIT"] = np.nan
    return df


# ---------- prepare ----------

@pytest.mark.parametrize("scaler", ["standard", "minmax", "robust"])
def test_features_have_no_gaps_and_drop_id(raw, scaler):
    features = build_features(raw, log_transform=True, scaler=scaler)
    assert list(features.columns) == EXPECTED_COLUMNS
    assert ID_COLUMN not in features.columns
    assert len(features) == len(raw)
    assert not features.isna().any().any()


def test_standard_scaler_centres_columns(raw):
    features = build_features(raw, log_transform=False, scaler="standard")
    assert np.allclose(features.mean(), 0, atol=1e-9)
    assert np.allclose(features.std(ddof=0), 1, atol=1e-9)


def test_minmax_scaler_range(raw):
    features = build_features(raw, log_transform=False, scaler="minmax")
    assert features.min().min() == pytest.approx(0)
    assert features.max().max() == pytest.approx(1)


def test_log_transform_changes_only_log_columns(raw):
    with_log = build_features(raw, log_transform=True, scaler="minmax")
    without = build_features(raw, log_transform=False, scaler="minmax")
    other = [c for c in EXPECTED_COLUMNS if c not in LOG_COLUMNS]
    assert np.allclose(with_log[other], without[other])
    assert not np.allclose(with_log[LOG_COLUMNS], without[LOG_COLUMNS])


def test_missing_column_rejected(raw):
    with pytest.raises(ValueError, match="missing columns"):
        build_features(raw.drop(columns=["TENURE"]), True, "standard")


def test_duplicate_ids_rejected(raw):
    raw.loc[1, ID_COLUMN] = raw.loc[0, ID_COLUMN]
    with pytest.raises(ValueError, match="duplicate"):
        build_features(raw, True, "standard")


def test_unknown_scaler_rejected(raw):
    with pytest.raises(ValueError, match="Unknown scaler"):
        build_features(raw, True, "quantile")


# ---------- fetch_data ----------

CSV = b"CUST_ID,BALANCE\r\nC1,1\r\nC2,2\r\nC3,3\r\n"


def test_take_rows_keeps_header_and_bytes():
    assert fetch_data.take_rows(CSV, 2) == b"CUST_ID,BALANCE\r\nC1,1\r\nC2,2\r\n"


def test_take_rows_none_returns_everything():
    assert fetch_data.take_rows(CSV, None) == CSV


@pytest.mark.parametrize("rows", [0, 4])
def test_take_rows_out_of_range(rows):
    with pytest.raises(ValueError):
        fetch_data.take_rows(CSV, rows)


# ---------- compare_metrics ----------

def test_metrics_within_tolerance_pass():
    assert compare_metrics.compare({"silhouette": 0.2512}, {"silhouette": 0.2513}, 1e-3) == []


def test_metrics_real_change_fails():
    problems = compare_metrics.compare({"silhouette": 0.25}, {"silhouette": 0.30}, 1e-3)
    assert problems and "silhouette" in problems[0]


def test_metrics_missing_key_fails():
    assert compare_metrics.compare({"a": 1, "b": 2}, {"a": 1}, 1e-3) == ["b: present in only one file"]


# ---------- check_lock (CI: lock must match committed code/params) ----------

def test_lock_check_ignores_missing_private_data():
    status = {
        "prepare": [{"changed deps": {"data/raw/CC_GENERAL.csv": "deleted"}},
                    {"changed outs": {"data/processed/features.csv": "not in cache"}}],
        "data/raw/CC_GENERAL.csv.dvc": [{"changed outs": {"data/raw/CC_GENERAL.csv": "deleted"}}],
    }
    assert check_lock.problems_from_status(status) == []


def test_lock_check_flags_modified_code():
    status = {"train": [{"changed deps": {"src/train.py": "modified"}}]}
    assert check_lock.problems_from_status(status) == ["train: changed deps src/train.py modified"]


def test_lock_check_flags_changed_param():
    status = {"train": [{"changed deps": {"params.yaml": {"train.n_clusters": "modified"}}}]}
    assert check_lock.problems_from_status(status) == [
        "train: changed deps params.yaml:train.n_clusters modified"]


def test_lock_check_flags_changed_command():
    assert check_lock.problems_from_status({"evaluate": ["changed command"]}) == [
        "evaluate: changed command"]
