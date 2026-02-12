import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration with environment variable loading and validation"""

    # Required configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    OP_ITEM_REFERENCE = os.environ.get('OP_ITEM_REFERENCE')

    # Optional configuration
    OPENAI_API_TIMEOUT = int(os.environ.get('OPENAI_API_TIMEOUT', 30))
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    # Flask-WTF configuration
    WTF_CSRF_ENABLED = True

    @staticmethod
    def validate():
        """
        Validate required configuration is present and correctly formatted.

        Raises:
            ValueError: If configuration is invalid or missing
        """
        if not Config.OP_ITEM_REFERENCE:
            raise ValueError(
                "OP_ITEM_REFERENCE environment variable is required. "
                "Please set it in your .env file. "
                "Format: op://vault-name/item-name/field-name"
            )

        if not Config.OP_ITEM_REFERENCE.startswith('op://'):
            raise ValueError(
                "OP_ITEM_REFERENCE must be in the format: op://vault-name/item-name/field-name"
            )

        if Config.SECRET_KEY == 'dev-secret-key-change-in-production' and Config.FLASK_ENV == 'production':
            raise ValueError(
                "SECRET_KEY must be set to a secure random value in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
