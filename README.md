# AI Sandbox

A multi-provider AI API client for testing and experimenting with different AI models through a simple web interface. Securely manage API keys via 1Password CLI.

## Overview

AI Sandbox is a Flask-based web application that provides a unified interface for calling various AI provider APIs (OpenAI, Google Gemini, Anthropic Claude, etc.). It features dynamic form generation based on provider-specific parameters, flexible response display with auto-detection of data schemas, and secure credential management through 1Password CLI integration.

## Features

### Core Functionality
- 🤖 **Multi-Provider Support**: Currently supports OpenAI (Gemini & Anthropic ready to add)
- 🔐 **Secure API Key Management**: Retrieves API keys from 1Password CLI via biometric authentication (never stored locally)
- 🎯 **Dynamic Provider Selection**: Switch between AI providers through intuitive UI dropdown
- 📊 **Smart Response Display**: Auto-detects response format (structured data tables, plain text, JSON)
- ⚡ **Performance Metrics**: Real-time latency, token usage, and provider tracking

### Architecture Highlights
- 🏗️ **Provider Abstraction Layer**: Extensible architecture for adding new AI providers
- 🔄 **Schema Detection System**: Automatically renders responses in optimal format
- 📝 **Dynamic Form Generation**: Form fields adapt to selected provider's capabilities
- 🎨 **Flexible Templates**: Modular partial templates for different response types
- 💾 **Session Persistence**: Remembers provider selection and system instruction paths

### User Experience
- 🛡️ **Form Validation**: Client and server-side validation for all inputs
- 📝 **System Instructions**: Load prompts from markdown files with session persistence
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- 🎨 **Provider Context**: Clear indication of which provider generated each response
- 🚨 **Generic Error Handling**: Provider-agnostic error messages and logging

## Supported Providers

