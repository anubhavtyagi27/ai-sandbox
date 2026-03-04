#!/usr/bin/env python3
"""
Application entry point for AI Sandbox Flask application.

This script initializes and runs the Flask development server.
For production deployment, use a WSGI server like Gunicorn instead.
"""
from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the Flask development server
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=app.config.get('DEBUG', True)
    )
