from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, BooleanField, SelectField, RadioField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError
from app.providers import list_providers, get_provider_class
import json


class ProviderSelectionForm(FlaskForm):
    """Form for selecting AI provider"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate provider choices
        providers = list_providers()
        self.provider.choices = [(name, display_name) for name, display_name in providers.items()]

    provider = SelectField(
        'AI Provider',
        validators=[DataRequired(message="Provider is required")],
        render_kw={"class": "form-select"}
    )


class ResponsesAPIForm(FlaskForm):
    """Form for AI API parameters - supports multiple providers"""

    def __init__(self, provider_name='openai', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provider_name = provider_name

        # Get provider class to fetch available models
        provider_class = get_provider_class(provider_name)
        if provider_class:
            # Create temporary instance to get models
            temp_provider = provider_class(api_key='dummy')
            self.model.choices = temp_provider.models
        else:
            # Fallback to default choices
            self.model.choices = [('gpt-4o', 'GPT-4o')]

    model = SelectField(
        'Model',
        choices=[],  # Will be populated dynamically in __init__
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

    input_mode = RadioField(
        'Input Mode',
        choices=[('text', 'Text'), ('image', 'Image')],
        default='text',
        render_kw={"class": "btn-group-toggle"}
    )

    image_path = StringField(
        'Image Path',
        validators=[Optional()],
        render_kw={
            "placeholder": "/absolute/path/to/image.jpg",
            "class": "form-control"
        }
    )

    input = TextAreaField(
        'Input',
        validators=[
            Optional(),
            # DataRequired is handled conditionally in validation
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
