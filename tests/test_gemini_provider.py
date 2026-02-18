import unittest
from typing import Optional
from unittest.mock import MagicMock, patch

from app.providers.gemini import (
    GeminiAuthenticationError,
    GeminiError,
    GeminiInvalidRequestError,
    GeminiProvider,
    GeminiRateLimitError,
)


def _make_http_response(
    status_code: int, json_body: Optional[dict] = None, text: str = ""
):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = text
    mock_resp.json.return_value = json_body or {}
    mock_resp.headers = {}
    return mock_resp


def _candidates_response(text: str, model: str = "gemini-2.5-flash") -> dict:
    return {
        "modelVersion": model,
        "candidates": [
            {
                "content": {"parts": [{"text": text}]},
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 20,
            "totalTokenCount": 30,
        },
    }


class TestGeminiProviderCreateResponse(unittest.TestCase):
    def setUp(self):
        self.provider = GeminiProvider(api_key="test-key")

    def _patch_post(self, mock_response):
        return patch.object(self.provider.session, "post", return_value=mock_response)

    def test_success_returns_json(self):
        raw = _candidates_response("Hello!")
        with self._patch_post(_make_http_response(200, raw)):
            result = self.provider.create_response(
                {
                    "model": "gemini-2.5-flash",
                    "contents": [{"role": "user", "parts": [{"text": "Hi"}]}],
                }
            )
        self.assertEqual(
            result["candidates"][0]["content"]["parts"][0]["text"], "Hello!"
        )

    def test_401_raises_authentication_error(self):
        with self._patch_post(_make_http_response(401, text="Unauthorized")):
            with self.assertRaises(GeminiAuthenticationError):
                self.provider.create_response(
                    {
                        "model": "gemini-2.5-flash",
                        "contents": [],
                    }
                )

    def test_429_raises_rate_limit_error(self):
        resp = _make_http_response(429, text="Too Many Requests")
        resp.headers = {"Retry-After": "30"}
        with self._patch_post(resp):
            with self.assertRaises(GeminiRateLimitError):
                self.provider.create_response(
                    {
                        "model": "gemini-2.5-flash",
                        "contents": [],
                    }
                )

    def test_400_raises_invalid_request_error(self):
        body = {"error": {"message": "Invalid model"}}
        with self._patch_post(_make_http_response(400, body)):
            with self.assertRaises(GeminiInvalidRequestError):
                self.provider.create_response(
                    {
                        "model": "bad-model",
                        "contents": [],
                    }
                )

    def test_500_raises_gemini_error(self):
        with self._patch_post(_make_http_response(500, text="Server Error")):
            with self.assertRaises(GeminiError):
                self.provider.create_response(
                    {
                        "model": "gemini-2.5-flash",
                        "contents": [],
                    }
                )


class TestGeminiProviderParseResponse(unittest.TestCase):
    def setUp(self):
        self.provider = GeminiProvider(api_key="test-key")

    def test_extracts_text_content(self):
        raw = _candidates_response("Nutrition data here")
        result = self.provider.parse_response(raw)
        self.assertEqual(result["content"], "Nutrition data here")

    def test_joins_multiple_parts(self):
        raw = {
            "candidates": [
                {"content": {"parts": [{"text": "Part one"}, {"text": "Part two"}]}}
            ]
        }
        result = self.provider.parse_response(raw)
        self.assertEqual(result["content"], "Part one\nPart two")

    def test_empty_candidates_returns_empty_content(self):
        result = self.provider.parse_response({"candidates": []})
        self.assertEqual(result["content"], "")

    def test_metadata_fields_present(self):
        raw = _candidates_response("text")
        result = self.provider.parse_response(raw)
        self.assertIn("model", result["metadata"])
        self.assertIn("finish_reason", result["metadata"])
        self.assertIn("usage", result["metadata"])


class TestGeminiProviderValidateParameters(unittest.TestCase):
    def setUp(self):
        self.provider = GeminiProvider(api_key="test-key")

    def test_valid_params(self):
        valid, msg = self.provider.validate_parameters(
            {
                "model": "gemini-2.5-flash",
                "contents": [{"role": "user", "parts": [{"text": "Hi"}]}],
            }
        )
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_missing_model(self):
        valid, msg = self.provider.validate_parameters({"contents": []})
        self.assertFalse(valid)
        self.assertIn("Model", msg)

    def test_missing_contents(self):
        valid, msg = self.provider.validate_parameters({"model": "gemini-2.5-flash"})
        self.assertFalse(valid)
        self.assertIn("contents", msg)

    def test_invalid_temperature(self):
        valid, msg = self.provider.validate_parameters(
            {
                "model": "gemini-2.5-flash",
                "contents": [{"role": "user", "parts": [{"text": "Hi"}]}],
                "temperature": 5.0,
            }
        )
        self.assertFalse(valid)
        self.assertIn("Temperature", msg)

    def test_invalid_max_tokens(self):
        valid, msg = self.provider.validate_parameters(
            {
                "model": "gemini-2.5-flash",
                "contents": [{"role": "user", "parts": [{"text": "Hi"}]}],
                "max_tokens": -1,
            }
        )
        self.assertFalse(valid)
        self.assertIn("max_tokens", msg)


class TestGeminiProviderGetMetrics(unittest.TestCase):
    def setUp(self):
        self.provider = GeminiProvider(api_key="test-key")

    def test_extracts_token_counts(self):
        raw = _candidates_response("text")
        metrics = self.provider.get_metrics(raw)
        self.assertEqual(metrics["prompt_tokens"], 10)
        self.assertEqual(metrics["completion_tokens"], 20)
        self.assertEqual(metrics["total_tokens"], 30)
        self.assertEqual(metrics["model"], "gemini-2.5-flash")
        self.assertEqual(metrics["finish_reason"], "STOP")

    def test_empty_response_defaults_to_zero(self):
        metrics = self.provider.get_metrics({})
        self.assertEqual(metrics["prompt_tokens"], 0)
        self.assertEqual(metrics["total_tokens"], 0)
        self.assertEqual(metrics["model"], "unknown")


if __name__ == "__main__":
    unittest.main()
