# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Flask app package (`__init__.py`, `routes.py`, `forms.py`).
- `app/providers/`: provider abstraction and registry (`base.py`, `openai.py`, `__init__.py`).
- `app/schemas/`: schema detection/rendering pipeline (`structured.py`, `text.py`).
- `app/services/`: integrations (notably `onepassword.py` for secret lookup).
- `app/templates/` + `app/static/css/`: Jinja views and styles.
- Root files: `run.py` (dev entrypoint, port `5001`), `config.py`, `start.sh`, `test_api.py`.

## Build, Test, and Development Commands
- `python3 -m venv venv && source venv/bin/activate`: local virtualenv setup.
- `pip install -r requirements.txt`: install runtime dependencies.
- `cp .env.example .env`: create local config file.
- `python run.py`: run app locally on `http://127.0.0.1:5001`.
- `./start.sh`: bootstrap venv + install deps + run app.
- `python test_api.py`: manual integration checks (requires running server).

## Coding Style & Naming Conventions
- Python style: 4-space indentation, `snake_case` functions/files, `PascalCase` classes, `UPPER_SNAKE_CASE` constants.
- Prefer type hints for changed/new logic.
- Keep provider-specific API logic in `app/providers/`; keep rendering/format detection in `app/schemas/`.
- Use module-level loggers (`logging.getLogger(__name__)`) and avoid logging secrets.

## Architecture & Agent Workflow Notes
- Provider layer uses a registry/factory pattern (`PROVIDERS`, `get_provider`, `list_providers`).
- Schema rendering uses priority-based detection; first matching schema wins.
- Request flow: selected provider (query/form/session) → dynamic form → 1Password secret fetch (`op://`) → provider call → parsed response → schema-based partial render.
- Session state is used for provider and instruction-path persistence; there is no database.

## Testing Guidelines
- No full automated pytest suite is currently configured.
- Validate changes with `python test_api.py` and targeted manual UI checks.
- When adding tests, follow `test_*.py` naming and keep scope close to changed behavior.

## Extending the System
- Add provider: create `app/providers/<name>.py` subclassing `BaseProvider`, implement core interface, then register in `app/providers/__init__.py` and add `OP_ITEM_REFERENCE_<NAME>` in config and `.env.example`.
- Add schema: create `app/schemas/<name>.py` subclassing `ResponseSchema`, register in `SCHEMAS`, and add matching template partial if needed.

## Commit & Pull Request Guidelines
- Prefer concise imperative commit messages; Conventional Commit prefixes (`feat:`, `fix:`, `chore:`) are encouraged.
- PRs should include summary, linked issue/context, verification steps, and screenshots for UI/template changes.

## Security & Configuration Tips
- Never commit `.env` or raw API keys.
- Secrets must come from 1Password CLI references (`op://...`).
- Keep CSRF protections enabled.
- Watchouts: `test_api.py` uses BeautifulSoup but `beautifulsoup4` is not currently in `requirements.txt`; 1Password CLI must be installed/authenticated.
