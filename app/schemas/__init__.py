"""
Response Schema Registry

Central registry for response display schemas.
Provides auto-detection and schema selection for different response types.
"""

from typing import Any, Optional, List
from .base import ResponseSchema
from .structured import StructuredDataSchema
from .text import TextSchema, JSONSchema


# Registry of available schemas (order matters for detection)
SCHEMAS: List[ResponseSchema] = [
    StructuredDataSchema(),  # Check structured data first
    TextSchema(),            # Fallback to text
]

# JSON schema is available but not in auto-detection
JSON_SCHEMA = JSONSchema()


def detect_schema(data: Any, force_schema: Optional[str] = None) -> ResponseSchema:
    """
    Automatically detect the appropriate schema for the given data.

    Args:
        data: Response data to analyze
        force_schema: Optional schema type to force ('json', 'text', 'structured')

    Returns:
        ResponseSchema: The best-matching schema instance

    Example:
        schema = detect_schema(response_data)
        context = schema.render_context(response_data)
        template = schema.template_name
    """
    # Handle forced schema types
    if force_schema:
        if force_schema == 'json':
            return JSON_SCHEMA
        elif force_schema == 'text':
            return TextSchema()
        elif force_schema == 'structured':
            return StructuredDataSchema()

    # Sort schemas by priority (lower number = higher priority)
    sorted_schemas = sorted(SCHEMAS, key=lambda s: s.priority)

    # Try each schema in priority order
    for schema in sorted_schemas:
        if schema.detect(data):
            return schema

    # Fallback to text schema if nothing matches
    return TextSchema()


def render_response(data: Any, force_schema: Optional[str] = None) -> dict:
    """
    Convenience function to detect schema and prepare render context.

    Args:
        data: Response data to render
        force_schema: Optional schema type to force

    Returns:
        dict: Dictionary with 'template' and 'context' keys

    Example:
        result = render_response(api_response)
        return render_template(result['template'], **result['context'])
    """
    schema = detect_schema(data, force_schema)
    context = schema.render_context(data)

    return {
        'template': schema.template_name,
        'context': context,
        'schema_type': type(schema).__name__
    }


__all__ = [
    'ResponseSchema',
    'StructuredDataSchema',
    'TextSchema',
    'JSONSchema',
    'SCHEMAS',
    'detect_schema',
    'render_response',
]
