"""
Video-to-Text Core Components: Data Models and Interfaces.

This package contains the fundamental building blocks of the Video-to-Text application,
including data models, interfaces, and contracts that define the application's
architecture. These components provide type-safe data structures and abstract
interfaces that enable dependency injection and maintainable code organization.

Features:
- Data Models: Type-safe data classes for transcription operations.
- Abstract Interfaces: Contracts for service implementations.
- Dependency Injection: Loose coupling through interface-based design.
- Type Safety: Comprehensive type hints for better code reliability.
- Immutable Data: Dataclass-based models for consistent state management.
- Validation Support: Built-in validation for data integrity.
- Extensibility: Easy to extend with new models and interfaces.

Components:
- TranscriptionRequest: Request data for transcription operations
- TranscriptionResult: Result data with success/error information
- ProgressUpdate: Progress tracking data structure
- ApplicationSettings: Configuration and preferences data
- Service Interfaces: Abstract base classes for service implementations

Usage:
Import models and interfaces for type annotations and data handling:
    from app.core.models import TranscriptionRequest, TranscriptionResult
    from app.core.interfaces import ITranscriptionService

Dependencies:
- Python 3.8+: Core language with dataclass support
- typing: Type hint support for better code quality
- abc: Abstract base class support for interfaces

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

from .models import TranscriptionRequest, TranscriptionResult, ProgressUpdate, ApplicationSettings
from .interfaces import (
    ITranscriptionService, IFileManager, ISettingsManager, 
    IProgressReporter, IGUIPanel, ITranscriptionController
)

__all__ = [
    'TranscriptionRequest',
    'TranscriptionResult', 
    'ProgressUpdate',
    'ApplicationSettings',
    'ITranscriptionService',
    'IFileManager',
    'ISettingsManager',
    'IProgressReporter',
    'IGUIPanel',
    'ITranscriptionController'
]