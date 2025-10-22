"""
Configuration management for Sora 2 Video Generator.
"""

import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """Configuration class for Sora 2 video generation."""
    
    # Default settings
    DEFAULT_SETTINGS = {
        "duration": 4,
        "quality": "standard",
        "aspect_ratio": "16:9",
        "output_dir": "generated_videos",
        "save_metadata": True,
        "max_retries": 3,
        "timeout": 300  # 5 minutes
    }
    
    # Supported parameters
    SUPPORTED_QUALITIES = ["standard", "hd"]
    SUPPORTED_ASPECT_RATIOS = ["16:9", "9:16", "1:1"]
    SUPPORTED_DURATIONS = [4, 8, 12]  # Sora 2 supported durations
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration."""
        self.config_file = Path(config_file)
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file or environment variables."""
        # Load from file if exists
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self.settings.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Override with environment variables
        env_mappings = {
            'SORA_DURATION': 'duration',
            'SORA_QUALITY': 'quality',
            'SORA_ASPECT_RATIO': 'aspect_ratio',
            'SORA_OUTPUT_DIR': 'output_dir',
            'SORA_SAVE_METADATA': 'save_metadata',
            'SORA_MAX_RETRIES': 'max_retries',
            'SORA_TIMEOUT': 'timeout'
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ['duration', 'max_retries', 'timeout']:
                    try:
                        self.settings[config_key] = int(value)
                    except ValueError:
                        print(f"Warning: Invalid {env_var} value: {value}")
                elif config_key == 'save_metadata':
                    self.settings[config_key] = value.lower() in ('true', '1', 'yes')
                else:
                    self.settings[config_key] = value
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            import json
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.settings[key] = value
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        errors = []
        
        # Validate duration
        if not isinstance(self.settings['duration'], int) or self.settings['duration'] not in self.SUPPORTED_DURATIONS:
            errors.append(f"Duration must be one of {self.SUPPORTED_DURATIONS}, got: {self.settings['duration']}")
        
        # Validate quality
        if self.settings['quality'] not in self.SUPPORTED_QUALITIES:
            errors.append(f"Quality must be one of {self.SUPPORTED_QUALITIES}, got: {self.settings['quality']}")
        
        # Validate aspect ratio
        if self.settings['aspect_ratio'] not in self.SUPPORTED_ASPECT_RATIOS:
            errors.append(f"Aspect ratio must be one of {self.SUPPORTED_ASPECT_RATIOS}, got: {self.settings['aspect_ratio']}")
        
        # Validate numeric settings
        if not isinstance(self.settings['max_retries'], int) or self.settings['max_retries'] < 1:
            errors.append(f"Max retries must be a positive integer, got: {self.settings['max_retries']}")
        
        if not isinstance(self.settings['timeout'], int) or self.settings['timeout'] < 1:
            errors.append(f"Timeout must be a positive integer, got: {self.settings['timeout']}")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def get_api_key(self) -> str:
        """Get OpenAI API key from environment or config."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key = self.settings.get('api_key')
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable "
                "or add 'api_key' to your config file."
            )
        return api_key
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"Config({self.settings})"
