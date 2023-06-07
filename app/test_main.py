from unittest import TestCase

from faker_file.providers.webp_file import WebpFileProvider
from fastapi.testclient import TestClient

from .main import PROVIDERS, app

__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2023 Artur Barseghyan"
__license__ = "MIT"
__all__ = ["TestApp"]

client = TestClient(app)

TEST_PAYLOADS = {
    "generic_file": {
        "content": "{{text}}",
        "extension": "html",
    }
}

IGNORE_PROVIDERS = {
    WebpFileProvider.webp_file.__name__,
}

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
                self.assertIn(f"/{name}/", response_json)

    def test_providers(self):
        """Test all individual providers (POST)."""
        for name in PROVIDERS:
            if not name in IGNORE_PROVIDERS:
                with self.subTest(f"{name}"):
                    response = client.post(
                        f"/{name}/", json=TEST_PAYLOADS.get(name, {})
                    )
                    self.assertEqual(response.status_code, 200, msg=name)
