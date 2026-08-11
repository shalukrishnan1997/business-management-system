from django.test import SimpleTestCase
from rest_framework.test import APIClient


class HealthCheckTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        client = APIClient()
        response = client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["service"], "bms-api")
