import json
import unittest
from unittest.mock import MagicMock, patch

from app.services.gemini_client import (
    GeminiAPIError,
    GeminiMealAnalysisService,
    GeminiResponseParseError,
)


def _make_provider(response_json):
    """Return a mock GeminiProvider whose create_response returns response_json."""
    provider = MagicMock()
    if isinstance(response_json, list):
        provider.create_response.side_effect = response_json
    else:
        provider.create_response.return_value = response_json
    # parse_response delegates to GeminiProvider.parse_response logic;
    # use the real implementation via a thin wrapper so we don't duplicate it.
    from app.providers.gemini import GeminiProvider as _Real

    real = _Real.__new__(_Real)
    provider.parse_response.side_effect = real.parse_response
    return provider


def _gemini_response(text: str) -> dict:
    """Wrap a text string in the Gemini candidates envelope."""
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


class TestGeminiMealAnalysisService(unittest.TestCase):
    def setUp(self):
        self.service = GeminiMealAnalysisService()

    @staticmethod
    def _success_payload() -> dict:
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
        raw = _gemini_response(json.dumps(self._success_payload()))
        provider = _make_provider(raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_text("2 rotis with dal makhani")

        self.assertTrue(result["success"])
        self.assertEqual(result["meal_name"], "Dal Makhani with 2 Rotis")

    def test_analyse_meal_from_image_success(self):
        raw = _gemini_response(json.dumps(self._success_payload()))
        provider = _make_provider(raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_image("abc123", "image/jpeg")

        self.assertTrue(result["success"])
        self.assertIn("identified_items", result)

    def test_retry_on_invalid_json_then_success(self):
        first = _gemini_response("not-json")
        second = _gemini_response(json.dumps(self._success_payload()))
        provider = _make_provider([first, second])

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_text(
                "aaj lunch mein dal chawal khaya"
            )

        self.assertTrue(result["success"])
        self.assertEqual(provider.create_response.call_count, 2)

    def test_fail_when_retry_also_invalid(self):
        invalid = _gemini_response("not-json")
        provider = _make_provider([invalid, invalid])

        with patch.object(self.service, "_get_provider", return_value=provider):
            with self.assertRaises(GeminiResponseParseError):
                self.service.analyse_meal_from_text("anything")

    def test_api_error_raises_gemini_api_error(self):
        from app.providers.gemini import GeminiError

        provider = MagicMock()
        provider.create_response.side_effect = GeminiError("rate limit")

        with patch.object(self.service, "_get_provider", return_value=provider):
            with self.assertRaises(GeminiAPIError):
                self.service.analyse_meal_from_text("anything")

    def test_non_food_failure_shape_passes(self):
        model_json = {
            "success": False,
            "error": "Could not identify food items in the provided input.",
        }
        raw = _gemini_response(json.dumps(model_json))
        provider = _make_provider(raw)

        with patch.object(self.service, "_get_provider", return_value=provider):
            result = self.service.analyse_meal_from_text("random words not food")

        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
