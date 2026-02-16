````markdown
# AI Sandbox

Guidelines for AI assistants working on this codebase.

## Project overview

AI Sandbox is a multi-provider AI API client with a unified Flask web UI. Users can call OpenAI (and future Gemini, Anthropic) models through a single interface. API keys are retrieved securely from 1Password CLI — no raw keys in code or environment.

**Stack**: Python 3.8+, Flask 3.0, Flask-WTF, WTForms, python-dotenv, requests. Frontend: Bootstrap 5 + Jinja2.

## Quick commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in 1Password refs and SECRET_KEY

# Run (dev server on 127.0.0.1:5001)
python run.py
# or
./start.sh  # creates venv, installs deps, runs app

# Test (requires app running on port 5001)
python test_api.py
```

There is no automated test suite (pytest, etc.) — `test_api.py` is a manual integration test using `requests` + BeautifulSoup4.

## Project structure

```
ai-sandbox/
├── run.py                    # Entry point → create_app() → dev server on :5001
├── config.py                 # Config classes, 1Password refs, validate()
├── requirements.txt          # 5 core dependencies
├── .env.example              # OP_ITEM_REFERENCE_*, DEFAULT_PROVIDER, SECRET_KEY
├── start.sh                  # Automated venv + install + run
├── test_api.py               # Manual integration tests (CSRF + text/image mode)
└── app/
    ├── __init__.py           # create_app(), blueprint registration, logging
    ├── routes.py             # Single blueprint: index GET/POST (form → API call → response)
    ├── forms.py              # ProviderSelectionForm, ResponsesAPIForm (dynamic per provider)
    ├── providers/            # Provider abstraction layer
    │   ├── __init__.py       # PROVIDERS dict, get_provider(), list_providers()
    │   ├── base.py           # BaseProvider ABC: name, models, form_fields, create_response, parse_response
    │   └── openai.py         # OpenAIProvider (Responses API, 6 models, text/image input)
    ├── schemas/              # Response display system
    │   ├── __init__.py       # SCHEMAS list, detect_schema(), render_response()
    │   ├── base.py           # ResponseSchema ABC: detect, render_context, template_name, priority
    │   ├── structured.py     # StructuredDataSchema — auto-detect tables with totals (priority 10)
    │   └── text.py           # TextSchema (fallback, priority 90), JSONSchema (explicit only, priority 100)
    ├── services/
    │   └── onepassword.py    # OnePasswordService.get_secret(), custom exceptions
    ├── templates/
    │   ├── base.html         # Bootstrap 5 base layout
    │   ├── index.html        # Main UI (provider switch, dynamic form, response display)
    │   └── partials/         # _table.html, _text.html, _json.html
    └── static/css/
        └── style.css         # Custom styles (306 lines)
```

## Architecture and design patterns

**Provider abstraction** (Factory + Strategy): All AI providers implement `BaseProvider` ABC. The `PROVIDERS` dict in `app/providers/__init__.py` acts as a registry. `get_provider(name, api_key)` returns an initialized instance. Each provider defines its own models, form fields, request/response handling, and error types.

**Schema detection** (Chain of Responsibility): Response data is passed through registered schemas by priority order. First match wins. `StructuredDataSchema` (priority 10) detects lists-of-dicts for table rendering. `TextSchema` (priority 90) is the fallback. Schemas can be forced via `force_schema` parameter.

**Request flow**:
1. Provider selected from query/form/session → persisted in `session['selected_provider']`
2. Forms generated dynamically from provider's model list and form fields
3. API key fetched from 1Password CLI via `op://` reference
4. Provider's `create_response(params)` called with validated parameters
5. Response parsed → schema detected → rendered via appropriate Jinja2 partial

## Configuration

- `config.py` defines `Config`, `DevelopmentConfig`, `ProductionConfig` classes
- 1Password references per provider: `OP_ITEM_REFERENCE_OPENAI`, `OP_ITEM_REFERENCE_GEMINI`, `OP_ITEM_REFERENCE_ANTHROPIC`
- Legacy `OP_ITEM_REFERENCE` maps to OpenAI for backward compatibility
- `Config.validate()` runs at startup (checks default provider has valid `op://` ref)
- `DEFAULT_PROVIDER` env var sets the initial provider (default: `openai`)

## Code conventions

### Naming
- **Files**: `snake_case.py`
- **Classes**: `PascalCase` (e.g., `BaseProvider`, `StructuredDataSchema`)
- **Functions/methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `PROVIDERS`, `SCHEMAS`, `API_BASE_URL`)
- **Private methods**: prefixed with underscore (e.g., `_encode_image`)

### Style
- 4-space indentation
- Type hints in function signatures (`Dict`, `List`, `Any`, `Optional`, `Tuple`)
- Module-level `logger = logging.getLogger(__name__)` for all logging
- Imports ordered: standard library, third-party, local
- Docstrings on modules and public functions

### Error handling
- Provider-specific exception classes (e.g., `OpenAIAuthenticationError`, `OpenAIRateLimitError`)
- 1Password errors have custom exceptions (`OnePasswordCLINotFound`, `OnePasswordAuthenticationError`, etc.)
- Errors flashed to user with `flash(message, 'danger')`
- No raw API keys or 1Password refs in logs or error messages

### Security
- CSRF protection via Flask-WTF on all forms (always enabled)
- API keys only from 1Password CLI, never stored in code or raw env vars
- Server-side validation for all user inputs
- Metadata field validated as JSON object in `validate_metadata`

### Templates
- Bootstrap 5 with Jinja2 block extension pattern
- Flash messages with `success`/`danger` categories
- Response rendered via schema-specific partials in `templates/partials/`
- Provider and performance metrics displayed alongside responses

## Adding a new AI provider

1. Create `app/providers/<name>.py` — subclass `BaseProvider`, implement: `name`, `models`, `form_fields`, `create_response(params)`, `parse_response(response)`, `validate_parameters(params)`
2. Register in `app/providers/__init__.py` — add to `PROVIDERS` dict
3. Add `OP_ITEM_REFERENCE_<UPPER_NAME>` to `config.py` and `.env.example`
4. No UI changes needed — provider dropdown and model list are data-driven

## Adding a new response schema

1. Create class in `app/schemas/` extending `ResponseSchema` — implement `detect(data)`, `render_context(data)`, `template_name`, and optionally `priority`
2. Register in `app/schemas/__init__.py` → `SCHEMAS` list (order matters)
3. Add corresponding partial template in `app/templates/partials/` if needed

## Things to watch out for

- The app runs on **port 5001** (hardcoded in `run.py`)
- `test_api.py` requires `beautifulsoup4` which is **not** in `requirements.txt`
- 1Password CLI (`op`) must be installed and authenticated for API key retrieval
- `onepassword.py` uses subprocess with no timeout to allow biometric auth prompts
- No database — all state is in Flask sessions (provider selection, system instruction file path)
- No CI/CD pipeline configured

