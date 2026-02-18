import unittest
import json
from unittest.mock import Mock, patch

from app.services.gemini_service import (
    GeminiAPIError,
    GeminiMealAnalysisService,
    GeminiResponseParseError,
)


class TestGeminiMealAnalysisService(unittest.TestCase):
    def setUp(self):
        self.service = GeminiMealAnalysisService()

    @staticmethod
    def _success_payload():
        return {
            "success": True,
            "meal_name": "Dal Makhani with 2 Rotis",
            "identified_items": [
                {
                    "name": "Dal Makhani",
                    "quantity": "1 bowl (approx 200g)",
                    "calories": 310,
                    "protein_g": 12,
                    "carbs_g": 35,
                    "fat_g": 11,
                    "fibre_g": 6,
                }
            ],
            "totals": {
                "calories": 310,
                "protein_g": 12,
                "carbs_g": 35,
                "fat_g": 11,
                "fibre_g": 6,
            },
            "confidence": "high",
            "notes": "Estimated from common serving size.",
        }

    def test_analyse_meal_from_text_success(self):
        model_json = self._success_payload()
        gemini_response = {
            "candidates": [{"content": {"parts": [{"text": json.dumps(model_json)}]}}]
        }

        with patch.object(self.service, "_get_api_key", return_value="dummy"), patch.object(
            self.service, "_call_gemini", return_value=gemini_response
        ):
            result = self.service.analyse_meal_from_text("2 rotis with dal makhani")

        self.assertTrue(result["success"])
        self.assertEqual(result["meal_name"], "Dal Makhani with 2 Rotis")

    def test_analyse_meal_from_image_success(self):
        model_json = self._success_payload()
        gemini_response = {
            "candidates": [{"content": {"parts": [{"text": json.dumps(model_json)}]}}]
        }

        with patch.object(self.service, "_get_api_key", return_value="dummy"), patch.object(
            self.service, "_call_gemini", return_value=gemini_response
        ):
            result = self.service.analyse_meal_from_image("abc123", "image/jpeg")

        self.assertTrue(result["success"])
        self.assertIn("identified_items", result)

    def test_retry_on_invalid_json_then_success(self):
        first = {"candidates": [{"content": {"parts": [{"text": "not-json"}]}}]}
        second = {
            "candidates": [
                {"content": {"parts": [{"text": json.dumps(self._success_payload())}]}}
            ]
        }

        with patch.object(self.service, "_get_api_key", return_value="dummy"), patch.object(
            self.service, "_call_gemini", side_effect=[first, second]
        ) as mock_call:
            result = self.service.analyse_meal_from_text("aaj lunch mein dal chawal khaya")

        self.assertTrue(result["success"])
        self.assertEqual(mock_call.call_count, 2)

    def test_fail_when_retry_also_invalid(self):
        invalid = {"candidates": [{"content": {"parts": [{"text": "not-json"}]}}]}

        with patch.object(self.service, "_get_api_key", return_value="dummy"), patch.object(
            self.service, "_call_gemini", side_effect=[invalid, invalid]
        ):
            with self.assertRaises(GeminiResponseParseError):
                self.service.analyse_meal_from_text("anything")

    def test_api_error_status_raises(self):
        with patch.object(self.service, "_get_api_key", return_value="dummy"):
            response = Mock()
            response.status_code = 429
            response.text = "rate limit"
            self.service.session.post = Mock(return_value=response)

            with self.assertRaises(GeminiAPIError):
                self.service._call_gemini({"contents": []}, "dummy")

    def test_non_food_failure_shape_passes(self):
        model_json = {
            "success": False,
            "error": "Could not identify food items in the provided input.",
        }
        gemini_response = {
            "candidates": [{"content": {"parts": [{"text": json.dumps(model_json)}]}}]
        }

        with patch.object(self.service, "_get_api_key", return_value="dummy"), patch.object(
            self.service, "_call_gemini", return_value=gemini_response
        ):
            result = self.service.analyse_meal_from_text("random words not food")

        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
