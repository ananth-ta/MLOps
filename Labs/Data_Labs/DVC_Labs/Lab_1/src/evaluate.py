"""Stage 3: score the clustering and produce the metrics and plot data DVC tracks."""
import joblib
import pandas as pd
import yaml
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score

from common import CLUSTER_SIZES, ELBOW, FEATURES, METRICS, MODEL, load_params, write_csv


def main():
    eval_params = load_params("evaluate")
    train_params = load_params("train")
    features = pd.read_csv(FEATURES)
    model = joblib.load(MODEL)
    labels = model.predict(features)

    # Rounded so that tiny floating-point differences between machines don't show up as changes
    metrics = {
        "n_customers": int(len(features)),
        "n_clusters": int(model.n_clusters),
        "inertia": round(float(model.inertia_), 2),
        # Higher is better (max 1): how well each customer fits its own cluster vs the nearest other
        "silhouette": round(float(silhouette_score(features, labels)), 4),
        # Lower is better: average similarity between each cluster and its most similar one
        "davies_bouldin": round(float(davies_bouldin_score(features, labels)), 4),
    }
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS, "w", newline="\n") as f:
        yaml.safe_dump(metrics, f, sort_keys=False)

    sizes = pd.Series(labels).value_counts().sort_index()
    write_csv(pd.DataFrame({"cluster": sizes.index, "customers": sizes.values}), CLUSTER_SIZES)

    # Elbow curve: inertia for a range of k, to judge whether n_clusters is a sensible choice
    elbow = [
        {
            "k": k,
            "inertia": round(float(KMeans(n_clusters=k, n_init=train_params["n_init"],
                                          random_state=train_params["random_state"])
                                   .fit(features).inertia_), 2),
        }
        for k in range(eval_params["elbow_k_min"], eval_params["elbow_k_max"] + 1)
    ]
    write_csv(pd.DataFrame(elbow), ELBOW)

    print("evaluate: " + ", ".join(f"{k}={v}" for k, v in metrics.items()))


if __name__ == "__main__":
    main()
