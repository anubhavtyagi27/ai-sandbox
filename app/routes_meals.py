import logging
import time
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from app.services.gemini_client import (
    GeminiServiceError,
    analyse_meal_from_image,
    analyse_meal_from_text,
)

bp = Blueprint("meals", __name__, url_prefix="/api/meals")
logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


def _json_error(message: str, status_code: int):
    return jsonify({"success": False, "error": message}), status_code


def _request_json() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@bp.route("/analyse/text", methods=["POST"])
def analyse_text():
    start = time.perf_counter()
    logger.info("POST /api/meals/analyse/text hit")

    try:
        body = _request_json()
        description = body.get("description")

        if not isinstance(description, str) or not description.strip():
            return _json_error("Field 'description' is required.", 400)

        result = analyse_meal_from_text(description.strip())
        return jsonify(result), 200

    except GeminiServiceError as exc:
        logger.error("Gemini service error on text analysis: %s", str(exc))
        return _json_error("Failed to analyse meal text via Gemini.", 500)
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error in text analysis endpoint: %s", str(exc))
        return _json_error("Unexpected server error while analysing meal text.", 500)
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info("POST /api/meals/analyse/text completed in %sms", elapsed_ms)


@bp.route("/analyse/image", methods=["POST"])
def analyse_image():
    start = time.perf_counter()
    logger.info("POST /api/meals/analyse/image hit")

    try:
        body = _request_json()
        image_data = body.get("image")
        mime_type = body.get("mimeType")

        if not isinstance(image_data, str) or not image_data.strip():
            return _json_error("Field 'image' is required.", 400)

        if not isinstance(mime_type, str) or not mime_type.strip():
            return _json_error("Field 'mimeType' is required.", 400)

        mime_type = mime_type.strip().lower()
        if mime_type not in ALLOWED_MIME_TYPES:
            return _json_error(
                "Field 'mimeType' must be one of: image/jpeg, image/png.", 400
            )

        result = analyse_meal_from_image(image_data.strip(), mime_type)
        return jsonify(result), 200

    except GeminiServiceError as exc:
        logger.error("Gemini service error on image analysis: %s", str(exc))
        return _json_error("Failed to analyse meal image via Gemini.", 500)
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error in image analysis endpoint: %s", str(exc))
        return _json_error("Unexpected server error while analysing meal image.", 500)
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info("POST /api/meals/analyse/image completed in %sms", elapsed_ms)
