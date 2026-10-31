"""Stage 2: fit KMeans on the feature matrix."""
import joblib
import pandas as pd
from sklearn.cluster import KMeans

from common import FEATURES, MODEL, load_params


def main():
    params = load_params("train")
    features = pd.read_csv(FEATURES)
    model = KMeans(
        n_clusters=params["n_clusters"],
        n_init=params["n_init"],
        random_state=params["random_state"],
    ).fit(features)
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL)
    print(f"train: KMeans k={params['n_clusters']} on {len(features)} customers, "
          f"inertia={model.inertia_:.1f} -> {MODEL.name}")


if __name__ == "__main__":
    main()
