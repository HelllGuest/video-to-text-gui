"""
Video-to-Text Application Package: Core Application Module.

This package contains the main Video-to-Text application components, providing a complete
solution for converting video files to text transcripts. The application is built with
a modular architecture separating GUI components, core business logic, services, and
utilities for maintainability and extensibility.

Features:
- Modular Architecture: Clean separation of concerns with distinct layers.
- GUI Components: Complete user interface built with tkinter.
- Core Models: Data structures for transcription requests, results, and settings.
- Service Layer: Business logic for transcription operations and file management.
- Utility Modules: Cross-platform utilities, error handling, and validation.
- Settings Management: Persistent configuration with JSON-based storage.
- Performance Monitoring: Resource usage tracking and optimization.
- Error Handling: Centralized error management with user-friendly messages.

Package Structure:
- gui/: User interface components and dialogs
- core/: Core data models and interfaces
- services/: Business logic and transcription services
- utils/: Utility modules and helper functions

Usage:
Import the main application class to create and run the GUI:
    from app import VideoToTextApp
    app = VideoToTextApp()
    app.run()

Dependencies:
- Python 3.8+: Core programming language
- tkinter: GUI framework (included with Python)
- moviepy: Video processing library
- SpeechRecognition: Speech-to-text conversion
- Additional dependencies listed in requirements.txt

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

__version__ = "1.0.0"
__author__ = "Anoop Kumar"
__email__ = "support@videototext.app"

from .gui.app import VideoToTextApp
from .core.models import TranscriptionRequest, TranscriptionResult, ProgressUpdate, ApplicationSettings

__all__ = [
    'VideoToTextApp',
    'TranscriptionRequest', 
    'TranscriptionResult',
    'ProgressUpdate',
    'ApplicationSettings'
]