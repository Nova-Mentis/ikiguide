import os
from typing import List

def load_cors_origins() -> List[str]:
    """
    Load CORS origins from environment variable with fallback
    """
    cors_origins_str = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    return [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

def load_log_level() -> str:
    """
    Load and validate log level
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    if log_level not in valid_levels:
        log_level = 'INFO'
    
    return log_level

def parse_bool_env(env_var: str, default: bool = False) -> bool:
    """
    Parse boolean environment variable with multiple truthy values.
    
    :param env_var: Name of environment variable
    :param default: Default value if not set
    :return: Boolean value
    """
    value = os.getenv(env_var, str(default)).lower()
    truthy_values = ['true', '1', 'yes', 'on']
    return value in truthy_values

class Settings:
    """
    Simple configuration management without Pydantic
    """
    APP_NAME = os.getenv('APP_NAME', 'Ikiguide')
    APP_ENV = os.getenv('APP_ENV', 'development')
    APP_DEBUG = parse_bool_env('APP_DEBUG', default=False)
    
    LOG_LEVEL = load_log_level()
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    CORS_ORIGINS = load_cors_origins()
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS')
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    API_HOST = os.getenv('API_HOST', 'localhost')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    SESSION_MAX_TIMEOUT = int(os.getenv('SESSION_MAX_TIMEOUT', '24'))  # hours
    SESSION_MAX_CONCURRENT = int(os.getenv('SESSION_MAX_CONCURRENT', '1000'))
    SESSION_MAX_AGE = int(os.getenv('SESSION_MAX_AGE', '3600'))  # 1 hour in seconds

# Create settings instance
settings = Settings()
