"""Configuration manager implementation with validation and hot reload support."""

import os
import yaml
from pathlib import Path
from typing import Optional
from src.models import Config
from src.interfaces import IConfigurationManager
from src.logging_config import get_logger


class ConfigurationManager(IConfigurationManager):
    """Configuration manager for loading, validating, and hot-reloading configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or "config/config.yaml"
        self.config: Optional[Config] = None
        self.logger = get_logger("config")
        self._default_config = Config()
    
    def load_config(self) -> Config:
        """Load configuration from file or use defaults.
        
        Returns:
            Config object with loaded settings
        """
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                self.config = Config(
                    java_home=config_data.get('java_home', self._default_config.java_home),
                    cassandra_bin_path=config_data.get('cassandra_bin_path', self._default_config.cassandra_bin_path),
                    api_keys=config_data.get('api_keys', []),
                    log_level=config_data.get('log_level', self._default_config.log_level),
                    log_file=config_data.get('log_file', self._default_config.log_file),
                    max_log_size=config_data.get('max_log_size', self._default_config.max_log_size),
                    health_check_interval=config_data.get('health_check_interval', self._default_config.health_check_interval)
                )
                self.logger.info(f"Configuration loaded from {config_file}")
                
                # Validate and fallback to defaults if needed
                self._validate_and_fallback()
                
            except yaml.YAMLError as e:
                self.logger.error(f"YAML parsing error in configuration file: {e}")
                self.config = Config()
                self.logger.info("Using default configuration due to parsing error")
            except Exception as e:
                self.logger.error(f"Error loading configuration: {e}")
                self.config = Config()
                self.logger.info("Using default configuration")
        else:
            self.logger.warning(f"Configuration file not found: {config_file}")
            self.config = Config()
            self.logger.info("Using default configuration")
        
        return self.config
    
    def _validate_and_fallback(self) -> None:
        """Validate paths and fallback to defaults if invalid."""
        if not self.config:
            return
        
        # Validate JAVA_HOME
        java_home_path = Path(self.config.java_home)
        if not java_home_path.exists():
            self.logger.error(f"Invalid JAVA_HOME path: {self.config.java_home}")
            self.config.java_home = self._default_config.java_home
            self.logger.info(f"Falling back to default JAVA_HOME: {self.config.java_home}")
        
        # Validate Cassandra bin path
        cassandra_path = Path(self.config.cassandra_bin_path)
        if not cassandra_path.exists():
            self.logger.error(f"Invalid Cassandra bin path: {self.config.cassandra_bin_path}")
            self.config.cassandra_bin_path = self._default_config.cassandra_bin_path
            self.logger.info(f"Falling back to default Cassandra path: {self.config.cassandra_bin_path}")
        
        # Check if nodetool is executable
        nodetool_path = cassandra_path / "nodetool"
        if cassandra_path.exists() and not nodetool_path.exists():
            self.logger.warning(f"nodetool not found in {cassandra_path}")
    
    def validate_paths(self) -> bool:
        """Validate configured paths for existence and executability.
        
        Returns:
            True if all paths are valid, False otherwise
        """
        if not self.config:
            self.load_config()
        
        java_home_path = Path(self.config.java_home)
        cassandra_bin_path = Path(self.config.cassandra_bin_path)
        
        java_home_valid = java_home_path.exists()
        cassandra_bin_valid = cassandra_bin_path.exists()
        
        if not java_home_valid:
            self.logger.warning(f"JAVA_HOME path does not exist: {self.config.java_home}")
        else:
            # Check for java executable
            java_executable = java_home_path / "bin" / "java"
            if not java_executable.exists():
                self.logger.warning(f"Java executable not found at {java_executable}")
                java_home_valid = False
        
        if not cassandra_bin_valid:
            self.logger.warning(f"Cassandra bin path does not exist: {self.config.cassandra_bin_path}")
        else:
            # Check for nodetool executable
            nodetool_path = cassandra_bin_path / "nodetool"
            if not nodetool_path.exists():
                self.logger.warning(f"nodetool not found at {nodetool_path}")
                cassandra_bin_valid = False
            elif not os.access(nodetool_path, os.X_OK):
                self.logger.warning(f"nodetool is not executable: {nodetool_path}")
                cassandra_bin_valid = False
        
        return java_home_valid and cassandra_bin_valid
    
    def get_java_home(self) -> str:
        """Get JAVA_HOME path.
        
        Returns:
            Path to Java installation
        """
        if not self.config:
            self.load_config()
        return self.config.java_home
    
    def get_cassandra_bin_path(self) -> str:
        """Get Cassandra bin path.
        
        Returns:
            Path to Cassandra bin directory
        """
        if not self.config:
            self.load_config()
        return self.config.cassandra_bin_path
    
    def reload_config(self) -> None:
        """Reload configuration from file without restarting the service.
        
        This supports hot-reloading of configuration changes.
        """
        self.logger.info("Hot-reloading configuration")
        old_config = self.config
        
        try:
            self.load_config()
            self.logger.info("Configuration reloaded successfully")
            
            # Log what changed
            if old_config:
                if old_config.java_home != self.config.java_home:
                    self.logger.info(f"JAVA_HOME changed: {old_config.java_home} -> {self.config.java_home}")
                if old_config.cassandra_bin_path != self.config.cassandra_bin_path:
                    self.logger.info(f"Cassandra path changed: {old_config.cassandra_bin_path} -> {self.config.cassandra_bin_path}")
                if old_config.log_level != self.config.log_level:
                    self.logger.info(f"Log level changed: {old_config.log_level} -> {self.config.log_level}")
        except Exception as e:
            self.logger.error(f"Error during config reload: {e}")
            # Keep old config if reload fails
            if old_config:
                self.config = old_config
                self.logger.info("Keeping previous configuration due to reload error")
