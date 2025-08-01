"""
Video-to-Text Utilities: Helper Functions and Cross-Platform Support.

This package contains utility modules that provide common functionality
across the Video-to-Text application. These utilities handle cross-platform
operations, file management, error handling, validation, and other support
functions that are used throughout the application.

Features:
- Cross-Platform Support: Platform-specific utilities for Windows, macOS, Linux.
- File Management: Robust file operations with validation and cleanup.
- Error Handling: Centralized error management with user-friendly messages.
- Settings Management: JSON-based configuration persistence.
- Validation: Comprehensive input validation with detailed feedback.
- Performance Monitoring: Resource usage tracking and optimization.
- Version Information: Application metadata and version management.
- Platform Utilities: Native look-and-feel and platform-specific features.

Utilities:
- FileManager: File operations, validation, and temporary file management
- SettingsManager: Configuration persistence and management
- ErrorHandler: Centralized error handling and user feedback
- Validation: Input validation with detailed error messages
- PerformanceMonitor: Resource usage tracking and optimization
- PlatformUtils: Cross-platform compatibility utilities
- VersionInfo: Application version and metadata management

Usage:
Import utilities as needed throughout the application:
    from app.utils import FileManager, SettingsManager
    file_manager = FileManager()
    settings = SettingsManager()

Dependencies:
- Python 3.8+: Core programming language
- json: Configuration file handling
- pathlib: Modern path operations
- Platform-specific libraries for native features

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

from .file_manager import FileManager
from .settings_manager import SettingsManager
from .error_handler import get_error_handler, ErrorCategory, ErrorSeverity
from .validation import FileValidator, SettingsValidator, ValidationResult

__all__ = [
    'FileManager',
    'SettingsManager', 
    'get_error_handler',
    'ErrorCategory',
    'ErrorSeverity',
    'FileValidator',
    'SettingsValidator',
    'ValidationResult'
]