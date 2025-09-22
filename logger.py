"""
Logging System for Deepgram Medical Dictation Tool
Provides privacy-aware logging with rotation and configurable levels
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class PrivacyFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""
    
    def __init__(self, privacy_mode: bool = True):
        super().__init__()
        self.privacy_mode = privacy_mode
    
    def filter(self, record):
        if self.privacy_mode and hasattr(record, 'msg'):
            # Redact transcribed text
            if 'Transcribed text:' in str(record.msg):
                record.msg = 'Transcribed text: [REDACTED - privacy mode enabled]'
            elif 'Text content:' in str(record.msg):
                record.msg = 'Text content: [REDACTED - privacy mode enabled]'
        return True


class DictationLogger:
    """Custom logger for the dictation application"""
    
    def __init__(self, config):
        """Initialize logger with configuration
        
        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.logger = None
        self.file_handler = None
        self.console_handler = None
        self.privacy_filter = None
        
        if self.config.get('logging.enabled', False):
            self.setup_logger()
    
    def setup_logger(self):
        """Set up the logging system"""
        # Create logger
        self.logger = logging.getLogger('deepgram_dictation')
        
        # Set level from config
        level = getattr(logging, self.config.get('logging.level', 'INFO'))
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create log directory if needed
        log_file = self.config.get('logging.file', './logs/dictation.log')
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Set up file handler with rotation
        max_bytes = self.config.get('logging.max_size_mb', 10) * 1024 * 1024
        self.file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=5,
            encoding='utf-8'
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
        
        # Add privacy filter
        self.privacy_filter = PrivacyFilter(
            self.config.get('logging.privacy_mode', True)
        )
        self.file_handler.addFilter(self.privacy_filter)
        
        # Add file handler to logger
        self.logger.addHandler(self.file_handler)
        
        # Set up console handler if enabled
        if self.config.get('logging.console_output', False):
            self.console_handler = logging.StreamHandler(sys.stdout)
            self.console_handler.setFormatter(formatter)
            self.console_handler.addFilter(self.privacy_filter)
            self.logger.addHandler(self.console_handler)
        
        # Clean old logs
        self.clean_old_logs()
        
        self.logger.info("=" * 50)
        self.logger.info("Deepgram Medical Dictation Tool Started")
        self.logger.info(f"Log level: {self.config.get('logging.level', 'INFO')}")
        self.logger.info(f"Privacy mode: {self.config.get('logging.privacy_mode', True)}")
        self.logger.info("=" * 50)
    
    def clean_old_logs(self):
        """Remove log files older than configured days"""
        try:
            keep_days = self.config.get('logging.keep_days', 7)
            if keep_days <= 0:
                return
            
            log_file = self.config.get('logging.file', './logs/dictation.log')
            log_dir = os.path.dirname(log_file)
            
            if not os.path.exists(log_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for file in Path(log_dir).glob('*.log*'):
                if file.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        file.unlink()
                        if self.logger:
                            self.logger.info(f"Deleted old log file: {file.name}")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Could not delete old log: {e}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cleaning old logs: {e}")
    
    def toggle_logging(self):
        """Toggle logging on/off at runtime"""
        if self.logger:
            # Disable logging
            self.logger.disabled = not self.logger.disabled
            status = "disabled" if self.logger.disabled else "enabled"
            print(f"Logging {status}")
            if not self.logger.disabled:
                self.logger.info(f"Logging {status} at runtime")
        else:
            # Enable logging if it was off
            self.config.set('logging.enabled', True)
            self.setup_logger()
            print("Logging enabled")
    
    def toggle_console_output(self):
        """Toggle console output on/off at runtime"""
        if not self.logger:
            return
        
        if self.console_handler:
            # Remove console handler
            self.logger.removeHandler(self.console_handler)
            self.console_handler = None
            print("Console logging disabled")
        else:
            # Add console handler
            self.console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.console_handler.setFormatter(formatter)
            self.console_handler.addFilter(self.privacy_filter)
            self.logger.addHandler(self.console_handler)
            print("Console logging enabled")
    
    def set_level(self, level: str):
        """Change logging level at runtime
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        if self.logger:
            new_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.setLevel(new_level)
            self.logger.info(f"Log level changed to: {level}")
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        if self.logger:
            self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        if self.logger:
            self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        if self.logger:
            self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        if self.logger:
            self.logger.error(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        if self.logger:
            self.logger.exception(message, *args, **kwargs)
    
    def log_performance(self, operation: str, duration: float, details: Optional[dict] = None):
        """Log performance metrics
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            details: Additional details to log
        """
        if self.logger:
            msg = f"Performance: {operation} took {duration:.3f} seconds"
            if details:
                msg += f" | Details: {details}"
            self.logger.info(msg)
    
    def log_audio_info(self, device_name: str, sample_rate: int, channels: int):
        """Log audio device information
        
        Args:
            device_name: Name of the audio device
            sample_rate: Sample rate in Hz
            channels: Number of channels
        """
        if self.logger:
            self.logger.info(f"Audio device: {device_name}")
            self.logger.debug(f"Audio settings: {sample_rate}Hz, {channels} channel(s)")
    
    def log_api_connection(self, status: str, model: str = None, error: str = None):
        """Log API connection status
        
        Args:
            status: Connection status
            model: Model being used
            error: Error message if any
        """
        if self.logger:
            if status == "connected":
                self.logger.info(f"Connected to Deepgram API (Model: {model})")
            elif status == "disconnected":
                self.logger.info("Disconnected from Deepgram API")
            elif status == "error":
                self.logger.error(f"API connection error: {error}")
            else:
                self.logger.info(f"API connection status: {status}")
    
    def log_transcription(self, duration: float, confidence: float = None, word_count: int = None):
        """Log transcription event
        
        Args:
            duration: Recording duration in seconds
            confidence: Confidence score (0-1)
            word_count: Number of words transcribed
        """
        if self.logger:
            msg = f"Transcription completed: {duration:.1f}s recording"
            if confidence is not None:
                msg += f", confidence: {confidence:.2%}"
            if word_count is not None:
                msg += f", {word_count} words"
            self.logger.info(msg)
    
    def close(self):
        """Clean up logging handlers"""
        if self.logger:
            self.logger.info("Shutting down logger")
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)