| Provider | Status | Models |
|----------|--------|--------|
| **OpenAI** | ✅ Active | GPT-4o, o1, o1-mini |
| **Google Gemini** | 🔜 Planned | Coming soon |
| **Anthropic Claude** | 🔜 Planned | Coming soon |

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **1Password CLI**: [Installation Guide](https://developer.1password.com/docs/cli/get-started/)
- **API Keys**: Stored in your 1Password vault for each provider you want to use

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/anubhavtyagi27/ai-sandbox.git
cd ai-sandbox
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Set Up 1Password

#### Store Your API Keys in 1Password

1. Open 1Password
2. Create items for each AI provider's API key
3. Note the reference paths in format: `op://vault-name/item-name/field-name`

Example 1Password items:
- OpenAI: `op://Projects/OpenAI API Key/credential`
- Gemini: `op://Projects/Google Gemini Key/credential`
- Anthropic: `op://Projects/Anthropic Key/credential`

#### Test 1Password CLI

Verify you can retrieve a key:

```bash
op read "op://Projects/OpenAI API Key/credential"
```

You'll be prompted to authenticate via biometrics or password on first use.

### 2. Configure Environment Variables

#### Create .env File

```bash
cp .env.example .env
```

#### Edit .env File

```bash
# Provider API Keys (1Password references)
OP_ITEM_REFERENCE_OPENAI=op://Projects/OpenAI API Key/credential
# OP_ITEM_REFERENCE_GEMINI=op://Projects/Google Gemini Key/credential
# OP_ITEM_REFERENCE_ANTHROPIC=op://Projects/Anthropic Key/credential

# Default provider
DEFAULT_PROVIDER=openai

# Flask configuration
SECRET_KEY=your-generated-secret-key-here
FLASK_ENV=development
```

#### Generate SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as your `SECRET_KEY` in `.env`.

## Running the Application

### Start the Flask Server

```bash
python run.py
```

You should see output like:

```
2026-02-12 - app - INFO - Starting Flask app in development mode
 * Running on http://127.0.0.1:5001
```

### Access the Application

Open your browser and navigate to:

```
http://localhost:5001
```

## Usage

### Basic Workflow

1. **Select Provider** (currently OpenAI, more coming soon)
2. **Choose Model**: Select from available models for the provider
3. **Enter Input**: Type your prompt or message
4. **Optional: System Instructions**: Provide a path to a markdown file with system prompts
5. **Optional Parameters**: Configure temperature, max tokens, etc.
6. **Submit Request**: View real-time response with performance metrics

### System Instructions

You can load system instructions from a markdown file:

1. Create a markdown file with your system prompt (e.g., `/path/to/instructions.md`)
2. Enter the file path in the "System Instruction File Path" field
3. The path persists across requests for convenience

### Response Display

AI Sandbox automatically detects the response format:

- **Structured Data** (e.g., nutrition tables): Displays as formatted table with totals
- **Plain Text**: Shows in readable text format
- **JSON**: Falls back to syntax-highlighted JSON view

## Project Structure

```
ai-sandbox/
├── app/
│   ├── __init__.py              # Flask app factory with blueprint registration
│   ├── routes.py                # Route handlers with provider selection
│   ├── forms.py                 # Dynamic form generation (provider-aware)
│   │
│   ├── providers/               # 🔥 Provider abstraction layer
│   │   ├── __init__.py          # Provider registry and factory
│   │   ├── base.py              # BaseProvider abstract class
│   │   ├── openai.py            # OpenAI implementation
│   │   ├── gemini.py            # (Future) Google Gemini
│   │   └── anthropic.py         # (Future) Anthropic Claude
│   │
│   ├── schemas/                 # 🔥 Response schema detection
│   │   ├── __init__.py          # Schema registry and detection
│   │   ├── base.py              # ResponseSchema abstract class
│   │   ├── structured.py        # Structured data (tables)
│   │   └── text.py              # Text and JSON responses
│   │
│   ├── services/
│   │   └── onepassword.py       # 1Password CLI integration
│   │
│   ├── templates/
│   │   ├── base.html            # Base template with navigation
│   │   ├── index.html           # Main interface with provider UI
│   │   └── partials/            # 🔥 Modular response templates
│   │       ├── _table.html      # Structured data table
│   │       ├── _text.html       # Plain text display
│   │       └── _json.html       # JSON syntax highlighting
│   │
│   └── static/css/
│       └── style.css            # Custom styles
│
├── config.py                    # Multi-provider configuration
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

🔥 = New in v2.0 (multi-provider architecture)

## Security

- ✅ API keys **never** stored in project files or code
- ✅ All keys retrieved on-demand from 1Password CLI
- ✅ Biometric authentication for key retrieval
- ✅ `.env` file excluded from version control
- ✅ CSRF protection on all forms
- ✅ Input validation and sanitization

## Development

### Adding a New Provider

To add support for a new AI provider:

1. Create provider implementation in `app/providers/`
2. Add API key reference to `config.py`
3. Update `.env.example` with provider configuration
4. Register provider in `app/providers/__init__.py`

See the [Architecture Guide](#architecture) for detailed instructions.

### Running Tests

```bash
pytest tests/
```

## Troubleshooting

### 1Password Issues

**Error**: `1Password CLI not found`
- Install from [1password.com/downloads/command-line](https://1password.com/downloads/command-line/)
- Verify installation: `op --version`

**Error**: `Not authenticated with 1Password`
- Run: `op signin`
- Follow biometric authentication prompts

**Error**: `Item not found`
- Verify item exists in 1Password
- Check `OP_ITEM_REFERENCE_OPENAI` (or other provider) in `.env`
- Ensure format: `op://vault/item/field`
- Test manually: `op read "op://vault/item/field"`

**Error**: `No 1Password reference configured for provider`
- Add missing `OP_ITEM_REFERENCE_[PROVIDER]` to `.env`
- Example: `OP_ITEM_REFERENCE_OPENAI=op://Projects/OpenAI Key/credential`

### Provider Issues

**Error**: `Provider 'xyz' is not supported`
- Check provider name spelling in dropdown
- Verify provider is registered in `app/providers/__init__.py`
- Ensure provider class is imported correctly

**Error**: `[Provider] API Error: ...`
- Check API key is correct in 1Password
- Verify provider API endpoint is accessible
- Check provider's service status page
- Review error message for specific issue

**Invalid API Key** (401):
- Verify key in 1Password
- Test: `op read "your-reference-path"`
- Ensure key has correct permissions for API

**Rate Limit** (429):
- Wait before retrying
- Check provider's rate limits documentation
- Consider upgrading API tier

### Application Issues

**Port in Use**:
- Change port in `run.py` (default: 5001)
- Or kill existing process: `lsof -ti:5001 | xargs kill`

**Provider dropdown not showing**:
- Check `list_providers()` returns providers
- Verify PROVIDERS dict in `app/providers/__init__.py`
- Clear browser cache and reload

**Form not updating after provider switch**:
- Ensure JavaScript is enabled
- Check browser console for errors
- Verify provider form submission works

**Schema detection not working**:
- Check data format returned by provider
- Verify `parse_response()` returns correct structure
- Add logging to `detect_schema()` for debugging

## Architecture

AI Sandbox uses a three-layer architecture for extensibility and maintainability:

### 1. Provider Abstraction Layer (`app/providers/`)

All AI providers implement the `BaseProvider` abstract class:

```python
class BaseProvider(ABC):
    @property
    def name(self) -> str: ...           # Display name

    @property
    def models(self) -> List[Tuple]: ... # Available models

    def create_response(params): ...      # API call
    def parse_response(response): ...     # Response parsing
    def validate_parameters(params): ...  # Parameter validation
```

**Current Implementations:**
- `OpenAIProvider` - OpenAI Responses API (GPT-4o, o1, o1-mini)
- Ready to add: `GeminiProvider`, `AnthropicProvider`

### 2. Schema Detection System (`app/schemas/`)

Automatically detects response format and renders appropriately:

- **StructuredDataSchema**: Tables with automatic totals for numeric columns
- **TextSchema**: Plain text responses with formatting preservation
- **JSONSchema**: Syntax-highlighted JSON for complex data

Detection happens automatically based on response content structure.

### 3. Dynamic Form Generation (`app/forms.py`)

Forms adapt to selected provider:
- Model dropdown populated from provider metadata
- Provider-specific parameters automatically included
- Form validation based on provider requirements

### Key Design Patterns

- **Factory Pattern**: Provider registry for dynamic instantiation
- **Template Method**: BaseProvider defines interface, subclasses implement
- **Strategy Pattern**: Schema detection chooses rendering strategy
- **Session Pattern**: Provider selection persists across requests

## Adding a New Provider

Want to add support for Google Gemini, Anthropic Claude, or another AI provider? Follow these steps:

### Step 1: Create Provider Implementation

Create `app/providers/your_provider.py`:

```python
from typing import Dict, List, Any, Tuple, Optional
from .base import BaseProvider

class YourProvider(BaseProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key)
        # Provider-specific initialization

    @property
    def name(self) -> str:
        return "Your Provider Name"

    @property
    def models(self) -> List[Tuple[str, str]]:
        return [
            ('model-id-1', 'Model Display Name 1'),
            ('model-id-2', 'Model Display Name 2'),
        ]

    def create_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Make API call to your provider
        # Return raw response
        pass

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        # Parse provider's response format
        return {
            'content': extracted_content,
            'metadata': {...}
        }

    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        # Validate params before API call
        if 'model' not in params:
            return False, "Model is required"
        return True, None
```

### Step 2: Register Provider

Add to `app/providers/__init__.py`:

```python
from .your_provider import YourProvider

PROVIDERS: Dict[str, Type[BaseProvider]] = {
    'openai': OpenAIProvider,
    'your_provider': YourProvider,  # Add here
}
```

### Step 3: Configure API Key

Add to `.env`:

```bash
OP_ITEM_REFERENCE_YOUR_PROVIDER=op://vault/Your Provider Key/credential
```

### Step 4: Test

Start the app and select your provider from the dropdown. The UI automatically updates with your provider's models and parameters!

### Optional: Custom Error Handling

Define provider-specific exceptions:

```python
class YourProviderError(Exception):
    pass

class YourProviderAuthError(YourProviderError):
    pass
```

The generic error handler in `routes.py` will catch these automatically.

## Schema Detection System

AI Sandbox automatically detects the format of AI responses and renders them optimally.

### How It Works

1. **Response Parsing**: Provider returns data from API
2. **Schema Detection**: `detect_schema()` analyzes the data structure
3. **Template Selection**: Appropriate partial template is chosen
4. **Rendering**: Data is displayed with the optimal format

### Available Schemas

#### StructuredDataSchema
- **Detects**: Lists of dictionaries with consistent keys
- **Renders**: Formatted tables with sortable columns
- **Features**:
  - Automatic totals for numeric columns (calories, price, etc.)
  - Smart column ordering (name fields first)
  - Responsive table design

**Example Use Cases:**
- Nutrition tables
- Product comparisons
- Data analysis results
- Any tabular data

#### TextSchema
- **Detects**: Plain text strings or simple dictionaries
- **Renders**: Clean text with whitespace preservation
- **Features**:
  - Proper formatting for paragraphs
  - Word wrapping
  - Readable fonts

**Example Use Cases:**
- Essay responses
- Code explanations
- General AI conversations

#### JSONSchema
- **Detects**: Explicitly requested only
- **Renders**: Syntax-highlighted JSON
- **Features**:
  - Pretty-printed with indentation
  - Scrollable for large responses
  - Raw data visibility

### Adding Custom Schemas

Create `app/schemas/your_schema.py`:

```python
from .base import ResponseSchema

class YourSchema(ResponseSchema):
    def detect(self, data: Any) -> bool:
        # Return True if this schema can handle the data
        return isinstance(data, YourCustomType)

    def render_context(self, data: Any) -> Dict[str, Any]:
        # Transform data for template
        return {'your_data': processed_data}

    @property
    def template_name(self) -> str:
        return 'partials/_your_template.html'

    @property
    def priority(self) -> int:
        return 20  # Lower = checked first
```

Register in `app/schemas/__init__.py`:

```python
SCHEMAS: List[ResponseSchema] = [
    YourSchema(),           # Add here
    StructuredDataSchema(),
    TextSchema(),
]
```

## Roadmap

### Completed ✅
- [x] OpenAI Responses API integration
- [x] Secure 1Password CLI integration
- [x] Dynamic response display with schema detection
- [x] Performance metrics tracking with provider context
- [x] Provider abstraction layer
- [x] Multi-provider UI with provider selection
- [x] Dynamic form generation based on provider
- [x] Schema detection system (structured, text, JSON)
- [x] Generic error handling for all providers
- [x] Session-based provider persistence

### In Progress 🚧
- [ ] Google Gemini provider implementation
- [ ] Anthropic Claude provider implementation

### Planned 📋
- [ ] Response history and export
- [ ] Streaming support for real-time responses
- [ ] Provider comparison mode (side-by-side)
- [ ] Cost tracking and estimation
- [ ] Custom schema definitions
- [ ] Batch request processing
- [ ] API response caching

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - free to use for personal and commercial projects.

## Support

- **Issues**: [GitHub Issues](https://github.com/anubhavtyagi27/ai-sandbox/issues)
- **1Password CLI**: [Documentation](https://developer.1password.com/docs/cli/)
- **OpenAI API**: [Help Center](https://help.openai.com/)

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Secured by [1Password CLI](https://1password.com/downloads/command-line/)
- Powered by [OpenAI](https://openai.com/), [Google Gemini](https://deepmind.google/technologies/gemini/), [Anthropic](https://www.anthropic.com/)
