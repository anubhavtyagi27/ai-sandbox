import json
import logging
import os
import time
from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, jsonify, render_template, request, send_file, session
from werkzeug.utils import secure_filename

from app.forms import ProviderSelectionForm, ResponsesAPIForm
from app.providers import get_provider, get_provider_class, list_providers
from app.schemas import detect_schema
from app.services.onepassword import OnePasswordError, OnePasswordService
from config import Config

# Create blueprint for routes
bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


def _get_upload_folder():
    folder = current_app.config.get("UPLOAD_FOLDER")
    os.makedirs(folder, exist_ok=True)
    return folder


def _find_active_image(upload_folder):
    """Return path to the active image file, or None if none exists."""
    for ext in ALLOWED_IMAGE_EXTENSIONS:
        path = os.path.join(upload_folder, f"active_image.{ext}")
        if os.path.exists(path):
            return path
    return None


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
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
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

    if response_data.get("id"):
        output_parameters["Response ID"] = response_data.get("id")
    if response_data.get("status"):
        output_parameters["Status"] = response_data.get("status")
    if response_data.get("max_output_tokens") is not None:
        output_parameters["Max Output Tokens"] = response_data.get("max_output_tokens")
    if response_data.get("parallel_tool_calls") is not None:
        output_parameters["Parallel Tool Calls"] = response_data.get(
            "parallel_tool_calls"
        )
    if response_data.get("store") is not None:
        output_parameters["Stored"] = response_data.get("store")
    if response_data.get("truncation"):
        output_parameters["Truncation"] = response_data.get("truncation")

    reasoning = response_data.get("reasoning")
    if isinstance(reasoning, dict):
        effort = reasoning.get("effort")
        if effort:
            output_parameters["Reasoning Effort"] = effort

    output = response_data.get("output")
    if isinstance(output, list):
        output_parameters["Output Items"] = len(output)

    return output_parameters


@bp.route("/api/providers/<name>/models")
def provider_models(name):
    """Return model list for a given provider as JSON."""
    provider_class = get_provider_class(name)
    if not provider_class:
        return jsonify({"error": f"Unknown provider: {name}"}), 404
    temp = provider_class(api_key="dummy")
    return jsonify([{"value": v, "label": l} for v, l in temp.models])


@bp.route("/api/uploads/instructions")
def preview_instructions():
    """Return the content of the active system instructions file."""
    folder = current_app.config.get("UPLOAD_FOLDER", "")
    path = os.path.join(folder, "active_instructions.md")
    if not os.path.exists(path):
        return jsonify({"exists": False, "content": None})
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"exists": True, "content": content})


@bp.route("/api/uploads/image")
def serve_active_image():
    """Serve the active image file."""
    folder = current_app.config.get("UPLOAD_FOLDER", "")
    img_path = _find_active_image(folder)
    if not img_path:
        return jsonify({"error": "No active image"}), 404
    return send_file(img_path)


