"""
Base Response Schema Abstract Class

Defines the interface for response display schemas.
Different schemas handle different types of data (structured tables, plain text, JSON, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class ResponseSchema(ABC):
    """
    Abstract base class for response display schemas.

    Each schema knows how to:
    1. Detect if it can handle a particular response format
    2. Prepare the data for template rendering
    3. Specify which template should be used
    """

    @abstractmethod
    def detect(self, data: Any) -> bool:
        """
        Detect if this schema can handle the given data.

        Args:
            data: Response data to check

        Returns:
            bool: True if this schema can handle the data, False otherwise
        """
        pass

    @abstractmethod
    def render_context(self, data: Any) -> Dict[str, Any]:
        """
        Prepare data for template rendering.

        Transforms the raw data into a format suitable for the template.

        Args:
            data: Response data to prepare

        Returns:
            Dict[str, Any]: Context dictionary for template rendering
        """
        pass

    @property
    @abstractmethod
    def template_name(self) -> str:
        """
        Template file to use for rendering this schema.

        Returns:
            str: Template filename (e.g., 'partials/_table.html')
        """
        pass

    @property
    def priority(self) -> int:
        """
        Schema priority for detection order.

        Lower numbers are checked first. Useful when multiple schemas
        might match the same data - the more specific schema should
        have lower priority number.

        Returns:
            int: Priority value (default: 50)
        """
        return 50
