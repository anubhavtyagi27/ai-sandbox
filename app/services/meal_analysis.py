"""
Meal Analysis Service

Orchestrates meal analysis using GeminiClient for HTTP calls.
Handles meal-specific prompt construction, retry logic, and
response schema validation on top of the client layer.

Setup:
1) Configure `OP_ITEM_REFERENCE_GEMINI` in `.env`
2) Ensure 1Password CLI is installed and authenticated
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.services.gemini_client import GeminiClient, GeminiClientError
from app.services.onepassword import OnePasswordError, OnePasswordService
from config import Config

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"

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


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class MealAnalysisError(Exception):
    """Base exception for meal analysis errors."""


class MealAnalysisAuthenticationError(MealAnalysisError):
    """Raised when API key retrieval or authentication fails."""


class MealAnalysisAPIError(MealAnalysisError):
    """Raised when the API call fails."""


class MealAnalysisParseError(MealAnalysisError):
    """Raised when the response cannot be parsed into the expected schema."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class MealAnalysisService:
    """Orchestrates meal analysis via GeminiClient."""

    def _get_client(self) -> GeminiClient:
        try:
            op_reference = Config.get_provider_reference("gemini")
            api_key = OnePasswordService.get_secret(op_reference)
        except OnePasswordError as exc:
            logger.error("Failed retrieving Gemini key from 1Password: %s", exc)
            raise MealAnalysisAuthenticationError(
                "Failed to retrieve Gemini API key"
            ) from exc
        except ValueError as exc:
            logger.error("Gemini provider reference misconfigured: %s", exc)
            raise MealAnalysisAuthenticationError(
                "Gemini provider is not configured"
            ) from exc
        return GeminiClient(api_key=api_key)

    def analyse_meal_from_text(self, description: str) -> Dict[str, Any]:
        if not description or not description.strip():
            return {
                "success": False,
                "error": "Could not identify food items in the provided input.",
            }

        params = {
            "model": GEMINI_MODEL,
            "instructions": SYSTEM_PROMPT,
            "input": (
                "Analyse this meal description and return nutrition JSON: "
                f"{description.strip()}"
            ),
        }
        return self._execute_with_retry(params)

    def analyse_meal_from_image(
        self, base64_image: str, mime_type: str
    ) -> Dict[str, Any]:
        if not base64_image or not base64_image.strip():
            return {
                "success": False,
                "error": "Could not identify food items in the provided input.",
            }

        # Pass pre-built Gemini contents for the image+text multipart payload
        params = {
            "model": GEMINI_MODEL,
            "instructions": SYSTEM_PROMPT,
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
        return self._execute_with_retry(params)

    def _execute_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        from app.providers.gemini import GeminiProvider

        client = self._get_client()

        for attempt in range(2):
            if attempt == 1:
                params = self._with_strict_retry_instruction(params)

            try:
                raw = client.create_response(params)
            except GeminiClientError as exc:
                raise MealAnalysisAPIError(str(exc)) from exc

            try:
                parsed = self._extract_and_validate(client._provider, raw)
                return parsed
            except MealAnalysisParseError as exc:
                logger.warning(
                    "Meal analysis parse/validation failed (attempt %s/2): %s",
                    attempt + 1,
                    str(exc),
                )
                if attempt == 1:
                    raise

        raise MealAnalysisParseError("Failed to parse Gemini response after retry")

    def _extract_and_validate(self, provider, raw: Dict[str, Any]) -> Dict[str, Any]:
        parsed_response = provider.parse_response(raw)
        text_body = parsed_response.get("content", "")

        if not text_body:
            raise MealAnalysisParseError("Gemini response contained empty text")

        cleaned = self._strip_code_fences(text_body)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise MealAnalysisParseError("Model output is not valid JSON") from exc

        self._validate_result_shape(data)
        return data

    def _with_strict_retry_instruction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        updated = json.loads(json.dumps(params))
        updated["instructions"] = (
            updated.get("instructions", "") + "\n\n" + STRICT_JSON_PROMPT
        )
        return updated

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
            raise MealAnalysisParseError("Parsed output must be a JSON object")

        if data.get("success") is False:
            if not isinstance(data.get("error"), str) or not data["error"].strip():
                raise MealAnalysisParseError(
                    "Failure shape must include non-empty string error"
                )
            return

        if data.get("success") is not True:
            raise MealAnalysisParseError("Output must include success boolean")

        missing = [field for field in SUCCESS_FIELDS if field not in data]
        if missing:
            raise MealAnalysisParseError(
                f"Success shape missing required fields: {', '.join(sorted(missing))}"
            )

        items = data.get("identified_items")
        if not isinstance(items, list):
            raise MealAnalysisParseError("identified_items must be a list")

        totals = data.get("totals")
        if not isinstance(totals, dict):
            raise MealAnalysisParseError("totals must be an object")

        for item in items:
            if not isinstance(item, dict):
                raise MealAnalysisParseError("each identified item must be an object")
            self._validate_macro_fields(item, context="identified item")

        self._validate_macro_fields(totals, context="totals")

    def _validate_macro_fields(self, payload: Dict[str, Any], context: str) -> None:
        for key in MACRO_FIELDS:
            if key not in payload:
                raise MealAnalysisParseError(f"{context} missing {key}")
            if not isinstance(payload[key], (int, float)):
                raise MealAnalysisParseError(f"{context} field {key} must be numeric")
