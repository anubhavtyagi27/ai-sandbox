import unittest
from unittest.mock import MagicMock, patch

from app.services.gemini_client import (
    GeminiAuthenticationError,
    GeminiClient,
    GeminiClientError,
    GeminiInvalidRequestError,
    GeminiRateLimitError,
)


def _make_provider(return_value=None, side_effect=None):
    provider = MagicMock()
    if side_effect:
        provider.create_response.side_effect = side_effect
    else:
        provider.create_response.return_value = return_value or {}
    return provider


class TestGeminiClientCreateResponse(unittest.TestCase):
    def setUp(self):
        self.client = GeminiClient(api_key="test-key")

    def _patch_provider(self, **kwargs):
        provider = _make_provider(**kwargs)
        return patch.object(self.client, "_provider", provider), provider

    def test_success_returns_raw_response(self):
        raw = {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]}
        ctx, _ = self._patch_provider(return_value=raw)
        with ctx:
            result = self.client.create_response(
                {"model": "gemini-2.5-flash", "input": "Hi"}
            )
        self.assertEqual(result, raw)

    def test_authentication_error_is_wrapped(self):
        from app.providers.gemini import GeminiAuthenticationError as _PE

        ctx, _ = self._patch_provider(side_effect=_PE("bad key"))
        with ctx:
            with self.assertRaises(GeminiAuthenticationError):
                self.client.create_response(
                    {"model": "gemini-2.5-flash", "input": "Hi"}
                )

    def test_rate_limit_error_is_wrapped(self):
        from app.providers.gemini import GeminiRateLimitError as _PE

        ctx, _ = self._patch_provider(side_effect=_PE("slow down"))
        with ctx:
            with self.assertRaises(GeminiRateLimitError):
                self.client.create_response(
                    {"model": "gemini-2.5-flash", "input": "Hi"}
                )

    def test_invalid_request_error_is_wrapped(self):
        from app.providers.gemini import GeminiInvalidRequestError as _PE

        ctx, _ = self._patch_provider(side_effect=_PE("bad param"))
        with ctx:
            with self.assertRaises(GeminiInvalidRequestError):
                self.client.create_response(
                    {"model": "gemini-2.5-flash", "input": "Hi"}
                )

    def test_generic_gemini_error_is_wrapped(self):
        from app.providers.gemini import GeminiError as _PE

        ctx, _ = self._patch_provider(side_effect=_PE("oops"))
        with ctx:
            with self.assertRaises(GeminiClientError):
                self.client.create_response(
                    {"model": "gemini-2.5-flash", "input": "Hi"}
                )


class TestGeminiClientValidateParameters(unittest.TestCase):
    def setUp(self):
        self.client = GeminiClient(api_key="test-key")

    def test_valid_text_params(self):
        valid, msg = self.client.validate_parameters(
            {"model": "gemini-2.5-flash", "input": "Hello"}
        )
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_valid_image_params(self):
        valid, msg = self.client.validate_parameters(
            {"model": "gemini-2.5-flash", "image_path": "/tmp/food.jpg"}
        )
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_missing_model(self):
        valid, msg = self.client.validate_parameters({"input": "Hello"})
        self.assertFalse(valid)
        self.assertIn("Model", msg)

    def test_missing_input_and_image(self):
        valid, msg = self.client.validate_parameters({"model": "gemini-2.5-flash"})
        self.assertFalse(valid)
        self.assertIn("Input", msg)

    def test_invalid_temperature(self):
        valid, msg = self.client.validate_parameters(
            {"model": "gemini-2.5-flash", "input": "Hi", "temperature": 5.0}
        )
        self.assertFalse(valid)
        self.assertIn("Temperature", msg)

    def test_invalid_max_tokens(self):
        valid, msg = self.client.validate_parameters(
            {"model": "gemini-2.5-flash", "input": "Hi", "max_tokens": 0}
        )
        self.assertFalse(valid)
        self.assertIn("max_tokens", msg)


if __name__ == "__main__":
    unittest.main()
