import requests
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class OpenAIError(Exception):
    """Base exception for OpenAI API errors"""
    pass


class OpenAIAuthenticationError(OpenAIError):
    """Authentication failed"""
    pass


class OpenAIRateLimitError(OpenAIError):
    """Rate limit exceeded"""
    pass


class OpenAIInvalidRequestError(OpenAIError):
    """Invalid request parameters"""
    pass


class OpenAIClient:
    """Client for interacting with OpenAI Responses API"""

    API_BASE_URL = "https://api.openai.com/v1"
    RESPONSES_ENDPOINT = "/responses"

    def __init__(self, api_key: str, timeout: Optional[int] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds (None for unlimited)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def create_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call OpenAI Responses API.

        Args:
            params: Request parameters (model, input, etc.)

        Returns:
            API response as dictionary

        Raises:
            OpenAIAuthenticationError: If API key is invalid
            OpenAIRateLimitError: If rate limit is exceeded
            OpenAIInvalidRequestError: If request parameters are invalid
            OpenAIError: For other errors
        """
        url = f"{self.API_BASE_URL}{self.RESPONSES_ENDPOINT}"

        try:
            logger.info(f"Making request to OpenAI Responses API with model: {params.get('model')}")

            response = self.session.post(
                url,
                json=params,
                timeout=self.timeout
            )

            # Handle different status codes
            if response.status_code == 200:
                logger.info("Successfully received response from OpenAI")
                return response.json()

            elif response.status_code == 401:
                raise OpenAIAuthenticationError(
                    "Invalid API key. Please check your OpenAI API key in 1Password."
                )

            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 'unknown')
                raise OpenAIRateLimitError(
                    f"Rate limit exceeded. Please try again later. "
                    f"Retry after: {retry_after} seconds"
                )

            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Invalid request')
                    logger.error(f"OpenAI 400 error details: {error_data}")
                except Exception:
                    error_message = response.text
                    logger.error(f"OpenAI 400 error (raw): {error_message}")

                raise OpenAIInvalidRequestError(f"Invalid request: {error_message}")

            elif response.status_code == 404:
                raise OpenAIInvalidRequestError(
                    "Endpoint not found. The Responses API may not be available yet. "
                    "Please check the OpenAI API documentation."
                )

            else:
                raise OpenAIError(
                    f"API error (status {response.status_code}): {response.text}"
                )

        except requests.exceptions.ConnectionError:
            raise OpenAIError(
                "Connection error. Please check your internet connection."
            )

        except OpenAIError:
            # Re-raise our custom exceptions
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise OpenAIError(f"Request failed: {str(e)}")

    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters before API call.

        Args:
            params: Request parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if 'model' not in params or not params['model']:
            return False, "Model is required"

        if 'input' not in params or not params['input']:
            return False, "Input is required"

        # Validate optional numeric parameters
        if 'temperature' in params:
            temp = params['temperature']
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                return False, "Temperature must be a number between 0 and 2"

        if 'top_p' in params:
            top_p = params['top_p']
            if not isinstance(top_p, (int, float)) or not (0 <= top_p <= 1):
                return False, "top_p must be a number between 0 and 1"

        if 'max_tokens' in params:
            max_tokens = params['max_tokens']
            if not isinstance(max_tokens, int) or max_tokens < 1:
                return False, "max_tokens must be a positive integer"

        return True, None

    def __del__(self):
        """Clean up session on deletion"""
        if hasattr(self, 'session'):
            self.session.close()
