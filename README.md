# AI Sandbox

A multi-provider AI API client for testing and experimenting with different AI models through a simple web interface. Securely manage API keys via 1Password CLI.

## Overview

AI Sandbox is a Flask-based web application that provides a unified interface for calling various AI provider APIs (OpenAI, Google Gemini, Anthropic Claude, etc.). It features dynamic form generation based on provider-specific parameters, flexible response display with auto-detection of data schemas, and secure credential management through 1Password CLI integration.

## Features

- 🤖 **Multi-Provider Support**: Currently supports OpenAI (Gemini & Anthropic coming soon)
- 🔐 **Secure API Key Management**: Retrieves API keys from 1Password CLI via biometric authentication (never stored locally)
- 🎯 **Dynamic Form Generation**: Form fields adapt to selected AI provider's API parameters
- 📊 **Smart Response Display**: Auto-detects response format (structured data tables, plain text, JSON)
- ⚡ **Performance Metrics**: Real-time latency and token usage tracking
- 🛡️ **Form Validation**: Client and server-side validation for all inputs
- 📝 **System Instructions**: Load prompts from markdown files with session persistence
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

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
│   ├── __init__.py           # Flask app factory
│   ├── routes.py             # Route handlers
│   ├── forms.py              # Dynamic form generation
│   ├── services/
│   │   ├── onepassword.py    # 1Password CLI integration
│   │   └── openai_client.py  # OpenAI API client
│   ├── templates/
│   │   ├── base.html         # Base template
│   │   └── index.html        # Main interface
│   └── static/css/
│       └── style.css         # Custom styles
├── config.py                 # Multi-provider configuration
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

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

**Error**: `Not authenticated with 1Password`
- Run: `op signin`

**Error**: `Item not found`
- Verify item exists in 1Password
- Check `OP_ITEM_REFERENCE_*` in `.env`
- Ensure format: `op://vault/item/field`

### API Errors

**Invalid API Key** (401):
- Verify key in 1Password
- Test: `op read "your-reference-path"`

**Rate Limit** (429):
- Wait before retrying
- Check provider usage limits

**Port in Use**:
- Change port in `run.py` (default: 5001)

## Architecture

AI Sandbox uses a provider abstraction layer for multi-provider support:

- **Base Provider Interface**: Abstract class defining common methods
- **Provider Implementations**: Specific clients for OpenAI, Gemini, etc.
- **Schema Detection**: Auto-detects response format for optimal display
- **Dynamic Forms**: Generates form fields based on provider capabilities

## Roadmap

- [x] OpenAI Responses API integration
- [x] Secure 1Password CLI integration
- [x] Dynamic response table display
- [x] Performance metrics tracking
- [ ] Provider abstraction layer
- [ ] Google Gemini support
- [ ] Anthropic Claude support
- [ ] Response history and export
- [ ] Streaming support

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
