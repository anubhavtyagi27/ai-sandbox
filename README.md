# OpenAI Responses API Flask App

A simple Flask web application for testing OpenAI's Responses API with secure API key management via 1Password CLI.

## Features

- 🔐 **Secure API Key Management**: Retrieves OpenAI API key from 1Password CLI (never stored locally)
- 🎯 **User-Friendly Form Interface**: Easy-to-use web form for all Responses API parameters
- ⚡ **Real-Time Response Display**: View API responses directly on the page
- 🛡️ **Form Validation**: Client and server-side validation for all inputs
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **1Password CLI**: [Installation Guide](https://developer.1password.com/docs/cli/get-started/)
- **OpenAI API Key**: Stored in your 1Password vault

## Installation

### 1. Clone or Navigate to Project

```bash
cd /Users/anubhav/Projects/keepmefit_v0
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

#### Store Your OpenAI API Key in 1Password

1. Open 1Password
2. Create a new item (or use existing) to store your OpenAI API key
3. Note the reference path in format: `op://vault-name/item-name/field-name`
   - Example: `op://Private/OpenAI API Key/credential`

#### Test 1Password CLI

Verify you can retrieve the key:

```bash
op read "op://Private/OpenAI API Key/credential"
```

If this is your first time, you'll be prompted to authenticate via biometrics or password.

### 2. Configure Environment Variables

#### Create .env File

```bash
cp .env.example .env
```

#### Edit .env File

```bash
# Required: Your 1Password secret reference
OP_ITEM_REFERENCE=op://Private/OpenAI API Key/credential

# Generate a secure secret key
SECRET_KEY=your-generated-secret-key-here

# Environment
FLASK_ENV=development

# Optional: API timeout in seconds
OPENAI_API_TIMEOUT=30
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
2026-02-10 10:00:00 - app - INFO - Starting Flask app in development mode
 * Running on http://127.0.0.1:5000
```

### Access the Application

Open your browser and navigate to:

```
http://localhost:5000
```

## Usage

### Making a Request

1. **Select a Model**: Choose from GPT-4, GPT-4 Turbo, GPT-4o, etc.
2. **Enter Input**: Type your prompt or message in the input textarea
3. **Optional Parameters** (click to expand):
   - **Max Tokens**: Limit the response length (1-128000)
   - **Temperature**: Control randomness (0.0-2.0)
   - **Top P**: Nucleus sampling parameter (0.0-1.0)
   - **Metadata**: Add JSON metadata (e.g., `{"user_id": "123"}`)
   - **Stream**: Enable streaming (checkbox)
   - **Store**: Store response for later retrieval (checkbox)
4. **Click "Submit Request"**: The form will be sent to OpenAI's API
5. **View Response**: Results appear below the form

### Example Request

**Model**: `gpt-4`
**Input**: `Explain quantum computing in simple terms`
**Temperature**: `0.7`
**Max Tokens**: `500`

## Troubleshooting

### Common Issues

#### 1Password CLI Not Found

**Error**: `1Password CLI not found`

**Solution**: Install 1Password CLI from [here](https://1password.com/downloads/command-line/)

#### Not Authenticated with 1Password

**Error**: `Not authenticated with 1Password`

**Solution**: Sign in to 1Password CLI:

```bash
op signin
```

Follow the prompts to authenticate.

#### Item Not Found

**Error**: `Item not found: op://...`

**Solution**:
- Verify the item exists in 1Password
- Check your `OP_ITEM_REFERENCE` in `.env` file
- Ensure the path format is correct: `op://vault/item/field`

#### Configuration Error

**Error**: `OP_ITEM_REFERENCE environment variable is required`

**Solution**: Ensure you have created a `.env` file with the required variables (see Configuration section).

#### OpenAI API Errors

**Invalid API Key** (401):
- Verify your API key in 1Password is correct
- Test retrieval: `op read "your-reference-path"`

**Rate Limit Exceeded** (429):
- Wait and try again later
- Check your OpenAI account usage limits

**Invalid Request** (400):
- Check that all parameters are within valid ranges
- Ensure model name is correct

#### Port Already in Use

**Error**: `Address already in use`

**Solution**: Either stop the other process using port 5000, or change the port in `run.py`:

```python
app.run(host='127.0.0.1', port=5001)  # Use different port
```

## Project Structure

```
keepmefit_v0/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── routes.py             # Route handlers
│   ├── forms.py              # Form definitions
│   ├── services/
│   │   ├── onepassword.py    # 1Password CLI integration
│   │   └── openai_client.py  # OpenAI API client
│   ├── templates/
│   │   ├── base.html         # Base template
│   │   └── index.html        # Main form page
│   └── static/
│       └── css/
│           └── style.css     # Custom styles
├── config.py                 # Configuration
├── run.py                    # Entry point
├── requirements.txt          # Dependencies
├── .env                      # Environment variables (not in git)
├── .env.example             # Example environment file
└── README.md                # This file
```

## Security Notes

- ✅ API key is **never** stored in project files
- ✅ API key is retrieved on-demand from 1Password
- ✅ `.env` file is in `.gitignore` (not committed to version control)
- ✅ CSRF protection enabled on all forms
- ✅ Input validation on client and server side

## Development

### Running in Debug Mode

Debug mode is enabled by default in development. To disable it:

```bash
# In .env
FLASK_ENV=production
```

### Installing New Dependencies

```bash
pip install package-name
pip freeze > requirements.txt
```

## Production Deployment

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 'app:create_app()'
```

**Important for Production**:
- Set `FLASK_ENV=production` in `.env`
- Generate a strong `SECRET_KEY`
- Use HTTPS
- Set up proper logging
- Configure firewall rules

## API Reference

This app uses OpenAI's Responses API endpoint:

- **Endpoint**: `POST https://api.openai.com/v1/responses`
- **Documentation**: [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)

## Contributing

Feel free to submit issues or pull requests for improvements.

## License

MIT License - feel free to use this for your own projects.

## Support

For issues related to:
- **Flask App**: Check the troubleshooting section above
- **1Password CLI**: [1Password CLI Documentation](https://developer.1password.com/docs/cli/)
- **OpenAI API**: [OpenAI Help Center](https://help.openai.com/)

## Acknowledgments

- Built with Flask
- Secured by 1Password CLI
- Powered by OpenAI Responses API
