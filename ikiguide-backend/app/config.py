import os
import base64
import secrets
from typing import List, Optional
import dotenv
import logging

# Load .env file explicitly
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Set up logging
logger = logging.getLogger(__name__)

def generate_key(password: str, salt: Optional[bytes] = None) -> bytes:
    """
    Generate a consistent encryption key
    """
    if salt is None:
        salt = b'ikiguide_fixed_salt_2024'
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_secret(secret: str, key: bytes) -> str:
    """
    Encrypt a secret using Fernet symmetric encryption
    """
    f = Fernet(key)
    return f.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted_secret: str, key: bytes) -> Optional[str]:
    """
    Decrypt a secret using Fernet symmetric encryption
    """
    f = Fernet(key)
    try:
        return f.decrypt(encrypted_secret.encode()).decode()
    except Exception as e:
        logger.error(f"Error decrypting secret: {e}")
        return None

def load_cors_origins() -> List[str]:
    """
    Load CORS origins from environment variable with fallback
    """
    cors_origins_str = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    return [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

class Settings:
    """
    Secure configuration management with encryption
    """
    # Application Environment
    APP_NAME = os.getenv('APP_NAME', 'Ikiguide')
    APP_ENV = os.getenv('APP_ENV', 'development')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # CORS Configuration
    CORS_ORIGINS = load_cors_origins()
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else []
    
    # Session Configuration
    SESSION_MAX_AGE = int(os.getenv('SESSION_MAX_AGE', 3600))
    SESSION_MAX_TIMEOUT = int(os.getenv('SESSION_MAX_TIMEOUT', 24))
    SESSION_MAX_CONCURRENT = int(os.getenv('SESSION_MAX_CONCURRENT', 1000))
    
    # Encryption Configuration
    _ENCRYPTION_PASSWORD = 'ikiguide_secret_encryption_key_2024'
    _ENCRYPTION_KEY = generate_key(_ENCRYPTION_PASSWORD)
    
    # Secure OpenAI Configuration
    _ENCRYPTED_OPENAI_API_KEY = os.getenv('ENCRYPTED_OPENAI_API_KEY', '')
    OPENAI_API_KEY = decrypt_secret(_ENCRYPTED_OPENAI_API_KEY, _ENCRYPTION_KEY) if _ENCRYPTED_OPENAI_API_KEY else ''
    
    # Azure Email Configuration
    _ENCRYPTED_AZURE_TENANT_ID = os.getenv('ENCRYPTED_AZURE_TENANT_ID', '')
    AZURE_TENANT_ID = decrypt_secret(_ENCRYPTED_AZURE_TENANT_ID, _ENCRYPTION_KEY) if _ENCRYPTED_AZURE_TENANT_ID else ''
    
    _ENCRYPTED_AZURE_CLIENT_ID = os.getenv('ENCRYPTED_AZURE_CLIENT_ID', '')
    AZURE_CLIENT_ID = decrypt_secret(_ENCRYPTED_AZURE_CLIENT_ID, _ENCRYPTION_KEY) if _ENCRYPTED_AZURE_CLIENT_ID else ''
    
    _ENCRYPTED_AZURE_CLIENT_SECRET = os.getenv('ENCRYPTED_AZURE_CLIENT_SECRET', '')
    AZURE_CLIENT_SECRET = decrypt_secret(_ENCRYPTED_AZURE_CLIENT_SECRET, _ENCRYPTION_KEY) if _ENCRYPTED_AZURE_CLIENT_SECRET else ''
    
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')

    EMAIL_BCC = os.getenv('EMAIL_BCC', '')
    
    # Debug logging for Azure configuration
    @classmethod
    def validate_azure_config(cls):
        """
        Validate Azure configuration and log diagnostic information.
        """
        logger.info("Validating Azure Configuration:")
        logger.info(f"Tenant ID: {bool(cls.AZURE_TENANT_ID)}")
        logger.info(f"Client ID: {bool(cls.AZURE_CLIENT_ID)}")
        logger.info(f"Client Secret: {bool(cls.AZURE_CLIENT_SECRET)}")
        logger.info(f"Sender Email: {cls.EMAIL_FROM}")
        
        # Perform basic validation
        if not all([cls.AZURE_TENANT_ID, cls.AZURE_CLIENT_ID, cls.AZURE_CLIENT_SECRET, cls.EMAIL_FROM]):
            logger.warning("Incomplete Azure configuration detected!")
        
        return all([cls.AZURE_TENANT_ID, cls.AZURE_CLIENT_ID, cls.AZURE_CLIENT_SECRET, cls.EMAIL_FROM])

    # API Configuration
    API_HOST = os.getenv('API_HOST', 'localhost')
    API_PORT = int(os.getenv('API_PORT', 8000))
    
    @classmethod
    def encrypt_and_store_secret(cls, secret: str, env_var_name: str) -> str:
        """
        Encrypt a secret and suggest how to store it in environment
        
        :param secret: The secret to encrypt
        :param env_var_name: The environment variable name to store the encrypted secret
        :return: The encrypted secret
        """
        encrypted_secret = encrypt_secret(secret, cls._ENCRYPTION_KEY)
        print(f"Encrypted Secret: {encrypted_secret}")
        print(f"Set the following environment variable:")
        print(f"export {env_var_name}={encrypted_secret}")
        return encrypted_secret
    
    @classmethod
    def setup_openai_key(cls):
        """
        Set up OpenAI API key for the current session
        """
        
        try:
            if cls.OPENAI_API_KEY:
                # Set the API key as an environment variable for OpenAI library
                os.environ['OPENAI_API_KEY'] = cls.OPENAI_API_KEY
                print(f"OpenAI API Key set in environment successfully!")
            else:
                print(f"No OpenAI API key found. Please encrypt and set ENCRYPTED_OPENAI_API_KEY.")
                print(f"OpenAI API key is not set. Some functionalities may be limited.")
        except Exception as e:
            print(f"Error setting up OpenAI API key: {e}")

# Create settings instance
settings = Settings()

# Automatically set up OpenAI key when this module is imported
settings.setup_openai_key()

# Validate Azure configuration at startup
if not settings.validate_azure_config():
    logger.warning("Azure email configuration is not complete. Email functionality may be limited.")
