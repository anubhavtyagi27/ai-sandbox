"""
OpenAI Provider Implementation

Implements the BaseProvider interface for OpenAI's API.
Supports OpenAI Responses API endpoint.
"""

import requests
import logging
from typing import Dict, List, Any, Tuple, Optional

from .base import BaseProvider

logger = logging.getLogger(__name__)


# Custom exceptions for OpenAI-specific errors
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


class OpenAIProvider(BaseProvider):
    """
    OpenAI provider implementation for the Responses API.

    Supports models: GPT-4o, o1, o1-mini
    """

    API_BASE_URL = "https://api.openai.com/v1"
    RESPONSES_ENDPOINT = "/responses"

    def __init__(self, api_key: str, timeout: Optional[int] = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds (None for unlimited)
        """
        super().__init__(api_key)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    @property
    def name(self) -> str:
        """Provider display name"""
        return "OpenAI"

    @property
    def models(self) -> List[Tuple[str, str]]:
        """
        Available OpenAI models.

        Returns:
            List of (model_id, display_name) tuples
        """
        return [
            ('gpt-4o', 'GPT-4o'),
            ('o1', 'o1'),
            ('o1-mini', 'o1-mini')
        ]

    @property
    def form_fields(self) -> Dict[str, Any]:
        """
        Form field definitions for OpenAI parameters.

        Defines the parameters users can configure for API calls.
        """
        return {
            'model': {
                'type': 'select',
                'label': 'Model',
                'choices': self.models,
                'required': True,
                'default': 'gpt-4o'
            },
            'input': {
                'type': 'textarea',
                'label': 'Input / Message',
                'required': True,
                'placeholder': 'Enter your message or prompt...'
            },
            'system_instruction_file': {
                'type': 'text',
                'label': 'System Instruction File Path (optional)',
                'required': False,
                'placeholder': '/path/to/instructions.md'
            },
            'temperature': {
                'type': 'float',
                'label': 'Temperature',
                'min': 0.0,
                'max': 2.0,
                'default': 1.0,
                'step': 0.1,
                'required': False,
                'help_text': 'Controls randomness. Lower is more focused, higher is more random.'
            },
            'max_tokens': {
                'type': 'integer',
                'label': 'Max Tokens',
                'min': 1,
                'default': None,
                'required': False,
                'placeholder': 'Leave empty for unlimited',
                'help_text': 'Maximum number of tokens to generate.'
            },
            'top_p': {
                'type': 'float',
                'label': 'Top P',
                'min': 0.0,
                'max': 1.0,
                'default': 1.0,
                'step': 0.1,
                'required': False,
                'help_text': 'Nucleus sampling. Alternative to temperature.'
            }
        }

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

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse OpenAI response into standard format.

        Args:
            response: Raw API response from OpenAI

        Returns:
            Parsed response with 'content' and 'metadata' fields
        """
        # Extract the main content
        content = response.get('choices', [{}])[0].get('message', {}).get('content', '')

        # Extract metadata
        metadata = {
            'model': response.get('model'),
            'finish_reason': response.get('choices', [{}])[0].get('finish_reason'),
            'usage': response.get('usage', {})
        }

        return {
            'content': content,
            'metadata': metadata
        }

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

    def get_metrics(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract performance metrics from OpenAI response.

        Args:
            response: Raw API response

        Returns:
            Dictionary of metrics (tokens, model, etc.)
        """
        usage = response.get('usage', {})

        return {
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0),
            'model': response.get('model', 'unknown')
        }

    def __del__(self):
        """Clean up session on deletion"""
        if hasattr(self, 'session'):
            self.session.close()
