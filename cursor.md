# AI Sandbox — Project Context

Use this when working on new features or refactors so behavior stays consistent with the existing codebase.

## What the project is

- **Name**: AI Sandbox (kvj worktree)
- **Purpose**: Multi-provider AI API client — unified web UI to call OpenAI, (future: Gemini, Anthropic). API keys come from 1Password CLI; nothing is stored in code or env as raw keys.
- **Stack**: Python 3.8+, Flask 3, Flask-WTF, WTForms, python-dotenv, requests. Frontend: Bootstrap 5, Jinja2, minimal custom CSS.
- **Entry**: `run.py` → `create_app()` in `app/__init__.py` → dev server on `127.0.0.1:5001` (debug from config). Production should use a WSGI server (e.g. Gunicorn).

## Layout (important paths)

```
kvj/
├── run.py                 # Entry point
├── config.py              # Config classes, get_config(), 1Password refs, validate()
├── requirements.txt
├── .env.example            # OP_ITEM_REFERENCE_*, DEFAULT_PROVIDER, SECRET_KEY, FLASK_ENV
├── start.sh                # Venv + pip install + run
├── test_api.py             # Requests + BeautifulSoup; CSRF + text/image mode
└── app/
    ├── __init__.py         # create_app(), blueprint registration, logging
    ├── routes.py           # Single blueprint, index GET/POST (form + provider + API call)
    ├── forms.py            # ProviderSelectionForm, ResponsesAPIForm (provider-aware, dynamic model choices)
    ├── providers/          # Provider abstraction
    │   ├── __init__.py     # PROVIDERS dict, get_provider(), list_providers()
    │   ├── base.py         # BaseProvider (ABC): name, models, form_fields, create_response, parse_response, validate_parameters
    │   └── openai.py       # OpenAIProvider (Responses API)
    ├── schemas/            # Response display
    │   ├── __init__.py     # SCHEMAS list, detect_schema(), render_response()
    │   ├── base.py         # ResponseSchema (ABC): detect, render_context, template_name, priority
    │   ├── structured.py   # StructuredDataSchema (tables, totals)
    │   └── text.py         # TextSchema, JSONSchema
    ├── services/
    │   └── onepassword.py  # OnePasswordService.get_secret(op_reference), exceptions
    ├── templates/          # base.html, index.html, partials/_table.html, _text.html, _json.html
    └── static/css/style.css
```

## Configuration and secrets

- **Config**: `config.py` — `Config` base, `DevelopmentConfig` / `ProductionConfig`. `get_config()` uses `FLASK_ENV`. `Config.validate()` runs at startup (default provider must have valid `op://` ref; production requires non-default `SECRET_KEY`).
- **1Password**: Per-provider refs: `OP_ITEM_REFERENCE_OPENAI`, `OP_ITEM_REFERENCE_GEMINI`, `OP_ITEM_REFERENCE_ANTHROPIC`. Legacy `OP_ITEM_REFERENCE` maps to OpenAI. `Config.get_provider_reference(provider)` returns the ref or raises.
- **Default provider**: `DEFAULT_PROVIDER` (e.g. `openai`). Session stores `selected_provider` and optional `system_instruction_file`.

## Request flow (index)

1. **Provider**: From query, form, or session; persist in `session['selected_provider']`.
2. **Forms**: `ProviderSelectionForm` (provider dropdown from `list_providers()`), `ResponsesAPIForm(provider_name=...)` (model choices from provider's `models`).
3. **System instruction**: Optional file path (session-persisted); read markdown from disk and pass as `params['instructions']`.
4. **API key**: `OnePasswordService.get_secret(Config.get_provider_reference(selected_provider))`.
5. **Params**: model, input, input_mode (text/image/voice), optional image_path, instructions, max_tokens, temperature, top_p, stream, store, metadata (JSON).
6. **Call**: `get_provider(name, api_key, timeout=None)` → `provider.create_response(params)`.
7. **Response**: Provider returns raw response; routes add `_metrics` (latency, tokens, etc.) and `_provider`; parse `output` → text/JSON, then `detect_schema(parsed_content)` → `render_context` + `template_name` → `_display_schema` for template.
8. **Templates**: `index.html` uses `response_data._display_schema.template` and context; partials: `_table.html`, `_text.html`, `_json.html`.

## Adding a new AI provider

1. **Implement** in `app/providers/<name>.py`: subclass `BaseProvider`, implement `name`, `models`, `form_fields`, `create_response`, `parse_response`, `validate_parameters`. Use provider-specific exceptions if desired (routes show generic "Provider API Error").
2. **Register** in `app/providers/__init__.py`: add to `PROVIDERS` dict and export.
3. **Config**: Add `OP_ITEM_REFERENCE_<UPPER_NAME>` in `config.py` and in `.env.example`; no raw keys.
4. **UI**: Provider dropdown and model list are driven by `list_providers()` and provider's `models`; no extra form changes needed unless the provider needs custom fields (then extend `ResponsesAPIForm` or provider-specific form logic).

## Response schemas

- **Detection**: `detect_schema(data)` in `app/schemas/__init__.py` runs registered `SCHEMAS` by `priority`; first matching schema wins. Fallback: `TextSchema`. Optional `force_schema` for 'json'/'text'/'structured'.
- **Adding a schema**: New class in `app/schemas/` extending `ResponseSchema` (implement `detect`, `render_context`, `template_name`; optionally `priority`). Register in `SCHEMAS` (order/priority). Add partial in `app/templates/partials/` if new template.

## Conventions to keep

- **Logging**: Module-level `logger = logging.getLogger(__name__)`; use in routes, providers, services. Startup and errors logged in app.
- **Errors**: 1Password errors → flash danger and user-facing message. Provider/validation errors → flash and log. No raw API keys or 1Password refs in logs.
- **Forms**: Flask-WTF, CSRF enabled. Validate required input per mode (e.g. text vs image). Metadata field: optional JSON object validated in `validate_metadata`.
- **Templates**: Bootstrap 5; flash messages with categories; response rendered via schema partials; provider and metrics shown with response.
- **Tests**: `test_api.py` assumes app on 5001; gets CSRF from GET, posts for text and image mode; checks for success message or "Response Content". Dependencies: `requests`, `beautifulsoup4` (not in requirements.txt; add if running tests in CI).

## Quick reference

- **Run**: `python run.py` or `./start.sh`.
- **Env**: Copy `.env.example` to `.env`; set 1Password refs and `SECRET_KEY`.
- **Provider list**: `app/providers/__init__.py` → `PROVIDERS` / `list_providers()`.
- **Schema list**: `app/schemas/__init__.py` → `SCHEMAS` / `detect_schema()`.

When adding features, follow the existing provider and schema patterns so the app stays consistent and extensible.
