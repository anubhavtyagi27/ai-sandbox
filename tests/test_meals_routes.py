import unittest
from unittest.mock import patch

from flask import Flask

from app.routes_meals import bp
from app.services.gemini_service import GeminiServiceError


class TestMealsRoutes(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(bp)
        self.client = app.test_client()

    def test_missing_description_returns_400(self):
        response = self.client.post("/api/meals/analyse/text", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.get_json()["error"])

    def test_missing_image_returns_400(self):
        response = self.client.post(
            "/api/meals/analyse/image", json={"mimeType": "image/jpeg"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("image", response.get_json()["error"])

    def test_missing_mime_type_returns_400(self):
        response = self.client.post(
            "/api/meals/analyse/image", json={"image": "abc"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("mimeType", response.get_json()["error"])

    def test_unsupported_mime_type_returns_400(self):
        response = self.client.post(
            "/api/meals/analyse/image",
            json={"image": "abc", "mimeType": "image/gif"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("image/jpeg", response.get_json()["error"])

    @patch("app.routes_meals.analyse_meal_from_text")
    def test_valid_text_returns_200(self, mock_analyse):
        mock_analyse.return_value = {"success": True, "meal_name": "Chole Bhature"}
        response = self.client.post(
            "/api/meals/analyse/text",
            json={"description": "aaj lunch mein chole bhature khaye the"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch("app.routes_meals.analyse_meal_from_image")
    def test_valid_image_returns_200(self, mock_analyse):
        mock_analyse.return_value = {"success": True, "meal_name": "Paneer Tikka"}
        response = self.client.post(
            "/api/meals/analyse/image",
            json={"image": "abc", "mimeType": "image/jpeg"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch("app.routes_meals.analyse_meal_from_text")
    def test_service_error_returns_500(self, mock_analyse):
        mock_analyse.side_effect = GeminiServiceError("boom")
        response = self.client.post(
            "/api/meals/analyse/text", json={"description": "2 rotis with dal"}
        )
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
