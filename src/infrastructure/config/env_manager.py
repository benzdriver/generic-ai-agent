"""
Configuration manager for the application.
"""
from functools import lru_cache
from .pydantic_config import AppSettings

@lru_cache()
def get_config() -> AppSettings:
    """
    Get the application settings.
    The settings are cached for performance.
    """
    return AppSettings()

def init_config(test_mode: bool = False) -> AppSettings:
    """
    Initialize the application configuration.
    
    Args:
        test_mode: Whether to run in test mode
        
    Returns:
        AppSettings: The initialized configuration
    """
    # Clear the cache if needed for testing
    if test_mode:
        get_config.cache_clear()
    
    config = get_config()
    
    # Additional initialization logic can be added here
    # For example, setting up logging, validating API keys, etc.
    
    return config 