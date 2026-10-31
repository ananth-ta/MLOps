"""Stage 1: raw CC_GENERAL.csv -> cleaned, scaled feature matrix."""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from common import FEATURES, RAW_DATA, load_params, write_csv

ID_COLUMN = "CUST_ID"
EXPECTED_COLUMNS = [
    "BALANCE", "BALANCE_FREQUENCY", "PURCHASES", "ONEOFF_PURCHASES",
    "INSTALLMENTS_PURCHASES", "CASH_ADVANCE", "PURCHASES_FREQUENCY",
    "ONEOFF_PURCHASES_FREQUENCY", "PURCHASES_INSTALLMENTS_FREQUENCY",
    "CASH_ADVANCE_FREQUENCY", "CASH_ADVANCE_TRX", "PURCHASES_TRX", "CREDIT_LIMIT",
    "PAYMENTS", "MINIMUM_PAYMENTS", "PRC_FULL_PAYMENT", "TENURE",
]
# Money amounts and transaction counts: non-negative and heavily right-skewed
LOG_COLUMNS = [
    "BALANCE", "PURCHASES", "ONEOFF_PURCHASES", "INSTALLMENTS_PURCHASES",
    "CASH_ADVANCE", "CASH_ADVANCE_TRX", "PURCHASES_TRX", "CREDIT_LIMIT",
    "PAYMENTS", "MINIMUM_PAYMENTS",
]
SCALERS = {"standard": StandardScaler, "minmax": MinMaxScaler, "robust": RobustScaler}


def validate(df):
    """Fail loudly if a new data version doesn't have the expected schema."""
    missing = [c for c in [ID_COLUMN, *EXPECTED_COLUMNS] if c not in df.columns]
    if missing:
        raise ValueError(f"Raw data is missing columns: {missing}")
    if df[ID_COLUMN].duplicated().any():
        raise ValueError("Raw data has duplicate customer IDs")
    if len(df) == 0:
        raise ValueError("Raw data is empty")


def build_features(df, log_transform, scaler):
    if scaler not in SCALERS:
        raise ValueError(f"Unknown scaler '{scaler}'; choose one of {sorted(SCALERS)}")
    validate(df)
    features = df[EXPECTED_COLUMNS].astype(float)
    # Only CREDIT_LIMIT and MINIMUM_PAYMENTS have gaps in the source data; the median is
    # robust to the extreme values in these columns
    features = features.fillna(features.median())
    if log_transform:
        features[LOG_COLUMNS] = np.log1p(features[LOG_COLUMNS].clip(lower=0))
    scaled = SCALERS[scaler]().fit_transform(features)
    return pd.DataFrame(scaled, columns=EXPECTED_COLUMNS)


def main():
    params = load_params("prepare")
    raw = pd.read_csv(RAW_DATA)
    features = build_features(raw, params["log_transform"], params["scaler"])
    write_csv(features, FEATURES, float_format="%.6f")
    print(f"prepare: {len(raw)} customers, {raw.isna().sum().sum()} missing values imputed, "
          f"scaler={params['scaler']}, log_transform={params['log_transform']} -> {FEATURES.name}")


if __name__ == "__main__":
    main()
