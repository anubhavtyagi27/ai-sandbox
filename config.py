import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration with environment variable loading and validation"""

    # Required configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Multi-provider API key references (1Password)
    OP_ITEM_REFERENCE_OPENAI = os.environ.get('OP_ITEM_REFERENCE_OPENAI')
    OP_ITEM_REFERENCE_GEMINI = os.environ.get('OP_ITEM_REFERENCE_GEMINI')
    OP_ITEM_REFERENCE_ANTHROPIC = os.environ.get('OP_ITEM_REFERENCE_ANTHROPIC')

    # Backward compatibility: support old OP_ITEM_REFERENCE for OpenAI
    # If the new variable isn't set but the old one is, use the old one
    if not OP_ITEM_REFERENCE_OPENAI and os.environ.get('OP_ITEM_REFERENCE'):
        OP_ITEM_REFERENCE_OPENAI = os.environ.get('OP_ITEM_REFERENCE')

    # Default provider
    DEFAULT_PROVIDER = os.environ.get('DEFAULT_PROVIDER', 'openai')

    # Optional configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    # Flask-WTF configuration
    WTF_CSRF_ENABLED = True

    @staticmethod
    def get_provider_reference(provider: str) -> str:
        """
        Get 1Password reference for a specific provider.

        Args:
            provider: Provider name (e.g., 'openai', 'gemini', 'anthropic')

        Returns:
            1Password reference string

        Raises:
            ValueError: If no reference configured for the provider
        """
        attr_name = f'OP_ITEM_REFERENCE_{provider.upper()}'
        ref = getattr(Config, attr_name, None)

        if not ref:
            raise ValueError(
                f"No 1Password reference configured for provider: {provider}. "
                f"Please set {attr_name} in your .env file. "
                f"Format: op://vault-name/item-name/field-name"
            )

        return ref

    @staticmethod
    def validate():
        """
        Validate required configuration is present and correctly formatted.

        Raises:
            ValueError: If configuration is invalid or missing
        """
        # Validate default provider has a configured reference
        default_provider = Config.DEFAULT_PROVIDER
        try:
            ref = Config.get_provider_reference(default_provider)

            if not ref.startswith('op://'):
                raise ValueError(
                    f"1Password reference for {default_provider} must be in the format: "
                    f"op://vault-name/item-name/field-name"
                )
        except ValueError as e:
            raise ValueError(
                f"Default provider '{default_provider}' is not properly configured. "
                f"{str(e)}"
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
