"""
Video-to-Text Core Interfaces: Abstract Base Classes and Contracts.

This module defines the abstract interfaces and contracts that various components
of the Video-to-Text application must implement. These interfaces enable loose
coupling, dependency injection, and testability by providing clear contracts
for service implementations. The interface-based design allows for easy
substitution of implementations and promotes clean architecture principles.

Features:
- Abstract Base Classes: Clear contracts for service implementations.
- Dependency Injection: Enables loose coupling between components.
- Testability: Easy to mock and test with interface-based design.
- Type Safety: Comprehensive type hints for all method signatures.
- Documentation: Clear method documentation with parameter descriptions.
- Extensibility: Easy to add new interfaces for additional functionality.
- Consistency: Ensures consistent behavior across implementations.

Interfaces:
- ITranscriptionService: Contract for video transcription services
- IFileManager: Contract for file operations and validation
- ISettingsManager: Contract for configuration management
- IProgressReporter: Contract for progress reporting components
- IGUIPanel: Contract for GUI panel components
- ITranscriptionController: Contract for transcription coordination

Usage:
Implement interfaces to create concrete service classes:
    class MyTranscriptionService(ITranscriptionService):
        def transcribe_video(self, video_path, progress_callback):
            # Implementation here
            pass

Dependencies:
- Python 3.8+: Abstract base class support
- abc: Abstract base class module
- typing: Type hint support for method signatures

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from .models import TranscriptionRequest, TranscriptionResult, ProgressUpdate, ApplicationSettings


class ITranscriptionService(ABC):
    """
    Interface for transcription service implementations.
    
    Defines the contract for services that can transcribe video files
    to text with progress reporting capabilities.
    """
    
    @abstractmethod
    def transcribe_video(self, video_path: str, progress_callback: Callable[[ProgressUpdate], None]) -> TranscriptionResult:
        """
        Transcribe a video file to text.
        
        Args:
            video_path: Path to the video file to transcribe
            progress_callback: Function to call with progress updates
            
        Returns:
            TranscriptionResult containing the transcription outcome
        """
        pass
    
    @abstractmethod
    def cancel_transcription(self) -> None:
        """Cancel the current transcription operation if running."""
        pass


class IFileManager(ABC):
    """
    Interface for file management operations.
    
    Defines the contract for components that handle file validation,
    saving transcripts, and managing temporary files.
    """
    
    @abstractmethod
    def validate_video_file(self, filepath: str) -> bool:
        """
        Validate that a video file exists and is in a supported format.
        
        Args:
            filepath: Path to the video file to validate
            
        Returns:
            True if the file is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> list:
        """
        Get list of supported video file extensions.
        
        Returns:
            List of supported file extensions including the dot
        """
        pass
    
    @abstractmethod
    def save_transcript(self, text: str, filepath: str, format: str) -> bool:
        """
        Save transcript text to a file in the specified format.
        
        Args:
            text: The transcript text to save
            filepath: Path where the transcript should be saved
            format: Output format ('txt' or 'json')
            
        Returns:
            True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_output_path(self, filepath: str) -> bool:
        """
        Validate that an output path is writable and in a valid location.
        
        Args:
            filepath: Path to validate for output
            
        Returns:
            True if the path is valid for output, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_size(self, filepath: str) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            filepath: Path to the file
            
        Returns:
            File size in bytes, or None if file doesn't exist or can't be accessed
        """
        pass
    
    @abstractmethod
    def ensure_extension(self, filepath: str, format: str) -> str:
        """
        Ensure the filepath has the correct extension for the given format.
        
        Args:
            filepath: Original file path
            format: Output format ('txt' or 'json')
            
        Returns:
            File path with correct extension
        """
        pass
    
    @abstractmethod
    def cleanup_temp_files(self) -> None:
        """Clean up any temporary files created during processing."""
        pass


class ISettingsManager(ABC):
    """
    Interface for application settings management.
    
    Defines the contract for components that handle loading,
    saving, and validating application settings.
    """
    
    @abstractmethod
    def load_settings(self) -> ApplicationSettings:
        """
        Load application settings from persistent storage.
        
        Returns:
            ApplicationSettings object with current settings
        """
        pass
    
    @abstractmethod
    def save_settings(self, settings: ApplicationSettings) -> bool:
        """
        Save application settings to persistent storage.
        
        Args:
            settings: ApplicationSettings object to save
            
        Returns:
            True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_default_settings(self) -> ApplicationSettings:
        """
        Get default application settings.
        
        Returns:
            ApplicationSettings object with default values
        """
        pass


class IProgressReporter(ABC):
    """
    Interface for components that can report progress updates.
    
    Defines the contract for components that need to communicate
    progress information to the user interface.
    """
    
    @abstractmethod
    def report_progress(self, update: ProgressUpdate) -> None:
        """
        Report a progress update.
        
        Args:
            update: ProgressUpdate containing current progress information
        """
        pass


class IGUIPanel(ABC):
    """
    Base interface for GUI panel components.
    
    Defines common behavior that all GUI panels should implement
    for consistent user interface management.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the panel and its components."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset the panel to its initial state."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate the current state of the panel.
        
        Returns:
            True if the panel state is valid, False otherwise
        """
        pass


class ITranscriptionController(ABC):
    """
    Interface for transcription controller implementations.
    
    Defines the contract for components that coordinate transcription
    operations between the GUI and service layers.
    """
    
    @abstractmethod
    def start_transcription(self, request: TranscriptionRequest) -> None:
        """
        Start a transcription operation.
        
        Args:
            request: TranscriptionRequest containing operation parameters
        """
        pass
    
    @abstractmethod
    def cancel_transcription(self) -> None:
        """Cancel the current transcription operation."""
        pass
    
    @abstractmethod
    def is_transcription_running(self) -> bool:
        """
        Check if a transcription operation is currently running.
        
        Returns:
            True if transcription is in progress, False otherwise
        """
        pass