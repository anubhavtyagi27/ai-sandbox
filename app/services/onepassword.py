import subprocess
import logging

logger = logging.getLogger(__name__)


class OnePasswordError(Exception):
    """Base exception for 1Password operations"""
    pass


class OnePasswordCLINotFound(OnePasswordError):
    """1Password CLI is not installed or not in PATH"""
    pass


class OnePasswordAuthenticationError(OnePasswordError):
    """Failed to authenticate with 1Password"""
    pass


class OnePasswordItemNotFound(OnePasswordError):
    """Requested item not found in 1Password"""
    pass


class OnePasswordService:
    """Service for retrieving secrets from 1Password CLI"""

    @staticmethod
    def get_secret(reference: str) -> str:
        """
        Retrieve a secret from 1Password using CLI.

        Args:
            reference: Secret reference in format op://vault/item/field

        Returns:
            The secret value as string

        Raises:
            OnePasswordCLINotFound: If 1Password CLI is not installed
            OnePasswordAuthenticationError: If not authenticated with 1Password
            OnePasswordItemNotFound: If the item doesn't exist
            OnePasswordError: For other errors
        """
        try:
            result = subprocess.run(
                ['op', 'read', reference],
                capture_output=True,
                text=True,
                timeout=None  # No timeout - allow time for biometric authentication
            )

            if result.returncode == 0:
                return result.stdout.strip()

            # Parse error messages from stderr
            error_output = result.stderr.lower()

            if 'not found' in error_output or 'no item' in error_output:
                raise OnePasswordItemNotFound(
                    f"Item not found: {reference}. Please check your OP_ITEM_REFERENCE."
                )
            elif 'not signed in' in error_output or 'not currently signed in' in error_output:
                raise OnePasswordAuthenticationError(
                    "Not authenticated with 1Password. Please sign in using: op signin"
                )
            elif 'authentication' in error_output or 'unauthorized' in error_output:
                raise OnePasswordAuthenticationError(
                    "Authentication failed. Please authenticate with 1Password."
                )
            else:
                raise OnePasswordError(f"Failed to retrieve secret: {result.stderr}")

        except FileNotFoundError:
            raise OnePasswordCLINotFound(
                "1Password CLI not found. Please install it from: "
                "https://1password.com/downloads/command-line/"
            )
        except OnePasswordError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret: {e}")
            raise OnePasswordError(f"Unexpected error: {str(e)}")

    @staticmethod
    def validate_cli_available() -> bool:
        """
        Check if 1Password CLI is available and working.

        Returns:
            True if CLI is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['op', '--version'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
