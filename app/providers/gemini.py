"""
Google Gemini Provider Implementation

Implements the BaseProvider interface for Google's Gemini API.
Supports Gemini REST API (generateContent endpoint).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from .base import BaseProvider

logger = logging.getLogger(__name__)


# Custom exceptions for Gemini-specific errors
class GeminiError(Exception):
    """Base exception for Gemini API errors"""

    pass


class GeminiAuthenticationError(GeminiError):
    """Authentication failed - invalid or missing API key"""

    pass


class GeminiRateLimitError(GeminiError):
    """Rate limit exceeded"""

    pass


class GeminiInvalidRequestError(GeminiError):
    """Invalid request parameters"""

    pass


class GeminiProvider(BaseProvider):
    """
    Google Gemini provider implementation.

    Supports models: Gemini 2.5 Flash, Gemini 2.0 Flash, Gemini 1.5 Pro
    Uses the generateContent REST endpoint.
    """

    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, timeout: Optional[int] = 60):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google AI API key
            timeout: Request timeout in seconds (default 60)
        """
        super().__init__(api_key)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def models(self) -> List[Tuple[str, str]]:
        return [
            ("gemini-2.5-flash", "Gemini 2.5 Flash"),
            ("gemini-2.0-flash", "Gemini 2.0 Flash"),
            ("gemini-1.5-pro", "Gemini 1.5 Pro"),
            ("gemini-1.5-flash", "Gemini 1.5 Flash"),
        ]

    @property
    def form_fields(self) -> Dict[str, Any]:
        return {
            "model": {
                "type": "select",
                "label": "Model",
                "choices": self.models,
                "required": True,
                "default": "gemini-2.5-flash",
            },
            "input": {
                "type": "textarea",
                "label": "Input / Message",
                "required": True,
                "placeholder": "Enter your message or prompt...",
            },
            "system_instruction": {
                "type": "textarea",
                "label": "System Instruction (optional)",
                "required": False,
                "placeholder": "Enter system-level instructions...",
            },
            "temperature": {
                "type": "float",
                "label": "Temperature",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
                "step": 0.1,
                "required": False,
                "help_text": "Controls randomness. Lower is more focused, higher is more random.",
            },
            "max_tokens": {
                "type": "integer",
                "label": "Max Output Tokens",
                "min": 1,
                "default": None,
                "required": False,
                "placeholder": "Leave empty for model default",
                "help_text": "Maximum number of tokens to generate.",
            },
        }

    def create_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Gemini generateContent API.

        Args:
            params: Request parameters. Expected keys:
                - model (str): Model ID
                - contents (list): Gemini-format contents array
                - system_instruction (dict, optional): System instruction object
                - temperature (float, optional)
                - max_tokens (int, optional)

        Returns:
            Raw API response as dictionary

        Raises:
            GeminiAuthenticationError: If API key is invalid (401)
            GeminiRateLimitError: If rate limit is exceeded (429)
            GeminiInvalidRequestError: If request parameters are invalid (400)
            GeminiError: For other errors
        """
        model = params.get("model", "gemini-2.5-flash")
        url = f"{self.API_BASE_URL}/models/{model}:generateContent"

        payload: Dict[str, Any] = {
            "contents": params.get("contents", []),
        }

        if params.get("system_instruction"):
            payload["system_instruction"] = params["system_instruction"]

        generation_config: Dict[str, Any] = {}
        if "temperature" in params and params["temperature"] is not None:
            generation_config["temperature"] = params["temperature"]
        if "max_tokens" in params and params["max_tokens"] is not None:
            generation_config["maxOutputTokens"] = params["max_tokens"]
        if generation_config:
            payload["generationConfig"] = generation_config

        try:
            logger.info("Making request to Gemini API with model: %s", model)
            response = self.session.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError:
            raise GeminiError(
                "Connection error. Please check your internet connection."
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Gemini request exception: %s", exc)
            raise GeminiError(f"Request failed: {exc}") from exc

        if response.status_code == 200:
            logger.info("Successfully received response from Gemini")
            try:
                return response.json()
            except ValueError as exc:
                raise GeminiError("Gemini API returned invalid JSON response") from exc

        elif response.status_code == 401:
            raise GeminiAuthenticationError(
                "Invalid API key. Please check your Gemini API key in 1Password."
            )

        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise GeminiRateLimitError(
                f"Rate limit exceeded. Please try again later. "
                f"Retry after: {retry_after} seconds"
            )

        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get(
                    "message", "Invalid request"
                )
                logger.error("Gemini 400 error details: %s", error_data)
            except Exception:
                error_message = response.text
                logger.error("Gemini 400 error (raw): %s", error_message)
            raise GeminiInvalidRequestError(f"Invalid request: {error_message}")

        else:
            body = response.text[:500]
            logger.error(
                "Gemini API error status=%s body=%s", response.status_code, body
            )
            raise GeminiError(f"API error (status {response.status_code}): {body}")

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gemini response into standard format.

        Extracts text from candidates[0].content.parts[].text and
        returns a normalised dict with 'content' and 'metadata' keys.

        Args:
            response: Raw API response from create_response()

        Returns:
            Dict with 'content' (str) and 'metadata' (dict) keys
        """
        candidates = response.get("candidates", [])
        content_text = ""

        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text_chunks = [
                part["text"]
                for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
            content_text = "\n".join(text_chunks).strip()

        metadata = {
            "model": response.get("modelVersion"),
            "finish_reason": candidates[0].get("finishReason") if candidates else None,
            "usage": response.get("usageMetadata", {}),
        }

        return {
            "content": content_text,
            "metadata": metadata,
        }

    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters before API call.

        Args:
            params: Request parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not params.get("model"):
            return False, "Model is required"

        if not params.get("contents"):
            return False, "contents is required"

        if "temperature" in params and params["temperature"] is not None:
            temp = params["temperature"]
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                return False, "Temperature must be a number between 0 and 2"

        if "max_tokens" in params and params["max_tokens"] is not None:
            max_tokens = params["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens < 1:
                return False, "max_tokens must be a positive integer"

        return True, None

    def get_metrics(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract performance metrics from Gemini response.

        Args:
            response: Raw API response

        Returns:
            Dictionary of metrics (tokens, model, etc.)
        """
        usage = response.get("usageMetadata", {})
        candidates = response.get("candidates", [])

        return {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
            "model": response.get("modelVersion", "unknown"),
            "finish_reason": candidates[0].get("finishReason") if candidates else None,
        }

    def __del__(self):
        if hasattr(self, "session"):
            self.session.close()
