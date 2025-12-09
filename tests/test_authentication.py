"""Tests for authentication manager."""

import pytest
from src.authentication import AuthenticationManager
from src.models import Config


class TestAuthenticationManager:
    """Test suite for AuthenticationManager."""
    
    def test_validate_valid_api_key(self):
        """Test validation of a valid API key."""
        config = Config(api_keys=["test-key-123", "another-key-456"])
        auth_manager = AuthenticationManager(config)
        
        assert auth_manager.validate_api_key("test-key-123") is True
        assert auth_manager.validate_api_key("another-key-456") is True
    
    def test_validate_invalid_api_key(self):
        """Test validation of an invalid API key."""
        config = Config(api_keys=["test-key-123"])
        auth_manager = AuthenticationManager(config)
        
        assert auth_manager.validate_api_key("wrong-key") is False
        assert auth_manager.validate_api_key("") is False
    
    def test_validate_empty_api_key(self):
        """Test validation of empty API key."""
        config = Config(api_keys=["test-key-123"])
        auth_manager = AuthenticationManager(config)
        
        assert auth_manager.validate_api_key("") is False
    
    def test_load_api_keys(self):
        """Test loading API keys from configuration."""
        config = Config(api_keys=["key1", "key2", "key3"])
        auth_manager = AuthenticationManager(config)
        
        keys = auth_manager.load_api_keys()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
    
    def test_multiple_api_keys_support(self):
        """Test support for multiple API keys."""
        config = Config(api_keys=["key1", "key2", "key3"])
        auth_manager = AuthenticationManager(config)
        
        # All keys should be valid
        assert auth_manager.validate_api_key("key1") is True
        assert auth_manager.validate_api_key("key2") is True
        assert auth_manager.validate_api_key("key3") is True
        
        # Invalid key should fail
        assert auth_manager.validate_api_key("key4") is False
    
    def test_log_auth_attempt_success(self, caplog):
        """Test logging of successful authentication attempt."""
        import logging
        caplog.set_level(logging.INFO)
        
        config = Config(api_keys=["test-key-123"])
        auth_manager = AuthenticationManager(config)
        
        auth_manager.log_auth_attempt("test-key-123", True, "192.168.1.1")
        
        assert "Authentication SUCCESS" in caplog.text
        assert "192.168.1.1" in caplog.text
    
    def test_log_auth_attempt_failure(self, caplog):
        """Test logging of failed authentication attempt."""
        import logging
        caplog.set_level(logging.WARNING)
        
        config = Config(api_keys=["test-key-123"])
        auth_manager = AuthenticationManager(config)
        
        auth_manager.log_auth_attempt("wrong-key", False, "192.168.1.1")
        
        assert "Authentication FAILED" in caplog.text
        assert "192.168.1.1" in caplog.text
    
    def test_api_key_masking(self):
        """Test that API keys are properly masked in logs."""
        config = Config(api_keys=["test-key-123456"])
        auth_manager = AuthenticationManager(config)
        
        masked = auth_manager._mask_api_key("test-key-123456")
        assert masked == "test...3456"
        
        # Short key
        masked_short = auth_manager._mask_api_key("short")
        assert masked_short == "s****"
        
        # Empty key
        masked_empty = auth_manager._mask_api_key("")
        assert masked_empty == "[empty]"
    
    def test_http_status_code_no_key(self):
        """Test HTTP status code for missing API key."""
        config = Config(api_keys=["test-key-123"])
        auth_manager = AuthenticationManager(config)
        
        assert auth_manager.get_http_status_code(None) == 401
        assert auth_manager.get_http_status_code("") == 401
    
    def test_http_status_code_invalid_key(self):
        """Test HTTP status code for invalid API key."""
        config = Config(api_keys=["test-key-123"])
        auth_manager = AuthenticationManager(config)
        
        assert auth_manager.get_http_status_code("wrong-key") == 403
    
    def test_http_status_code_valid_key(self):
        """Test HTTP status code for valid API key."""
        config = Config(api_keys=["test-key-123"])
        auth_manager = AuthenticationManager(config)
        
        assert auth_manager.get_http_status_code("test-key-123") == 200
    
    def test_reload_api_keys(self, caplog):
        """Test reloading API keys from updated configuration."""
        import logging
        caplog.set_level(logging.INFO)
        
        config = Config(api_keys=["key1", "key2"])
        auth_manager = AuthenticationManager(config)
        
        assert len(auth_manager._api_keys) == 2
        
        # Update configuration
        new_config = Config(api_keys=["key1", "key2", "key3", "key4"])
        auth_manager.reload_api_keys(new_config)
        
        assert len(auth_manager._api_keys) == 4
        assert "API keys reloaded: 2 -> 4" in caplog.text
    
    def test_no_api_keys_configured(self, caplog):
        """Test behavior when no API keys are configured."""
        import logging
        caplog.set_level(logging.WARNING)
        
        config = Config(api_keys=[])
        auth_manager = AuthenticationManager(config)
        
        assert "No API keys configured" in caplog.text
        assert auth_manager.validate_api_key("any-key") is False
