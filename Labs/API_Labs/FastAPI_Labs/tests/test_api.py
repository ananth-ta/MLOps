import joblib
import pytest
from fastapi.testclient import TestClient

from main import MAX_BATCH_SIZE, app

SETOSA = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
VERSICOLOR = {"sepal_length": 6.0, "sepal_width": 2.9, "petal_length": 4.5, "petal_width": 1.5}
VIRGINICA = {"sepal_length": 6.9, "sepal_width": 3.1, "petal_length": 5.8, "petal_width": 2.3}


@pytest.fixture
def client():
    # The context manager runs the app's startup (lifespan), which loads the model
    with TestClient(app) as c:
        yield c


# ---------- health and metadata ----------

def test_health_reports_model_loaded(client):
    assert client.get("/health").json() == {"status": "ok", "model_loaded": True}


def test_model_info(client):
    info = client.get("/model-info").json()
    assert info["algorithm"] == "DecisionTreeClassifier"
    assert info["class_names"] == ["setosa", "versicolor", "virginica"]
    assert info["feature_names"] == ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    assert info["test_accuracy"] >= 0.9


# ---------- single prediction ----------

@pytest.mark.parametrize("flower, species", [
    (SETOSA, "setosa"), (VERSICOLOR, "versicolor"), (VIRGINICA, "virginica")])
def test_predict_species(client, flower, species):
    body = client.post("/predict", json=flower).json()
    assert body["species"] == species
    assert body["class_id"] == ["setosa", "versicolor", "virginica"].index(species)
    assert set(body["probabilities"]) == {"setosa", "versicolor", "virginica"}
    assert sum(body["probabilities"].values()) == pytest.approx(1.0, abs=1e-3)
    assert body["probabilities"][species] == max(body["probabilities"].values())
    assert body["model_version"]


def test_field_order_in_json_does_not_matter(client):
    reordered = {k: SETOSA[k] for k in reversed(list(SETOSA))}
    assert client.post("/predict", json=reordered).json()["species"] == "setosa"


# ---------- input validation (422) ----------

@pytest.mark.parametrize("field, value", [
    ("petal_length", -1.0),      # negative size
    ("sepal_width", 0),          # zero size
    ("petal_width", 50),         # far larger than any iris
    ("sepal_length", "five"),    # not a number
])
def test_invalid_values_rejected(client, field, value):
    resp = client.post("/predict", json={**SETOSA, field: value})
    assert resp.status_code == 422
    assert resp.json()["detail"][0]["loc"][-1] == field


def test_missing_field_rejected(client):
    flower = dict(SETOSA)
    del flower["petal_width"]
    assert client.post("/predict", json=flower).status_code == 422


def test_unknown_field_rejected(client):
    # e.g. a typo: without extra="forbid" this would be silently ignored
    assert client.post("/predict", json={**SETOSA, "petal_lenght": 1.4}).status_code == 422


# ---------- batch ----------

def test_batch_predicts_each_item_in_order(client):
    body = client.post("/predict/batch", json={"items": [SETOSA, VERSICOLOR, VIRGINICA]}).json()
    assert body["count"] == 3
    assert [p["species"] for p in body["predictions"]] == ["setosa", "versicolor", "virginica"]


def test_batch_matches_single_predictions(client):
    batch = client.post("/predict/batch", json={"items": [VERSICOLOR]}).json()["predictions"][0]
    single = client.post("/predict", json=VERSICOLOR).json()
    assert batch["probabilities"] == single["probabilities"]


@pytest.mark.parametrize("n", [0, MAX_BATCH_SIZE + 1])
def test_batch_size_limits(client, n):
    assert client.post("/predict/batch", json={"items": [SETOSA] * n}).status_code == 422


def test_batch_one_bad_item_rejects_request(client):
    resp = client.post("/predict/batch", json={"items": [SETOSA, {**SETOSA, "petal_length": -2}]})
    assert resp.status_code == 422
    assert resp.json()["detail"][0]["loc"][:3] == ["body", "items", 1]


# ---------- no model ----------

def test_missing_model_returns_503(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing.pkl"))
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "degraded", "model_loaded": False}
        resp = c.post("/predict", json=SETOSA)
        assert resp.status_code == 503
        assert "train" in resp.json()["detail"]
        assert c.get("/model-info").status_code == 503


def test_old_bare_model_file_is_rejected(monkeypatch, tmp_path):
    # The original lab saved a bare model with no metadata; it must not be served
    from sklearn.tree import DecisionTreeClassifier
    path = tmp_path / "bare.pkl"
    joblib.dump(DecisionTreeClassifier(), path)
    monkeypatch.setenv("MODEL_PATH", str(path))
    with TestClient(app) as c:
        assert c.post("/predict", json=SETOSA).status_code == 503
