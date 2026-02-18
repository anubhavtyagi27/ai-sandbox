"""
Gemini Meal Analysis Service

Setup:
1) Configure `OP_ITEM_REFERENCE_GEMINI` in `.env` / `.env.example`
2) Ensure 1Password CLI is installed and authenticated
3) This service calls Gemini REST API (`gemini-2.5-flash`) via `requests`
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import requests

from config import Config
from app.services.onepassword import OnePasswordError, OnePasswordService

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.5-flash"
GENERATE_CONTENT_PATH = f"/models/{GEMINI_MODEL}:generateContent"

SUCCESS_FIELDS = {
    "success",
    "meal_name",
    "identified_items",
    "totals",
    "confidence",
    "notes",
}

MACRO_FIELDS = ("calories", "protein_g", "carbs_g", "fat_g", "fibre_g")

SYSTEM_PROMPT = (
    "You are a nutrition expert specializing in Indian cuisine across regions "
    "(North Indian, South Indian, Bengali, Gujarati, Maharashtrian, Punjabi, etc.). "
    "Understand Hindi, English, and Hinglish meal descriptions. "
    "Interpret common Indian portion descriptors such as katori, vati, cup, piece, handful, and glass. "
    "Estimate calories/macros realistically and account for typical home-cooked vs restaurant differences where relevant. "
    "Always return valid JSON only, with no markdown and no prose outside JSON. "
    "If items are ambiguous, make a reasonable assumption and document it in notes. "
    "If no food is detected, return exactly this shape: "
    '{"success": false, "error": "Could not identify food items in the provided input."}'
)

STRICT_JSON_PROMPT = (
    "Your previous response was not valid JSON for the required schema. "
    "Return ONLY valid JSON with no markdown, no comments, and no extra keys."
)


class GeminiServiceError(Exception):
    """Base exception for Gemini meal analysis service."""


class GeminiAuthenticationError(GeminiServiceError):
    """Raised when auth/key retrieval fails."""


class GeminiAPIError(GeminiServiceError):
    """Raised when Gemini API call fails."""


class GeminiResponseParseError(GeminiServiceError):
    """Raised when Gemini response cannot be parsed into expected JSON shape."""


class GeminiMealAnalysisService:
    """Service for meal analysis via Gemini REST API."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.endpoint = f"{GEMINI_API_BASE}{GENERATE_CONTENT_PATH}"

    def analyse_meal_from_text(self, description: str) -> Dict[str, Any]:
        if not description or not description.strip():
            return {
                "success": False,
                "error": "Could not identify food items in the provided input.",
            }

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Analyse this meal description and return nutrition JSON: "
                                f"{description.strip()}"
                            )
                        }
                    ],
                }
            ],
        }
        return self._execute_with_retry(payload)

    def analyse_meal_from_image(self, base64_image: str, mime_type: str) -> Dict[str, Any]:
        if not base64_image or not base64_image.strip():
            return {
                "success": False,
                "error": "Could not identify food items in the provided input.",
            }

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_image.strip(),
                            }
                        },
                        {
                            "text": (
                                "Identify food items from this image and return nutrition JSON "
                                "using the required schema."
                            )
                        },
                    ],
                }
            ],
        }
        return self._execute_with_retry(payload)

    def _execute_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        api_key = self._get_api_key()

        for attempt in range(2):
            if attempt == 1:
                payload = self._with_strict_retry_instruction(payload)

            raw = self._call_gemini(payload, api_key)
            try:
                parsed = self._extract_and_parse(raw)
                self._validate_result_shape(parsed)
                return parsed
            except GeminiResponseParseError as exc:
                logger.warning(
                    "Gemini response parse validation failed (attempt %s/2): %s",
                    attempt + 1,
                    str(exc),
                )
                if attempt == 1:
                    raise

        raise GeminiResponseParseError("Failed to parse Gemini response after retry")

    def _get_api_key(self) -> str:
        try:
            op_reference = Config.get_provider_reference("gemini")
            return OnePasswordService.get_secret(op_reference)
        except OnePasswordError as exc:
            logger.error("Failed retrieving Gemini key from 1Password: %s", str(exc))
            raise GeminiAuthenticationError("Failed to retrieve Gemini API key") from exc
        except ValueError as exc:
            logger.error("Gemini provider reference misconfigured: %s", str(exc))
            raise GeminiAuthenticationError("Gemini provider is not configured") from exc

    def _call_gemini(self, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}

        try:
            response = self.session.post(
                self.endpoint,
                headers=headers,
                params=params,
                json=payload,
                timeout=60,
            )
        except requests.RequestException as exc:
            logger.error("Gemini request failed before response: %s", str(exc))
            raise GeminiAPIError("Gemini API request failed") from exc

        if response.status_code != 200:
            body = response.text[:500]
            logger.error(
                "Gemini API error status=%s body=%s", response.status_code, body
            )
            raise GeminiAPIError(
                f"Gemini API returned status {response.status_code}."
            )

        try:
            return response.json()
        except ValueError as exc:
            logger.error("Gemini API returned non-JSON response")
            raise GeminiAPIError("Gemini API returned invalid JSON response") from exc

    def _with_strict_retry_instruction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        updated = json.loads(json.dumps(payload))
        instruction = updated.setdefault("system_instruction", {}).setdefault("parts", [])
        instruction.append({"text": STRICT_JSON_PROMPT})
        return updated

    def _extract_and_parse(self, response_json: Dict[str, Any]) -> Dict[str, Any]:
        candidates = response_json.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise GeminiResponseParseError("Gemini response missing candidates")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        text_chunks: List[str] = []
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text_chunks.append(part["text"])

        text_body = "\n".join(text_chunks).strip()
        if not text_body:
            raise GeminiResponseParseError("Gemini response contained empty text")

        cleaned = self._strip_code_fences(text_body)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GeminiResponseParseError("Model output is not valid JSON") from exc

    def _strip_code_fences(self, value: str) -> str:
        content = value.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content

    def _validate_result_shape(self, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise GeminiResponseParseError("Parsed output must be a JSON object")

        if data.get("success") is False:
            if not isinstance(data.get("error"), str) or not data["error"].strip():
                raise GeminiResponseParseError(
                    "Failure shape must include non-empty string error"
                )
            return

        if data.get("success") is not True:
            raise GeminiResponseParseError("Output must include success boolean")

        missing = [field for field in SUCCESS_FIELDS if field not in data]
        if missing:
            raise GeminiResponseParseError(
                f"Success shape missing required fields: {', '.join(sorted(missing))}"
            )

        items = data.get("identified_items")
        if not isinstance(items, list):
            raise GeminiResponseParseError("identified_items must be a list")

        totals = data.get("totals")
        if not isinstance(totals, dict):
            raise GeminiResponseParseError("totals must be an object")

        for item in items:
            if not isinstance(item, dict):
                raise GeminiResponseParseError("each identified item must be an object")
            self._validate_macro_fields(item, context="identified item")

        self._validate_macro_fields(totals, context="totals")

    def _validate_macro_fields(self, payload: Dict[str, Any], context: str) -> None:
        for key in MACRO_FIELDS:
            if key not in payload:
                raise GeminiResponseParseError(f"{context} missing {key}")
            if not isinstance(payload.get(key), (int, float)):
                raise GeminiResponseParseError(
                    f"{context} field {key} must be numeric"
                )


_service = GeminiMealAnalysisService()


def analyse_meal_from_text(description: str) -> Dict[str, Any]:
    """Analyse meal nutrition from natural language text."""
    return _service.analyse_meal_from_text(description)


def analyse_meal_from_image(base64_image: str, mime_type: str) -> Dict[str, Any]:
    """Analyse meal nutrition from a base64 image payload."""
    return _service.analyse_meal_from_image(base64_image, mime_type)
