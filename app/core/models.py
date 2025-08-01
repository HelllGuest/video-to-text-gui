"""
Video-to-Text Core Data Models: Type-Safe Data Structures.

This module defines the fundamental data structures used throughout the Video-to-Text
application. These dataclass-based models provide type safety, immutability, and
clear contracts for data exchange between different application layers. Each model
represents a specific aspect of the transcription workflow or application state.

Features:
- Type-Safe Data Classes: Comprehensive type hints for all attributes.
- Immutable Design: Dataclass structures for consistent state management.
- Validation Ready: Structured data that supports validation workflows.
- Serialization Support: Compatible with JSON serialization for persistence.
- Documentation: Clear attribute documentation for maintainability.
- Extensibility: Easy to extend with additional fields and models.

Models:
- TranscriptionRequest: Contains all parameters for a transcription operation
- TranscriptionResult: Encapsulates the outcome of transcription processing
- ProgressUpdate: Tracks progress during long-running operations
- ApplicationSettings: Stores user preferences and configuration data

Usage:
Create and use data models for type-safe operations:
    request = TranscriptionRequest(
        video_path="video.mp4",
        output_path="transcript.txt",
        output_format="txt",
        verbose=True,
        timestamp=datetime.now()
    )

Dependencies:
- Python 3.8+: Dataclass support and type hints
- dataclasses: For creating structured data classes
- datetime: For timestamp handling
- typing: Advanced type hint support

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TranscriptionRequest:
    """
    Represents a request to transcribe a video file.
    
    Attributes:
        video_path: Path to the video file to transcribe
        output_path: Path where the transcript should be saved
        output_format: Format for the output ('txt' or 'json')
        verbose: Whether to enable verbose logging
        timestamp: When the request was created
    """
    video_path: str
    output_path: str
    output_format: str  # 'txt' or 'json'
    verbose: bool
    timestamp: datetime


@dataclass
class TranscriptionResult:
    """
    Represents the result of a transcription operation.
    
    Attributes:
        success: Whether the transcription completed successfully
        transcript: The transcribed text content
        error_message: Error message if transcription failed
        processing_time: Time taken to complete the transcription
        output_file_path: Path to the saved transcript file
    """
    success: bool
    transcript: str
    error_message: Optional[str]
    processing_time: float
    output_file_path: Optional[str]


@dataclass
class ProgressUpdate:
    """
    Represents a progress update during transcription.
    
    Attributes:
        percentage: Completion percentage (0.0 to 100.0)
        current_step: Description of the current processing step
        message: Detailed progress message
        timestamp: When the progress update was created
    """
    percentage: float
    current_step: str
    message: str
    timestamp: datetime


@dataclass
class ApplicationSettings:
    """
    Represents the application's persistent settings.
    
    Attributes:
        default_output_format: Default format for transcript output
        verbose_mode: Whether verbose mode is enabled by default
        last_video_directory: Last directory used for video file selection
        last_output_directory: Last directory used for output file selection
        window_geometry: Window size and position settings
    """
    default_output_format: str
    verbose_mode: bool
    last_video_directory: str
    last_output_directory: str
    window_geometry: str