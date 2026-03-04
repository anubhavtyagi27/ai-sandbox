"""
Structured Data Schema

Handles structured tabular data (e.g., nutrition tables, product lists, etc.)
Displays data as formatted tables with optional totals.
"""

from typing import Dict, List, Any, Optional
from .base import ResponseSchema


class StructuredDataSchema(ResponseSchema):
    """
    Schema for displaying structured data as tables.

    Detects when response data is a list of dictionaries with consistent keys
    and displays it as a formatted table.
    """

    # Common numeric fields that should have totals calculated
    NUMERIC_FIELDS = {
        'calories', 'protein', 'carbs', 'fat', 'fiber',
        'sugar', 'sodium', 'cholesterol', 'saturated_fat',
        'price', 'cost', 'amount', 'quantity', 'total',
        'count', 'value', 'score'
    }

    def detect(self, data: Any) -> bool:
        """
        Detect if data is structured tabular data.

        Criteria:
        - Must be a list
        - Must have at least one item
        - All items must be dictionaries
        - All dictionaries should have similar keys

        Args:
            data: Response data to check

        Returns:
            bool: True if data matches structured format
        """
        if not isinstance(data, list) or not data:
            return False

        # Check if all items are dictionaries
        if not all(isinstance(item, dict) for item in data):
            return False

        # Check if dictionaries have keys (not empty)
        if not all(item for item in data):
            return False

        # Get keys from first item
        first_keys = set(data[0].keys())

        # Check if all items have similar structure (at least 50% key overlap)
        for item in data[1:]:
            item_keys = set(item.keys())
            overlap = len(first_keys & item_keys) / max(len(first_keys), len(item_keys))
            if overlap < 0.5:
                return False

        return True

    def render_context(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare structured data for table rendering.

        Args:
            data: List of dictionaries with consistent structure

        Returns:
            Context dictionary with columns, rows, and optional totals
        """
        if not data:
            return {
                'columns': [],
                'rows': [],
                'totals': None
            }

        # Extract column names from all items (union of all keys)
        all_columns = set()
        for item in data:
            all_columns.update(item.keys())

        # Sort columns: put common name fields first, then others
        priority_fields = ['name', 'food_name', 'item', 'product', 'title', 'description']
        columns = []

        # Add priority fields first (if they exist)
        for field in priority_fields:
            if field in all_columns:
                columns.append(field)
                all_columns.remove(field)

        # Add remaining fields
        columns.extend(sorted(all_columns))

        # Calculate totals for numeric columns
        totals = self._calculate_totals(data, columns)

        return {
            'columns': columns,
            'rows': data,
            'totals': totals if any(totals.values()) else None,
            'schema_type': 'structured'
        }

    def _calculate_totals(self, data: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
        """
        Calculate totals for numeric columns.

        Args:
            data: List of data rows
            columns: List of column names

        Returns:
            Dictionary of column totals
        """
        totals = {}

        for column in columns:
            # Check if this column should have totals
            if column.lower() in self.NUMERIC_FIELDS or self._is_numeric_column(data, column):
                try:
                    total = sum(
                        float(item.get(column, 0))
                        for item in data
                        if item.get(column) is not None and self._is_numeric(item.get(column))
                    )
                    if total > 0:  # Only include non-zero totals
                        totals[column] = round(total, 2)
                except (ValueError, TypeError):
                    pass  # Skip columns that can't be summed

        return totals

    def _is_numeric_column(self, data: List[Dict[str, Any]], column: str) -> bool:
        """
        Check if a column contains mostly numeric values.

        Args:
            data: List of data rows
            column: Column name to check

        Returns:
            bool: True if column is mostly numeric
        """
        values = [item.get(column) for item in data if item.get(column) is not None]
        if not values:
            return False

        numeric_count = sum(1 for val in values if self._is_numeric(val))
        return numeric_count / len(values) > 0.8  # 80% numeric threshold

    def _is_numeric(self, value: Any) -> bool:
        """
        Check if a value is numeric.

        Args:
            value: Value to check

        Returns:
            bool: True if value is numeric
        """
        if isinstance(value, (int, float)):
            return True

        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False

        return False

    @property
    def template_name(self) -> str:
        """Template for structured data display"""
        return 'partials/_table.html'

    @property
    def priority(self) -> int:
        """Higher priority (checked earlier) for structured data"""
        return 10
