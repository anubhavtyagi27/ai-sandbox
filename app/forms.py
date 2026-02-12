from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError
import json


class ResponsesAPIForm(FlaskForm):
    """Form for OpenAI Responses API parameters"""

    # Latest OpenAI models
    MODEL_CHOICES = [
        ('gpt-4o', 'GPT-4o (5.2)'),
        ('o1', 'o1 (5-mini)'),
        ('o1-mini', 'o1-mini (5-nano)'),
    ]

    model = SelectField(
        'Model',
        choices=MODEL_CHOICES,
        default='gpt-4o',
        validators=[DataRequired(message="Model is required")],
        render_kw={"class": "form-select"}
    )

    system_instruction_file = StringField(
        'System Instruction File Path',
        validators=[Optional()],
        render_kw={
            "placeholder": "/path/to/system-instructions.md",
            "class": "form-control"
        }
    )

    input = TextAreaField(
        'Input',
        validators=[
            DataRequired(message="Input is required"),
            Length(min=1, message="Input cannot be empty")
        ],
        render_kw={
            "rows": 8,
            "placeholder": "Enter your prompt or message here...",
            "class": "form-control"
        }
    )

    max_tokens = IntegerField(
        'Max Tokens',
        validators=[
            Optional(),
            NumberRange(min=1, max=128000, message="Max tokens must be between 1 and 128000")
        ],
        render_kw={
            "placeholder": "Optional (e.g., 1000)",
            "class": "form-control"
        }
    )

    temperature = DecimalField(
        'Temperature',
        validators=[
            Optional(),
            NumberRange(min=0, max=2, message="Temperature must be between 0 and 2")
        ],
        render_kw={
            "placeholder": "0.0 - 2.0 (default: 1.0)",
            "step": "0.1",
            "class": "form-control"
        }
    )

    top_p = DecimalField(
        'Top P',
        validators=[
            Optional(),
            NumberRange(min=0, max=1, message="Top P must be between 0 and 1")
        ],
        render_kw={
            "placeholder": "0.0 - 1.0",
            "step": "0.1",
            "class": "form-control"
        }
    )

    stream = BooleanField(
        'Stream Response',
        default=False,
        render_kw={"class": "form-check-input"}
    )

    store = BooleanField(
        'Store Response',
        default=False,
        render_kw={"class": "form-check-input"}
    )

    metadata = TextAreaField(
        'Metadata (JSON)',
        validators=[Optional()],
        render_kw={
            "rows": 3,
            "placeholder": '{"key1": "value1", "key2": "value2"}',
            "class": "form-control font-monospace"
        }
    )

    def validate_metadata(self, field):
        """Custom validator for metadata JSON format"""
        if field.data and field.data.strip():
            try:
                parsed = json.loads(field.data)
                # Ensure it's a dictionary
                if not isinstance(parsed, dict):
                    raise ValidationError("Metadata must be a JSON object (dictionary)")
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON format: {str(e)}")
