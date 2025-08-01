"""
Settings Manager for the Video-to-Text application.

This module provides functionality for loading, saving, and managing
user preferences and application settings with JSON persistence.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.models import ApplicationSettings
from .error_handler import get_error_handler, ErrorCategory
from .validation import SettingsValidator


class SettingsManager:
    """
    Manages application settings persistence using JSON configuration files.
    
    Handles loading, saving, validation, and default initialization of
    user preferences and application settings.
    """
    
    DEFAULT_SETTINGS = {
        'default_output_format': 'txt',
        'verbose_mode': False,
        'last_video_directory': '',
        'last_output_directory': '',
        'window_geometry': '800x600+100+100'
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the SettingsManager.
        
        Args:
            config_dir: Directory to store configuration files. 
                       If None, uses the same directory as the main script
        """
        if config_dir is None:
            main_script_path = Path(__file__).parent.parent.parent / 'main.py'
            if main_script_path.exists():
                self.config_dir = main_script_path.parent
            else:
                self.config_dir = Path.cwd()
        else:
            self.config_dir = Path(config_dir)
        
        self.config_file = self.config_dir / 'settings.json'
        self._ensure_config_directory()
        
        # Set up error handling
        self.error_handler = get_error_handler()
        self.validator = SettingsValidator()
    
    def _ensure_config_directory(self) -> None:
        """Create the configuration directory if it doesn't exist."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.error_handler.handle_settings_error(e, "create config directory", show_dialog=False)
            raise
    
    def load_settings(self) -> ApplicationSettings:
        """
        Load settings from the configuration file.
        
        Returns:
            ApplicationSettings object with loaded or default settings
            
        Raises:
            OSError: If there's an error reading the configuration file
        """
        if not self.config_file.exists():
            return self.get_default_settings()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
            
            validated_settings = self._validate_and_merge_settings(settings_dict)
            
            return ApplicationSettings(**validated_settings)
            
        except (json.JSONDecodeError, OSError) as e:
            self.error_handler.handle_settings_error(e, "load settings", show_dialog=False)
            return self.get_default_settings()
    
    def save_settings(self, settings: ApplicationSettings) -> None:
        """
        Save settings to the configuration file.
        
        Args:
            settings: ApplicationSettings object to save
            
        Raises:
            OSError: If there's an error writing the configuration file
        """
        try:
            settings_dict = self._settings_to_dict(settings)
            validated_settings = self._validate_and_merge_settings(settings_dict)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(validated_settings, f, indent=2, ensure_ascii=False)
            
        except (OSError, TypeError) as e:
            self.error_handler.handle_settings_error(e, "save settings", show_dialog=True)
            raise
    
    def get_default_settings(self) -> ApplicationSettings:
        """
        Get default application settings.
        
        Returns:
            ApplicationSettings object with default values
        """
        return ApplicationSettings(**self.DEFAULT_SETTINGS)
    
    def validate_settings(self, settings: ApplicationSettings) -> bool:
        """
        Validate application settings.
        
        Args:
            settings: ApplicationSettings object to validate
            
        Returns:
            True if settings are valid, False otherwise
        """
        try:
            settings_dict = self._settings_to_dict(settings)
            self._validate_and_merge_settings(settings_dict)
            return True
        except (ValueError, TypeError):
            return False
    
    def _settings_to_dict(self, settings: ApplicationSettings) -> Dict[str, Any]:
        """Convert ApplicationSettings object to dictionary."""
        return {
            'default_output_format': settings.default_output_format,
            'verbose_mode': settings.verbose_mode,
            'last_video_directory': settings.last_video_directory,
            'last_output_directory': settings.last_output_directory,
            'window_geometry': settings.window_geometry
        }
    
    def _validate_and_merge_settings(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate settings dictionary and merge with defaults.
        
        Args:
            settings_dict: Dictionary of settings to validate
            
        Returns:
            Validated and merged settings dictionary
            
        Raises:
            ValueError: If settings contain invalid values
        """
        validated = self.DEFAULT_SETTINGS.copy()
        for key, value in settings_dict.items():
            if key not in self.DEFAULT_SETTINGS:
                continue
            
            if key == 'default_output_format':
                if value not in ['txt', 'json']:
                    raise ValueError(f"Invalid output format: {value}. Must be 'txt' or 'json'")
                validated[key] = value
            
            elif key == 'verbose_mode':
                if not isinstance(value, bool):
                    raise ValueError(f"verbose_mode must be boolean, got {type(value)}")
                validated[key] = value
            
            elif key in ['last_video_directory', 'last_output_directory']:
                if not isinstance(value, str):
                    raise ValueError(f"{key} must be string, got {type(value)}")
                validated[key] = value
            
            elif key == 'window_geometry':
                if not isinstance(value, str):
                    raise ValueError(f"window_geometry must be string, got {type(value)}")
                if value and not self._validate_geometry_string(value):
                    validated[key] = self.DEFAULT_SETTINGS[key]
                else:
                    validated[key] = value
        
        return validated
    
    def _validate_geometry_string(self, geometry: str) -> bool:
        """
        Validate window geometry string format.
        
        Args:
            geometry: Geometry string in format 'widthxheight+x+y' or 'widthxheight-x-y'
            
        Returns:
            True if format is valid, False otherwise
        """
        try:
            if 'x' not in geometry:
                return False
            
            if '+' in geometry:
                size_part, position_part = geometry.split('+', 1)
            elif '-' in geometry:
                parts = geometry.split('-')
                if len(parts) < 2:
                    return False
                size_part = parts[0]
                position_part = '-'.join(parts[1:])
            else:
                return False
            
            if 'x' not in size_part:
                return False
            width, height = size_part.split('x')
            int(width)
            int(height)
            
            position_pattern = r'^[+-]?\d+[+-]\d+$'
            if not re.match(position_pattern, position_part):
                return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def reset_to_defaults(self) -> ApplicationSettings:
        """
        Reset settings to defaults and save to file.
        
        Returns:
            ApplicationSettings object with default values
        """
        default_settings = self.get_default_settings()
        self.save_settings(default_settings)
        return default_settings
    
    def get_config_file_path(self) -> Path:
        """
        Get the path to the configuration file.
        
        Returns:
            Path object pointing to the configuration file
        """
        return self.config_file