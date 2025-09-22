"""
Configuration Manager for Deepgram Medical Dictation Tool
Handles loading, saving, and managing configuration settings
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class ConfigManager:
    """Manages application configuration with encryption support for sensitive data"""
    
    DEFAULT_CONFIG = {
        "api_key": "",
        "push_to_talk_key": "ctrl",
        "preview_mode": True,
        "auto_punctuation": True,
        "model": "nova-3-medical",
        "language": "en-US",
        "save_transcriptions": False,
        "transcription_folder": "./transcriptions",
        "sound_feedback": True,
        "min_recording_duration": 0.5,
        "max_recording_duration": 300,
        "logging": {
            "enabled": False,
            "level": "INFO",
            "file": "./logs/dictation.log",
            "max_size_mb": 10,
            "keep_days": 7,
            "console_output": False,
            "privacy_mode": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_path: Path to configuration file. If None, uses default location
        """
        if config_path is None:
            # Get the directory where the executable is located
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_path = os.path.join(app_dir, "config.json")
        
        self.config_path = config_path
        self.config = self.load_config()
        self._cipher_suite = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default
        
        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = self.DEFAULT_CONFIG.copy()
                self._deep_update(config, user_config)
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                print("Using default configuration.")
        
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path) or '.', exist_ok=True)
            
            # Prepare config for saving (decrypt API key if encrypted)
            save_config = self.config.copy()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_cipher_suite(self) -> Fernet:
        """Get or create cipher suite for encryption
        
        Returns:
            Fernet cipher suite
        """
        if self._cipher_suite is None:
            # Use machine-specific salt for key derivation
            salt = os.environ.get('COMPUTERNAME', 'default').encode()[:16].ljust(16, b'0')
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b"deepgram_dictation_key"))
            self._cipher_suite = Fernet(key)
        
        return self._cipher_suite
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Encrypted API key
        """
        if not api_key:
            return ""
        
        cipher_suite = self.get_cipher_suite()
        encrypted = cipher_suite.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key from storage
        
        Args:
            encrypted_key: Encrypted API key
            
        Returns:
            Plain text API key
        """
        if not encrypted_key:
            return ""
        
        try:
            cipher_suite = self.get_cipher_suite()
            decoded = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # If decryption fails, assume it's not encrypted
            return encrypted_key
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Deep update dictionary
        
        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def create_default_config_file(self) -> bool:
        """Create a default configuration file template
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2)
            print(f"Created default configuration file at: {self.config_path}")
            return True
        except IOError as e:
            print(f"Error creating configuration file: {e}")
            return False