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

    # Register blueprints
    from app.routes import bp as main_bp
    from app.routes_meals import bp as meals_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(meals_bp)

    return app
