from flask import render_template, request, flash, current_app, session, Blueprint
from app.forms import ResponsesAPIForm, ProviderSelectionForm
from app.services.onepassword import OnePasswordService, OnePasswordError
from app.providers import get_provider, list_providers
from app.schemas import detect_schema
from config import Config
import json
import logging
import os
import time
from datetime import datetime, timezone

# Create blueprint for routes
bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


def _format_created_at(created_value):
    """
    Normalize provider timestamp fields into a readable local date/time string.

    Supports Unix timestamps (seconds/ms), ISO-8601 strings, or passthrough fallback.
    """
    if created_value is None:
        return None

    # Numeric timestamps (seconds or milliseconds)
    try:
        ts = float(created_value)
        if ts > 1_000_000_000_000:  # milliseconds
            ts /= 1000.0
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")
    except (TypeError, ValueError, OSError):
        pass

    # ISO string timestamps
    try:
        raw = str(created_value).strip()
        dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %I:%M:%S %p %Z")
    except (TypeError, ValueError):
        return str(created_value)


def _extract_output_parameters(response_data):
    """
    Build a concise set of useful output parameters for the response UI.
    """
    output_parameters = {}

    if response_data.get('id'):
        output_parameters['Response ID'] = response_data.get('id')
    if response_data.get('status'):
        output_parameters['Status'] = response_data.get('status')
    if response_data.get('max_output_tokens') is not None:
        output_parameters['Max Output Tokens'] = response_data.get('max_output_tokens')
    if response_data.get('parallel_tool_calls') is not None:
        output_parameters['Parallel Tool Calls'] = response_data.get('parallel_tool_calls')
    if response_data.get('store') is not None:
        output_parameters['Stored'] = response_data.get('store')
    if response_data.get('truncation'):
        output_parameters['Truncation'] = response_data.get('truncation')

    reasoning = response_data.get('reasoning')
    if isinstance(reasoning, dict):
        effort = reasoning.get('effort')
        if effort:
            output_parameters['Reasoning Effort'] = effort

    output = response_data.get('output')
    if isinstance(output, list):
        output_parameters['Output Items'] = len(output)

    return output_parameters


@bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Main page with form and response display.

    Handles both GET (display form) and POST (submit form and call API) requests.
    Supports provider selection and dynamic form generation.
    """
    # Get selected provider from request or session
    selected_provider = request.args.get('provider') or request.form.get('provider') or session.get('selected_provider') or current_app.config.get('DEFAULT_PROVIDER', 'openai')

    # Save selected provider to session
    session['selected_provider'] = selected_provider

    # Create provider selection form
    provider_form = ProviderSelectionForm()
    if request.method == 'GET':
        provider_form.provider.data = selected_provider

    # Create API form with provider-specific fields
    form = ResponsesAPIForm(provider_name=selected_provider)
    response_data = None
    error_message = None

    # Get available providers for display
    available_providers = list_providers()

    # Pre-populate system instruction file path from session
    if request.method == 'GET' and 'system_instruction_file' in session:
        form.system_instruction_file.data = session['system_instruction_file']

    if form.validate_on_submit():
        try:
            # Step 1: Handle system instruction file path
            system_instruction = None
            if form.system_instruction_file.data and form.system_instruction_file.data.strip():
                file_path = form.system_instruction_file.data.strip()

                # Save the file path to session for persistence
                session['system_instruction_file'] = file_path

                # Read the markdown file
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            system_instruction = f.read()
                        logger.info(f"Loaded system instruction from: {file_path}")
                    except Exception as e:
                        flash(f"Error reading file {file_path}: {str(e)}", 'warning')
                        logger.error(f"Error reading system instruction file: {e}")
                else:
                    flash(f"File not found: {file_path}", 'warning')
                    logger.warning(f"System instruction file not found: {file_path}")
            elif 'system_instruction_file' in session:
                # Use previously saved file path
                file_path = session['system_instruction_file']
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            system_instruction = f.read()
                        logger.info(f"Loaded system instruction from saved path: {file_path}")
                        # Pre-populate the form field with saved path
                        form.system_instruction_file.data = file_path
                    except Exception as e:
                        logger.error(f"Error reading saved system instruction file: {e}")

            # Step 2: Retrieve API key from 1Password
            # Use the selected provider
            provider_name = selected_provider
            logger.info(f"Retrieving API key for provider: {provider_name}")

            # Get provider-specific 1Password reference
            op_reference = Config.get_provider_reference(provider_name)
            api_key = OnePasswordService.get_secret(op_reference)

            # Step 3: Prepare API parameters
            params = {
                'model': form.model.data,
                'input': form.input.data,  # May be empty in image mode
                'input_mode': form.input_mode.data
            }

            # Validate input based on mode
            if form.input_mode.data == 'text':
                if not form.input.data or not form.input.data.strip():
                    raise ValueError("Input text is required in text mode")
            elif form.input_mode.data == 'image':
                if not form.image_path.data or not form.image_path.data.strip():
                    raise ValueError("Image path is required in image mode")
                
                image_path = form.image_path.data.strip()
                if not os.path.exists(image_path):
                    raise ValueError(f"Image file not found at: {image_path}")
                
                params['image_path'] = image_path
                logger.info(f"Processing image input: {image_path}")

            # Add system instruction if available (top-level parameter)
            if system_instruction:
                params['instructions'] = system_instruction
                logger.info(f"Added system instructions ({len(system_instruction)} characters)")

            # Add optional parameters if provided
            if form.max_tokens.data:
                params['max_tokens'] = form.max_tokens.data

            if form.temperature.data is not None:
                params['temperature'] = float(form.temperature.data)

            if form.top_p.data is not None:
                params['top_p'] = float(form.top_p.data)

            if form.stream.data:
                params['stream'] = form.stream.data

            if form.store.data:
                params['store'] = form.store.data

            if form.metadata.data and form.metadata.data.strip():
                params['metadata'] = json.loads(form.metadata.data)

            # Step 4: Call Provider API
            logger.info(f"Calling {provider_name} API with model: {params['model']}")
            provider = get_provider(provider_name, api_key, timeout=None)  # No timeout - unlimited

            if not provider:
                raise ValueError(f"Provider '{provider_name}' is not supported")

            # Measure response time
            start_time = time.time()
            response_data = provider.create_response(params)
            end_time = time.time()

            # Calculate latency
            latency_seconds = end_time - start_time

            # Extract metrics for display
            created_raw = response_data.get('created_at') or response_data.get('created')
            metrics = {
                'latency_ms': round(latency_seconds * 1000, 2),
                'latency_seconds': round(latency_seconds, 2),
                'model': response_data.get('model', 'N/A'),
                'created_at_raw': created_raw,
                'created_at_display': _format_created_at(created_raw),
                'completion_tokens': None,
                'prompt_tokens': None,
                'total_tokens': None,
                'output_parameters': _extract_output_parameters(response_data)
            }

            # Try to extract token usage (structure may vary)
            usage = response_data.get('usage', {})
            if usage:
                metrics['completion_tokens'] = usage.get('completion_tokens')
                metrics['prompt_tokens'] = usage.get('prompt_tokens')
                metrics['total_tokens'] = usage.get('total_tokens')

            # Add metrics to response data for template
            response_data['_metrics'] = metrics

            # Add provider information for display
            response_data['_provider'] = {
                'name': provider_name,
                'display_name': available_providers.get(provider_name, provider_name.title())
            }

            # Parse response content and detect appropriate display schema
            parsed_content = None
            display_schema = None

            if response_data.get('output'):
                try:
                    # Extract text from output
                    text_content = []
                    for item in response_data.get('output', []):
                        if item.get('content'):
                            for content_item in item['content']:
                                if content_item.get('text'):
                                    text_content.append(content_item['text'])

                    # Try to parse as JSON first
                    if text_content:
                        combined_text = ''.join(text_content)
                        try:
                            parsed_json = json.loads(combined_text)
                            parsed_content = parsed_json
                            logger.info(f"Parsed JSON content from response")
                        except json.JSONDecodeError:
                            # Not JSON, use plain text
                            parsed_content = combined_text
                            logger.info("Response is plain text")

                except Exception as e:
                    logger.warning(f"Error parsing response content: {e}")
                    parsed_content = str(response_data.get('output', ''))

            # Auto-detect the appropriate schema for display
            if parsed_content is not None:
                schema = detect_schema(parsed_content)
                display_schema = schema.render_context(parsed_content)
                display_schema['template'] = schema.template_name
                response_data['_display_schema'] = display_schema
                logger.info(f"Using schema: {type(schema).__name__}")

            flash('Response received successfully!', 'success')
            logger.info(f"Successfully received response from {provider_name} (latency: {latency_seconds:.2f}s)")

        except OnePasswordError as e:
            error_message = f"1Password Error: {str(e)}"
            logger.error(f"1Password error: {e}")
            flash(error_message, 'danger')

        except json.JSONDecodeError as e:
            error_message = f"Invalid metadata JSON: {str(e)}"
            logger.error(f"JSON decode error: {e}")
            flash(error_message, 'danger')

        except ValueError as e:
            # Catches provider validation errors and configuration errors
            error_message = str(e)
            logger.error(f"Validation error: {e}")
            flash(error_message, 'danger')

        except Exception as e:
            # Generic error handler for provider API errors and unexpected issues
            error_type = type(e).__name__
            error_message = f"{provider_name.title()} API Error: {str(e)}"
            logger.exception(f"{error_type} from {provider_name}: {e}")
            flash(error_message, 'danger')

    return render_template(
        'index.html',
        form=form,
        provider_form=provider_form,
        selected_provider=selected_provider,
        available_providers=available_providers,
        response_data=response_data,
        error=error_message
    )
