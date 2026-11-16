import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from predict import DEFAULT_MODEL_PATH, load_bundle, predict_data

logger = logging.getLogger("uvicorn.error")
MAX_BATCH_SIZE = 100


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model ONCE at startup (the original reloaded it from disk on every request)."""
    path = os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH)
    try:
        app.state.bundle = load_bundle(path)
        logger.info("Loaded model v%s from %s", app.state.bundle["version"], path)
    except (FileNotFoundError, ValueError) as e:
        # Keep serving so /health can report the problem; prediction endpoints return 503
        app.state.bundle = None
        logger.error("Model not loaded: %s", e)
    yield


app = FastAPI(
    title="Iris Species Classifier",
    description="Predicts the iris species from flower measurements (cm).",
    version="1.1.0",
    lifespan=lifespan,
)


# ---------- Request / response schemas ----------

class IrisFeatures(BaseModel):
    """
    Measurements of one iris flower, in centimetres. Bounds reject impossible values
    (zero/negative sizes, or several times larger than any iris) with a 422 error,
    instead of silently returning a meaningless prediction.
    """
    model_config = ConfigDict(
        extra="forbid",  # a misspelt field name is an error, not silently ignored
        json_schema_extra={"examples": [
            {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}]},
    )
    sepal_length: float = Field(gt=0, le=15, description="Sepal length in cm")
    sepal_width: float = Field(gt=0, le=10, description="Sepal width in cm")
    petal_length: float = Field(gt=0, le=15, description="Petal length in cm")
    petal_width: float = Field(gt=0, le=5, description="Petal width in cm")


class IrisBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[IrisFeatures] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


class Prediction(BaseModel):
    class_id: int
    species: str
    probabilities: dict[str, float]


class PredictionResponse(Prediction):
    model_version: str


class BatchResponse(BaseModel):
    count: int
    model_version: str
    predictions: list[Prediction]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ModelInfo(BaseModel):
    version: str
    algorithm: str
    feature_names: list[str]
    class_names: list[str]
    test_accuracy: float | None = None
    trained_at: str | None = None
    sklearn_version: str | None = None


# ---------- Helpers ----------

def get_bundle(request: Request):
    bundle = request.app.state.bundle
    if bundle is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Model is not loaded; train it with `python src/train.py` and restart")
    return bundle


def to_rows(bundle, items):
    # Build each row in the order the model was trained on, by name, never by field position
    return [[getattr(item, name) for name in bundle["feature_names"]] for item in items]


# ---------- Endpoints ----------
# Plain `def` (not `async def`): the model call is CPU-bound and blocking, so FastAPI runs it in
# a worker thread instead of blocking the event loop that serves every other request.

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Iris classifier API. See /docs for the interactive documentation."}


@app.get("/health", response_model=HealthResponse)
def health(request: Request):
    """Liveness check that also reports whether the model is ready."""
    loaded = request.app.state.bundle is not None
    return HealthResponse(status="ok" if loaded else "degraded", model_loaded=loaded)


@app.get("/model-info", response_model=ModelInfo)
def model_info(request: Request):
    """Which model is serving: version, features, classes and its held-out accuracy."""
    bundle = get_bundle(request)
    return ModelInfo(
        algorithm=type(bundle["model"]).__name__,
        **{k: bundle.get(k) for k in ("version", "feature_names", "class_names",
                                      "test_accuracy", "trained_at", "sklearn_version")},
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(features: IrisFeatures, request: Request):
    """Predict the species of one flower, with the probability of each species."""
    bundle = get_bundle(request)
    result = predict_data(bundle, to_rows(bundle, [features]))[0]
    return PredictionResponse(**result, model_version=bundle["version"])


@app.post("/predict/batch", response_model=BatchResponse)
def predict_batch(batch: IrisBatch, request: Request):
    """Predict up to 100 flowers in one request (one model call for the whole batch)."""
    bundle = get_bundle(request)
    results = predict_data(bundle, to_rows(bundle, batch.items))
    return BatchResponse(count=len(results), model_version=bundle["version"], predictions=results)
