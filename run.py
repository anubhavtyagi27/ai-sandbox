#!/usr/bin/env python3
"""
Application entry point for AI Sandbox Flask application.

This script initializes and runs the Flask development server.
For production deployment, use a WSGI server like Gunicorn instead.
"""
import os

from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the Flask development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5001)),
        debug=app.config.get('DEBUG', True)
    )
