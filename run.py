#!/usr/bin/env python3
"""
Application entry point for the OpenAI Responses API Flask application.

This script initializes and runs the Flask development server.
For production deployment, use a WSGI server like Gunicorn instead.
"""
from app.routes import app

if __name__ == '__main__':
    # Run the Flask development server
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=app.config.get('DEBUG', True)
    )
