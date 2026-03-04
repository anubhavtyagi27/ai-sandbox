import logging
from typing import Any, Dict, Optional, Tuple

from app.providers.gemini import (
    GeminiAuthenticationError as _ProviderAuthError,
)
from app.providers.gemini import (
    GeminiError,
    GeminiProvider,
)
from app.providers.gemini import (
    GeminiInvalidRequestError as _ProviderInvalidRequestError,
)
from app.providers.gemini import (
    GeminiRateLimitError as _ProviderRateLimitError,
)

logger = logging.getLogger(__name__)


class GeminiClientError(Exception):
    """Base exception for Gemini client errors"""

    pass


class GeminiAuthenticationError(GeminiClientError):
    """Authentication failed"""

    pass


class GeminiRateLimitError(GeminiClientError):
    """Rate limit exceeded"""

    pass


class GeminiInvalidRequestError(GeminiClientError):
    """Invalid request parameters"""

    pass


class GeminiClient:
    """Client for interacting with Google Gemini generateContent API"""

    def __init__(self, api_key: str, timeout: Optional[int] = 60):
        """
        Initialize Gemini client.

        Args:
            api_key: Google AI API key
            timeout: Request timeout in seconds (default 60)
        """
        self.api_key = api_key
        self.timeout = timeout
        self._provider = GeminiProvider(api_key=api_key, timeout=timeout)

    def create_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Gemini generateContent API.

        Accepts the same top-level param keys as OpenAIClient so routes.py
        can call either client identically:
          - model          (str, required)
          - input          (str) — user message text
          - instructions   (str, optional) — system instruction text
          - image_path     (str, optional) — local image file path
          - temperature    (float, optional)
          - max_tokens     (int, optional)

        Returns:
            Raw API response as dictionary (Gemini candidates envelope)

        Raises:
            GeminiAuthenticationError: If API key is invalid (401)
            GeminiRateLimitError: If rate limit is exceeded (429)
            GeminiInvalidRequestError: If request parameters are invalid (400)
            GeminiClientError: For other errors
        """
        try:
            logger.info(
                "Making request to Gemini API with model: %s", params.get("model")
            )
            response = self._provider.create_response(params)
            logger.info("Successfully received response from Gemini")
            return response

        except _ProviderAuthError as exc:
            raise GeminiAuthenticationError(str(exc)) from exc
        except _ProviderRateLimitError as exc:
            raise GeminiRateLimitError(str(exc)) from exc
        except _ProviderInvalidRequestError as exc:
            raise GeminiInvalidRequestError(str(exc)) from exc
        except GeminiError as exc:
            raise GeminiClientError(str(exc)) from exc

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

        if not params.get("input") and not params.get("image_path"):
            return False, "Input is required"

        if "temperature" in params and params["temperature"] is not None:
            temp = params["temperature"]
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                return False, "Temperature must be a number between 0 and 2"

        if "max_tokens" in params and params["max_tokens"] is not None:
            max_tokens = params["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens < 1:
                return False, "max_tokens must be a positive integer"

        return True, None

    def __del__(self):
        if hasattr(self, "_provider"):
            del self._provider
