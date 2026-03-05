import json
import unittest
from unittest.mock import MagicMock, patch

from app.services.meal_analysis import (
    MealAnalysisAPIError,
    MealAnalysisParseError,
    MealAnalysisService,
)


def _make_provider(return_value=None, side_effect=None):
    """Return a mock BaseProvider with parse_response wired to GeminiProvider."""
    provider = MagicMock()
    if side_effect:
        provider.create_response.side_effect = side_effect
    else:
        provider.create_response.return_value = return_value or {}
    from app.providers.gemini import GeminiProvider

    real = GeminiProvider.__new__(GeminiProvider)
    provider.parse_response.side_effect = real.parse_response
    return provider


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
        provider = _make_provider(return_value=raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_text("2 rotis with dal makhani")

        self.assertTrue(result["success"])
        self.assertEqual(result["meal_name"], "Dal Makhani with 2 Rotis")

    def test_analyse_meal_from_image_success(self):
        raw = _gemini_response(json.dumps(_success_payload()))
        provider = _make_provider(return_value=raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_image("abc123", "image/jpeg")

        self.assertTrue(result["success"])
        self.assertIn("identified_items", result)

    def test_analyse_meal_from_image_passes_base64_params(self):
        raw = _gemini_response(json.dumps(_success_payload()))
        provider = _make_provider(return_value=raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            self.service.analyse_meal_from_image("abc123", "image/png")

        call_params = provider.create_response.call_args[0][0]
        self.assertEqual(call_params["base64_image"], "abc123")
        self.assertEqual(call_params["mime_type"], "image/png")

    def test_retry_on_invalid_json_then_success(self):
        first = _gemini_response("not-json")
        second = _gemini_response(json.dumps(_success_payload()))
        provider = _make_provider(side_effect=[first, second])

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_text(
                "aaj lunch mein dal chawal khaya"
            )

        self.assertTrue(result["success"])
        self.assertEqual(provider.create_response.call_count, 2)

    def test_fail_when_retry_also_invalid(self):
        invalid = _gemini_response("not-json")
        provider = _make_provider(side_effect=[invalid, invalid])

        with patch.object(self.service, "_get_provider", return_value=provider):
            with self.assertRaises(MealAnalysisParseError):
                self.service.analyse_meal_from_text("anything")

    def test_api_error_raises_meal_analysis_api_error(self):
        from app.providers.gemini import GeminiError

        provider = _make_provider(side_effect=GeminiError("rate limit"))

        with patch.object(self.service, "_get_provider", return_value=provider):
            with self.assertRaises(MealAnalysisAPIError):
                self.service.analyse_meal_from_text("anything")

    def test_non_food_failure_shape_passes(self):
        failure = {
            "success": False,
            "error": "Could not identify food items in the provided input.",
        }
        raw = _gemini_response(json.dumps(failure))
        provider = _make_provider(return_value=raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_text("random words not food")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_instructions_passed_as_system_prompt(self):
        raw = _gemini_response(json.dumps(_success_payload()))
        provider = _make_provider(return_value=raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            self.service.analyse_meal_from_text("dal rice")

        call_params = provider.create_response.call_args[0][0]
        self.assertIn("instructions", call_params)
        self.assertIn("nutrition expert", call_params["instructions"])


if __name__ == "__main__":
    unittest.main()
