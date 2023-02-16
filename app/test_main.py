from fastapi.testclient import TestClient

from .main import app, PROVIDERS

__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2023 Artur Barseghyan"
__license__ = "MIT"
__all__ = [
    "test_heartbeat_endpoint",
    "test_providers_endpoint",
    "test_providers",
]

client = TestClient(app)


def test_heartbeat_endpoint():
    """Test heartbeat (GET)."""
    response = client.get("/heartbeat/")
    assert response.status_code == 200
    assert response.json() == {"message": "Heartbeat"}


def test_providers_endpoint():
    """Test list of providers (GET)."""
    response = client.get("/providers/")
    assert response.status_code == 200
    response_json = response.json()
    for name in PROVIDERS:
        assert f"/{name}/" in response_json


def test_providers():
    """Test all individual providers (POST)."""
    for name in PROVIDERS:
        response = client.post(f"/{name}/", json={})
        assert response.status_code == 200, name
