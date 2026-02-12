from flask import Flask
import logging
from config import get_config, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_app():
    """
    Flask application factory.

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        app.logger.error(f"Configuration error: {e}")
        raise

    # Log startup info
    app.logger.info(f"Starting Flask app in {app.config['FLASK_ENV']} mode")

    # Register routes
    with app.app_context():
        from app import routes

    return app