@bp.route("/", methods=["GET", "POST"])
def index():
    """
    Main page with form and response display.

    Handles both GET (display form) and POST (submit form and call API) requests.
    Supports provider selection and dynamic form generation.
    """
    # Get selected provider from request or session
    selected_provider = (
        request.args.get("provider")
        or request.form.get("provider")
        or session.get("selected_provider")
        or current_app.config.get("DEFAULT_PROVIDER", "openai")
    )

    # Save selected provider to session
    session["selected_provider"] = selected_provider

    # Create provider selection form
    provider_form = ProviderSelectionForm()
    if request.method == "GET":
        provider_form.provider.data = selected_provider

    # Create API form with provider-specific fields
    form = ResponsesAPIForm(provider_name=selected_provider)
    response_data = None
    error_message = None

    # Get available providers for display
    available_providers = list_providers()

    if form.validate_on_submit():
        try:
            # Step 1: Handle system instruction file upload
            system_instruction = None
            upload_folder = _get_upload_folder()
            instr_path = os.path.join(upload_folder, "active_instructions.md")

            uploaded_instr = form.system_instruction_upload.data
            if uploaded_instr and uploaded_instr.filename:
                uploaded_instr.save(instr_path)
                logger.info(f"Saved system instruction to: {instr_path}")

            if os.path.exists(instr_path):
                try:
                    with open(instr_path, "r", encoding="utf-8") as f:
                        system_instruction = f.read()
                    logger.info(
                        f"Loaded system instruction ({len(system_instruction)} chars)"
                    )
                except Exception as e:
                    flash(f"Error reading system instructions: {str(e)}", "warning")
                    logger.error(f"Error reading system instruction file: {e}")

            # Step 2: Retrieve API key from 1Password
            # Use the selected provider
            provider_name = selected_provider
            logger.info(f"Retrieving API key for provider: {provider_name}")

            # Get provider-specific 1Password reference
            op_reference = Config.get_provider_reference(provider_name)
            api_key = OnePasswordService.get_secret(op_reference)

            # Step 3: Prepare API parameters
            params = {
                "model": form.model.data,
                "input": form.input.data,  # May be empty in image mode
                "input_mode": form.input_mode.data,
            }

            # Validate input based on mode
            if form.input_mode.data == "text":
                if not form.input.data or not form.input.data.strip():
                    raise ValueError("Input text is required in text mode")
            elif form.input_mode.data == "image":
                active_img_path = None

                uploaded_img = form.image_upload.data
                if uploaded_img and uploaded_img.filename:
                    filename = secure_filename(uploaded_img.filename)
                    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
                    # Remove any previously stored active image
                    for old_ext in ALLOWED_IMAGE_EXTENSIONS:
                        old_path = os.path.join(upload_folder, f"active_image.{old_ext}")
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    active_img_path = os.path.join(upload_folder, f"active_image.{ext}")
                    uploaded_img.save(active_img_path)
                    logger.info(f"Saved uploaded image to: {active_img_path}")
                else:
                    active_img_path = _find_active_image(upload_folder)

                if not active_img_path:
                    raise ValueError(
                        "An image is required in Image Mode. Please upload an image."
                    )

                params["image_path"] = active_img_path
                logger.info(f"Processing image input: {active_img_path}")

            # Add system instruction if available (top-level parameter)
            if system_instruction:
                params["instructions"] = system_instruction
                logger.info(
                    f"Added system instructions ({len(system_instruction)} characters)"
                )

            # Add optional parameters if provided
            if form.max_tokens.data:
                params["max_tokens"] = form.max_tokens.data

            if form.temperature.data is not None:
                params["temperature"] = float(form.temperature.data)

            if form.top_p.data is not None:
                params["top_p"] = float(form.top_p.data)

            if form.stream.data:
                params["stream"] = form.stream.data

            if form.store.data:
                params["store"] = form.store.data

            if form.metadata.data and form.metadata.data.strip():
                params["metadata"] = json.loads(form.metadata.data)

            # Step 4: Call Provider API
            logger.info(f"Calling {provider_name} API with model: {params['model']}")
            provider = get_provider(
                provider_name, api_key, timeout=None
            )  # No timeout - unlimited

            if not provider:
                raise ValueError(f"Provider '{provider_name}' is not supported")

            # Measure response time
            start_time = time.time()
            response_data = provider.create_response(params)
            end_time = time.time()

            # Calculate latency
            latency_seconds = end_time - start_time

            # Use provider.get_metrics() — normalised across all providers
            provider_metrics = provider.get_metrics(response_data)

            created_raw = response_data.get("created_at") or response_data.get(
                "created"
            )
            metrics = {
                "latency_ms": round(latency_seconds * 1000, 2),
                "latency_seconds": round(latency_seconds, 2),
                "model": provider_metrics.get("model")
                or response_data.get("model", "N/A"),
                "created_at_raw": created_raw,
                "created_at_display": _format_created_at(created_raw),
                "completion_tokens": provider_metrics.get("completion_tokens"),
                "prompt_tokens": provider_metrics.get("prompt_tokens"),
                "total_tokens": provider_metrics.get("total_tokens"),
                "output_parameters": _extract_output_parameters(response_data),
            }

            # Add metrics to response data for template
            response_data["_metrics"] = metrics

            # Add provider information for display
            response_data["_provider"] = {
                "name": provider_name,
                "display_name": available_providers.get(
                    provider_name, provider_name.title()
                ),
            }

            # Use provider.parse_response() to extract content — normalised across all providers
            parsed_content = None
            display_schema = None

            try:
                parsed_response = provider.parse_response(response_data)
                raw_content = parsed_response.get("content", "")

                if raw_content:
                    try:
                        parsed_content = json.loads(raw_content)
                        logger.info("Parsed JSON content from response")
                    except json.JSONDecodeError:
                        parsed_content = raw_content
                        logger.info("Response is plain text")

            except Exception as e:
                logger.warning(f"Error parsing response content: {e}")
                parsed_content = None

            # Auto-detect the appropriate schema for display
            if parsed_content is not None:
                schema = detect_schema(parsed_content)
                display_schema = schema.render_context(parsed_content)
                display_schema["template"] = schema.template_name
                response_data["_display_schema"] = display_schema
                logger.info(f"Using schema: {type(schema).__name__}")

            flash("Response received successfully!", "success")
            logger.info(
                f"Successfully received response from {provider_name} (latency: {latency_seconds:.2f}s)"
            )

        except OnePasswordError as e:
            error_message = f"1Password Error: {str(e)}"
            logger.error(f"1Password error: {e}")
            flash(error_message, "danger")

        except json.JSONDecodeError as e:
            error_message = f"Invalid metadata JSON: {str(e)}"
            logger.error(f"JSON decode error: {e}")
            flash(error_message, "danger")

        except ValueError as e:
            # Catches provider validation errors and configuration errors
            error_message = str(e)
            logger.error(f"Validation error: {e}")
            flash(error_message, "danger")

        except Exception as e:
            # Generic error handler for provider API errors and unexpected issues
            error_type = type(e).__name__
            error_message = f"{provider_name.title()} API Error: {str(e)}"
            logger.exception(f"{error_type} from {provider_name}: {e}")
            flash(error_message, "danger")

    # Compute active upload file info for the template
    _upload_folder = current_app.config.get("UPLOAD_FOLDER", "")
    active_instructions_file = None
    active_image_file = None
    if _upload_folder and os.path.isdir(_upload_folder):
        if os.path.exists(os.path.join(_upload_folder, "active_instructions.md")):
            active_instructions_file = "active_instructions.md"
        active_img = _find_active_image(_upload_folder)
        if active_img:
            active_image_file = os.path.basename(active_img)

    return render_template(
        "index.html",
        form=form,
        provider_form=provider_form,
        selected_provider=selected_provider,
        available_providers=available_providers,
        response_data=response_data,
        error=error_message,
        active_instructions_file=active_instructions_file,
        active_image_file=active_image_file,
    )
