import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app as app_module


@pytest.fixture
def client():
    return app_module.app.test_client()


def test_root_returns_greeting_and_version(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["message"] == "Hello, World!"
    assert body["version"] == "dev"
    assert body["revision"] == "local"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_env_vars_override_defaults(monkeypatch):
    # Mirrors what Cloud Run does: deploy.sh sets APP_VERSION/GREETING, Cloud Run sets K_REVISION
    monkeypatch.setenv("APP_VERSION", "v2")
    monkeypatch.setenv("GREETING", "Hello from v2!")
    monkeypatch.setenv("K_REVISION", "hello-cloud-run-v2")
    reloaded = importlib.reload(app_module)
    body = reloaded.app.test_client().get("/").get_json()
    assert body == {"message": "Hello from v2!", "version": "v2", "revision": "hello-cloud-run-v2"}
    monkeypatch.undo()
    importlib.reload(app_module)


def test_unknown_route_404(client):
    assert client.get("/does-not-exist").status_code == 404
