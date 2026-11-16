from datetime import datetime, timezone

import joblib
import sklearn
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

from data import load_data, split_data
from predict import DEFAULT_MODEL_PATH

# Bump when the model or its training changes; the API reports it with every prediction
MODEL_VERSION = "1.1.0"


def fit_model(X_train, y_train):
    """
    Train a Decision Tree Classifier.
    Args:
        X_train (numpy.ndarray): Training features.
        y_train (numpy.ndarray): Training target values.
    Returns:
        DecisionTreeClassifier: The fitted model.
    """
    return DecisionTreeClassifier(max_depth=3, random_state=12).fit(X_train, y_train)


def save_bundle(model, feature_names, class_names, test_accuracy, path=DEFAULT_MODEL_PATH):
    """
    Save the model together with the metadata the API needs, as one file, so the
    model and its feature order / class names can never get out of sync.
    """
    bundle = {
        "model": model,
        "feature_names": feature_names,
        "class_names": class_names,
        "version": MODEL_VERSION,
        "test_accuracy": round(float(test_accuracy), 4),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    return bundle


if __name__ == "__main__":
    X, y, feature_names, class_names = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)
    model = fit_model(X_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(X_test))
    save_bundle(model, feature_names, class_names, accuracy)
    print(f"Trained DecisionTree v{MODEL_VERSION}: test accuracy {accuracy:.4f} "
          f"on {len(X_test)} held-out flowers -> {DEFAULT_MODEL_PATH.name}")
