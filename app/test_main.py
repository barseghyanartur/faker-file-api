from unittest import TestCase

from fastapi.testclient import TestClient

from .main import app, PROVIDERS

__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2023 Artur Barseghyan"
__license__ = "MIT"
__all__ = ["TestApp"]

client = TestClient(app)


class TestApp(TestCase):

    def test_heartbeat_endpoint(self):
        """Test heartbeat (GET)."""
        response = client.get("/heartbeat/")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {"message": "Heartbeat"})

    def test_providers_endpoint(self):
        """Test list of providers (GET)."""
        response = client.get("/providers/")
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        for name in PROVIDERS:
            with self.subTest(f"{name}"):
                self.assertIn(f"/{name}1/", response_json)

    def test_providers(self):
        """Test all individual providers (POST)."""
        for name in PROVIDERS:
            with self.subTest(f"{name}"):
                response = client.post(f"/{name}/", json={})
                self.assertEqual(response.status_code, 200, msg=name)
