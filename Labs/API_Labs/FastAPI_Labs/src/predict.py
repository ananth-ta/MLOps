from pathlib import Path

import joblib
import numpy as np

# Resolved from this file, so it works no matter which directory the server starts in
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "iris_model.pkl"
REQUIRED_KEYS = {"model", "feature_names", "class_names", "version"}


def load_bundle(path=DEFAULT_MODEL_PATH):
    """
    Load the model bundle written by train.py.
    Raises:
        FileNotFoundError: If there is no model file (run `python src/train.py`).
        ValueError: If the file is not a model bundle (e.g. an old bare model).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No model at {path}; train one with `python src/train.py`")
    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or not REQUIRED_KEYS <= bundle.keys():
        raise ValueError(f"{path} is not a model bundle with keys {sorted(REQUIRED_KEYS)}")
    return bundle


def predict_data(bundle, rows):
    """
    Predict species for one or more flowers.
    Args:
        bundle (dict): Loaded model bundle.
        rows (list[list[float]]): Feature rows, in bundle["feature_names"] order.
    Returns:
        list[dict]: For each row: class_id, species and per-species probabilities.
    """
    X = np.asarray(rows, dtype=float)
    model, class_names = bundle["model"], bundle["class_names"]
    class_ids = model.predict(X)
    probabilities = model.predict_proba(X)
    return [
        {
            "class_id": int(class_id),
            "species": class_names[int(class_id)],
            "probabilities": {name: round(float(p), 4) for name, p in zip(class_names, probs)},
        }
        for class_id, probs in zip(class_ids, probabilities)
    ]
