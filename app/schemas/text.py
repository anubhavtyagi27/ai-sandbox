"""
Text Schema

Handles plain text responses from AI models.
Displays text with proper formatting and whitespace preservation.
"""

from typing import Dict, Any
from .base import ResponseSchema


class TextSchema(ResponseSchema):
    """
    Schema for displaying plain text responses.

    This is the default/fallback schema for most AI text responses.
    """

    def detect(self, data: Any) -> bool:
        """
        Detect if data is plain text.

        This schema accepts strings as well as serving as a fallback
        for data that doesn't match other schemas.

        Args:
            data: Response data to check

        Returns:
            bool: True if data is a string or can be converted to text
        """
        # Accept strings directly
        if isinstance(data, str):
            return True

        # Accept dictionaries that aren't structured data
        # (handled by checking if it's a single dict, not a list)
        if isinstance(data, dict):
            return True

        # Accept other types that can be converted to string
        return True

    def render_context(self, data: Any) -> Dict[str, Any]:
        """
        Prepare text data for rendering.

        Args:
            data: Text data (string, dict, or other)

        Returns:
            Context dictionary with formatted content
        """
        # If it's already a string, use it directly
        if isinstance(data, str):
            content = data

        # If it's a dict, try to extract meaningful text
        elif isinstance(data, dict):
            content = self._extract_text_from_dict(data)

        # Otherwise, convert to string
        else:
            content = str(data)

        return {
            'content': content,
            'schema_type': 'text'
        }

    def _extract_text_from_dict(self, data: Dict[str, Any]) -> str:
        """
        Extract meaningful text from a dictionary response.

        Looks for common text fields and formats them nicely.

        Args:
            data: Dictionary containing response data

        Returns:
            str: Extracted and formatted text
        """
        # Common text field names (in priority order)
        text_fields = [
            'text', 'content', 'message', 'response', 'output',
            'result', 'answer', 'reply', 'data'
        ]

        # Try to find a text field
        for field in text_fields:
            if field in data and isinstance(data[field], str):
                return data[field]

        # If no standard field found, check if there's a single string value
        string_values = [v for v in data.values() if isinstance(v, str)]
        if len(string_values) == 1:
            return string_values[0]

        # Fallback: format the entire dictionary as JSON-like text
        lines = []
        for key, value in data.items():
            if isinstance(value, str):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {str(value)}")

        return '\n'.join(lines) if lines else str(data)

    @property
    def template_name(self) -> str:
        """Template for text display"""
        return 'partials/_text.html'

    @property
    def priority(self) -> int:
        """Lower priority (checked last) as fallback"""
        return 90


class JSONSchema(ResponseSchema):
    """
    Schema for displaying raw JSON data.

    Used when we want to show the raw structure of complex data
    that doesn't fit other schemas well.
    """

    def detect(self, data: Any) -> bool:
        """
        This schema is only used explicitly, not through auto-detection.

        Returns:
            bool: Always False (must be explicitly chosen)
        """
        return False

    def render_context(self, data: Any) -> Dict[str, Any]:
        """
        Prepare data for JSON rendering.

        Args:
            data: Any data to display as JSON

        Returns:
            Context dictionary with JSON-formatted content
        """
        import json

        try:
            # Pretty-print JSON with indentation
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            # Fallback if data can't be JSON serialized
            json_content = str(data)

        return {
            'content': json_content,
            'schema_type': 'json'
        }

    @property
    def template_name(self) -> str:
        """Template for JSON display"""
        return 'partials/_json.html'

    @property
    def priority(self) -> int:
        """Not used in auto-detection"""
        return 100
