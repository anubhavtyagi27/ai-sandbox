from flask import render_template, request, flash, current_app, session, Blueprint
from app.forms import ResponsesAPIForm
from app.services.onepassword import OnePasswordService, OnePasswordError
from app.providers import get_provider
from app.providers.openai import OpenAIError
import json
import logging
import os
import time

# Create blueprint for routes
bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Main page with form and response display.

    Handles both GET (display form) and POST (submit form and call API) requests.
    """
    form = ResponsesAPIForm()
    response_data = None
    error_message = None

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
            # Get the default provider from config
            provider_name = current_app.config.get('DEFAULT_PROVIDER', 'openai')
            logger.info(f"Retrieving API key for provider: {provider_name}")

            # Get provider-specific 1Password reference
            op_reference = current_app.config.get_provider_reference(provider_name)
            api_key = OnePasswordService.get_secret(op_reference)

            # Step 3: Prepare API parameters
            params = {
                'model': form.model.data,
                'input': form.input.data
            }

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
            metrics = {
                'latency_ms': round(latency_seconds * 1000, 2),
                'latency_seconds': round(latency_seconds, 2),
                'model': response_data.get('model', 'N/A'),
                'created_at': response_data.get('created_at'),
                'completion_tokens': None,
                'prompt_tokens': None,
                'total_tokens': None
            }

            # Try to extract token usage (structure may vary)
            usage = response_data.get('usage', {})
            if usage:
                metrics['completion_tokens'] = usage.get('completion_tokens')
                metrics['prompt_tokens'] = usage.get('prompt_tokens')
                metrics['total_tokens'] = usage.get('total_tokens')

            # Add metrics to response data for template
            response_data['_metrics'] = metrics

            # Parse structured data from output for table display
            parsed_content = None
            if response_data.get('output'):
                try:
                    # Extract text from output
                    text_content = []
                    for item in response_data.get('output', []):
                        if item.get('content'):
                            for content_item in item['content']:
                                if content_item.get('text'):
                                    text_content.append(content_item['text'])

                    # Try to parse as JSON
                    if text_content:
                        combined_text = ''.join(text_content)
                        try:
                            parsed_json = json.loads(combined_text)
                            if isinstance(parsed_json, list):
                                response_data['_parsed_data'] = parsed_json
                                logger.info(f"Parsed {len(parsed_json)} items from response")
                        except json.JSONDecodeError:
                            # Not JSON, keep as text
                            response_data['_text_content'] = combined_text
                except Exception as e:
                    logger.warning(f"Error parsing response content: {e}")

            flash('Response received successfully!', 'success')
            logger.info(f"Successfully received response from {provider_name} (latency: {latency_seconds:.2f}s)")

        except OnePasswordError as e:
            error_message = f"1Password Error: {str(e)}"
            logger.error(f"1Password error: {e}")
            flash(error_message, 'danger')

        except OpenAIError as e:
            error_message = f"OpenAI API Error: {str(e)}"
            logger.error(f"OpenAI error: {e}")
            flash(error_message, 'danger')

        except json.JSONDecodeError as e:
            error_message = f"Invalid metadata JSON: {str(e)}"
            logger.error(f"JSON decode error: {e}")
            flash(error_message, 'danger')

        except Exception as e:
            error_message = "An unexpected error occurred. Please try again."
            logger.exception(f"Unexpected error: {e}")
            flash(error_message, 'danger')

    return render_template(
        'index.html',
        form=form,
        response_data=response_data,
        error=error_message
    )
