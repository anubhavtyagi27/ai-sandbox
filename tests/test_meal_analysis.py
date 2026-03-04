import json
import unittest
from unittest.mock import MagicMock, patch

from app.services.meal_analysis import (
    MealAnalysisAPIError,
    MealAnalysisParseError,
    MealAnalysisService,
)


def _make_client(return_value=None, side_effect=None):
    """Return a mock GeminiClient."""
    client = MagicMock()
    if side_effect:
        client.create_response.side_effect = side_effect
    else:
        client.create_response.return_value = return_value or {}
    # Wire _provider.parse_response to the real GeminiProvider implementation
    from app.providers.gemini import GeminiProvider

    real = GeminiProvider.__new__(GeminiProvider)
    client._provider.parse_response.side_effect = real.parse_response
    return client


def _gemini_response(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


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


class TestMealAnalysisService(unittest.TestCase):
    def setUp(self):
        self.service = MealAnalysisService()

    def test_analyse_meal_from_text_success(self):
        raw = _gemini_response(json.dumps(_success_payload()))
        client = _make_client(return_value=raw)

        with patch.object(self.service, "_get_client", return_value=client):
            result = self.service.analyse_meal_from_text("2 rotis with dal makhani")

        self.assertTrue(result["success"])
        self.assertEqual(result["meal_name"], "Dal Makhani with 2 Rotis")

    def test_analyse_meal_from_image_success(self):
        raw = _gemini_response(json.dumps(_success_payload()))
        client = _make_client(return_value=raw)

        with patch.object(self.service, "_get_client", return_value=client):
            result = self.service.analyse_meal_from_image("abc123", "image/jpeg")

        self.assertTrue(result["success"])
        self.assertIn("identified_items", result)

    def test_retry_on_invalid_json_then_success(self):
        first = _gemini_response("not-json")
        second = _gemini_response(json.dumps(_success_payload()))
        client = _make_client(side_effect=[first, second])

        with patch.object(self.service, "_get_client", return_value=client):
            result = self.service.analyse_meal_from_text(
                "aaj lunch mein dal chawal khaya"
            )

        self.assertTrue(result["success"])
        self.assertEqual(client.create_response.call_count, 2)

    def test_fail_when_retry_also_invalid(self):
        invalid = _gemini_response("not-json")
        client = _make_client(side_effect=[invalid, invalid])

        with patch.object(self.service, "_get_client", return_value=client):
            with self.assertRaises(MealAnalysisParseError):
                self.service.analyse_meal_from_text("anything")

    def test_api_error_raises_meal_analysis_api_error(self):
        from app.services.gemini_client import GeminiClientError

        client = _make_client(side_effect=GeminiClientError("rate limit"))

        with patch.object(self.service, "_get_client", return_value=client):
            with self.assertRaises(MealAnalysisAPIError):
                self.service.analyse_meal_from_text("anything")

    def test_non_food_failure_shape_passes(self):
        failure = {
            "success": False,
            "error": "Could not identify food items in the provided input.",
        }
        raw = _gemini_response(json.dumps(failure))
        client = _make_client(return_value=raw)

        with patch.object(self.service, "_get_client", return_value=client):
            result = self.service.analyse_meal_from_text("random words not food")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_instructions_passed_as_system_prompt(self):
        raw = _gemini_response(json.dumps(_success_payload()))
        client = _make_client(return_value=raw)

        with patch.object(self.service, "_get_client", return_value=client):
            self.service.analyse_meal_from_text("dal rice")

        call_params = client.create_response.call_args[0][0]
        self.assertIn("instructions", call_params)
        self.assertIn("nutrition expert", call_params["instructions"])


if __name__ == "__main__":
    unittest.main()
