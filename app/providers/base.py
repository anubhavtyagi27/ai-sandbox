"""
Base Provider Abstract Class

Defines the interface that all AI provider implementations must follow.
This ensures consistency across different providers (OpenAI, Gemini, Anthropic, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional


class BaseProvider(ABC):
    """
    Abstract base class for AI provider clients.

    All provider implementations must inherit from this class and implement
    all abstract methods to ensure a consistent interface.
    """

    def __init__(self, api_key: str):
        """
        Initialize the provider with an API key.

        Args:
            api_key: The API key for authenticating with the provider
        """
        self.api_key = api_key

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider display name (e.g., 'OpenAI', 'Google Gemini', 'Anthropic').

        Returns:
            str: Human-readable provider name
        """
        pass

    @property
    @abstractmethod
    def models(self) -> List[Tuple[str, str]]:
        """
        Available models for this provider as (value, label) tuples.

        The value is used in API calls, the label is displayed to the user.

        Returns:
            List[Tuple[str, str]]: List of (model_id, display_name) tuples

        Example:
            [('gpt-4o', 'GPT-4o'), ('gpt-4o-mini', 'GPT-4o Mini')]
        """
        pass

    @property
    @abstractmethod
    def form_fields(self) -> Dict[str, Any]:
        """
        Form field definitions for this provider's parameters.

        Defines what parameters the user can configure for API calls.
        Each field should include type, validators, default values, etc.

        Returns:
            Dict[str, Any]: Dictionary of field definitions

        Example:
            {
                'temperature': {
                    'type': 'float',
                    'label': 'Temperature',
                    'min': 0.0,
                    'max': 2.0,
                    'default': 1.0,
                    'required': False
                }
            }
        """
        pass

    @abstractmethod
    def create_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the provider's API and return the response.

        Args:
            params: Dictionary of parameters for the API call (model, input, etc.)

        Returns:
            Dict[str, Any]: Raw API response from the provider

        Raises:
            APIError: If the API call fails
            ValidationError: If parameters are invalid
        """
        pass

    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the provider's response into a standard format.

        Converts provider-specific response formats into a normalized structure
        that the application can display consistently.

        Args:
            response: Raw API response from create_response()

        Returns:
            Dict[str, Any]: Parsed response with standardized fields:
                - 'content': The main response content (text, structured data, etc.)
                - 'metadata': Optional metadata (tokens, finish_reason, etc.)
        """
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters before making an API call.

        Args:
            params: Dictionary of parameters to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
                - is_valid: True if parameters are valid, False otherwise
                - error_message: Description of validation error, or None if valid
        """
        pass

    def get_metrics(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract performance metrics from the API response.

        This is optional - providers can override to return custom metrics.

        Args:
            response: Raw API response

        Returns:
            Dict[str, Any]: Dictionary of metrics (tokens, latency, etc.)
        """
        return {}
