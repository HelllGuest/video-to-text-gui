"""
Video-to-Text Services: Business Logic Layer.

This package contains the business logic services that handle the core
functionality of the Video-to-Text application. The services layer provides
a clean separation between the user interface and the underlying transcription
operations, enabling testability, maintainability, and potential API exposure.

Features:
- Business Logic Separation: Clean separation from GUI and data layers.
- Transcription Services: Core video-to-text conversion functionality.
- Controller Pattern: Coordination between GUI and service operations.
- Threading Support: Background processing with progress reporting.
- Error Handling: Comprehensive error management and recovery.
- Resource Management: Efficient handling of video and audio resources.
- Performance Optimization: Memory management and processing efficiency.
- Extensibility: Easy to add new transcription providers or features.

Services:
- TranscriptionService: Core transcription logic with speech recognition
- TranscriptionController: Coordinates transcription operations with GUI

Usage:
Use services for transcription operations:
    from app.services import TranscriptionService
    service = TranscriptionService()
    result = service.transcribe_video(video_path, progress_callback)

Dependencies:
- Python 3.8+: Core programming language
- moviepy: Video processing and audio extraction
- SpeechRecognition: Speech-to-text conversion
- threading: Background processing support

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

from .transcription_service import TranscriptionService
from .transcription_controller import TranscriptionController

__all__ = [
    'TranscriptionService',
    'TranscriptionController'
]