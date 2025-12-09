"""Authentication manager implementation for API key validation."""

from typing import List, Optional
from datetime import datetime
from src.interfaces import IAuthenticationManager
from src.models import Config
from src.logging_config import get_logger


class AuthenticationManager(IAuthenticationManager):
    """Authentication manager for API key validation and security event logging."""
    
    def __init__(self, config: Config):
        """Initialize authentication manager.
        
        Args:
            config: Configuration object containing API keys
        """
        self.config = config
        self.logger = get_logger("auth")
        self._api_keys: List[str] = []
        self._load_api_keys_from_config()
    
    def _load_api_keys_from_config(self) -> None:
        """Load API keys from configuration."""
        self._api_keys = self.config.api_keys.copy()
        if self._api_keys:
            self.logger.info(f"Loaded {len(self._api_keys)} API key(s) from configuration")
        else:
            self.logger.warning("No API keys configured - all requests will be rejected")
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if the API key is valid, False otherwise
        """
        if not api_key:
            return False
        
        # Check if the API key exists in the list of valid keys
        is_valid = api_key in self._api_keys
        
        return is_valid
    
    def load_api_keys(self) -> List[str]:
        """Load API keys from configuration.
        
        Returns:
            List of valid API keys
        """
        self._load_api_keys_from_config()
        return self._api_keys.copy()
    
    def log_auth_attempt(self, api_key: str, success: bool, ip: str) -> None:
        """Log an authentication attempt.
        
        Args:
            api_key: The API key used (will be masked in logs)
            success: Whether authentication was successful
            ip: The IP address of the requester
        """
        # Mask the API key for security (show only first 4 and last 4 characters)
        masked_key = self._mask_api_key(api_key)
        
        timestamp = datetime.now().isoformat()
        
        if success:
            self.logger.info(
                f"Authentication SUCCESS - IP: {ip}, API Key: {masked_key}, Time: {timestamp}"
            )
        else:
            self.logger.warning(
                f"Authentication FAILED - IP: {ip}, API Key: {masked_key}, Time: {timestamp}"
            )
    
    def _mask_api_key(self, api_key: str) -> str:
        """Mask an API key for logging purposes.
        
        Args:
            api_key: The API key to mask
            
        Returns:
            Masked API key string
        """
        if not api_key:
            return "[empty]"
        
        if len(api_key) <= 8:
            # For short keys, mask everything except first character
            return api_key[0] + "*" * (len(api_key) - 1)
        
        # For longer keys, show first 4 and last 4 characters
        return f"{api_key[:4]}...{api_key[-4:]}"
    
    def get_http_status_code(self, api_key: Optional[str]) -> int:
        """Get appropriate HTTP status code based on API key validation.
        
        Args:
            api_key: The API key to validate (can be None)
            
        Returns:
            HTTP status code (401 for missing key, 403 for invalid key, 200 for valid)
        """
        # No API key provided
        if not api_key:
            return 401  # Unauthorized
        
        # Invalid API key
        if not self.validate_api_key(api_key):
            return 403  # Forbidden
        
        # Valid API key
        return 200  # OK
    
    def reload_api_keys(self, config: Config) -> None:
        """Reload API keys from updated configuration.
        
        Args:
            config: Updated configuration object
        """
        old_count = len(self._api_keys)
        self.config = config
        self._load_api_keys_from_config()
        new_count = len(self._api_keys)
        
        self.logger.info(f"API keys reloaded: {old_count} -> {new_count}")
