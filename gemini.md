# AI Sandbox Project Context

This document provides a summary of the AI Sandbox project for the Gemini CLI.

## Project Overview

AI Sandbox is a Flask-based web application that provides a unified interface for calling various AI provider APIs (OpenAI, Google Gemini, Anthropic Claude, etc.). It features dynamic form generation based on provider-specific parameters, flexible response display with auto-detection of data schemas, and secure credential management through 1Password CLI integration.

## Key Features

- **Multi-Provider Support**: Currently supports OpenAI, with plans to add Google Gemini and Anthropic Claude.
- **Secure API Key Management**: Retrieves API keys from 1Password CLI via biometric authentication.
- **Dynamic Provider Selection**: Switch between AI providers through a dropdown in the UI.
- **Smart Response Display**: Auto-detects response format (structured data tables, plain text, JSON).
- **Performance Metrics**: Real-time latency, token usage, and provider tracking.

## Project Structure

```
ai-sandbox/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Route handlers
│   ├── forms.py                 # Dynamic form generation
│   │
│   ├── providers/               # Provider abstraction layer
│   │   ├── base.py              # BaseProvider abstract class
│   │   └── openai.py            # OpenAI implementation
│   │
│   ├── schemas/                 # Response schema detection
│   │   ├── base.py              # ResponseSchema abstract class
│   │   ├── structured.py        # Structured data (tables)
│   │   └── text.py              # Text and JSON responses
│   │
│   ├── services/
│   │   └── onepassword.py       # 1Password CLI integration
│   │
│   └── templates/               # Jinja2 templates
│
├── config.py                    # Configuration management
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # Project documentation
```

## Dependencies

- Flask==3.0.0
- Flask-WTF==1.2.1
- WTForms==3.1.1
- python-dotenv==1.0.0
- requests==2.31.0

## Configuration

- The application is configured through a `.env` file.
- API keys are stored in 1Password and referenced in the `.env` file using the `op://` URI scheme.
- The `config.py` file loads the configuration and provides a `get_provider_reference` method to retrieve the 1Password reference for a given provider.

## Running the Application

To run the application, use the following command:

```bash
python run.py
```

The application will be available at `http://127.0.0.1:5001`.

## Running the Application (Easy Way)

A `start.sh` script is provided to simplify the process of running the application. This script will automatically create a virtual environment, install dependencies, and start the application.

To run the application using the script, execute the following command in your terminal:

```bash
./start.sh
```
