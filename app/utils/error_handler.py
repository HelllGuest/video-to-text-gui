"""
Centralized error handling system for the Video-to-Text application.

This module provides comprehensive error handling and user-friendly error message display.
"""

import os
import sys
import traceback
from typing import Optional, Callable, Any, Dict, List
from enum import Enum
import tkinter as tk
from tkinter import messagebox

from ..core.models import ApplicationSettings


class ErrorSeverity(Enum):
    """Enumeration of error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Enumeration of error categories for better organization."""
    FILE_SYSTEM = "FILE_SYSTEM"
    VIDEO_PROCESSING = "VIDEO_PROCESSING"
    SPEECH_RECOGNITION = "SPEECH_RECOGNITION"
    SETTINGS = "SETTINGS"
    GUI = "GUI"
    NETWORK = "NETWORK"
    VALIDATION = "VALIDATION"
    THREADING = "THREADING"
    UNKNOWN = "UNKNOWN"


class ErrorHandler:
    """
    Centralized error handling system with user feedback.
    
    This class provides methods for handling different types of errors
    and displaying user-friendly messages.
    """
    
    def __init__(self, settings: Optional[ApplicationSettings] = None, show_dialogs: bool = True):
        """
        Initialize the error handler.
        
        Args:
            settings: Application settings for configuration
        """
        self.settings = settings
        self._error_counts: Dict[ErrorCategory, int] = {cat: 0 for cat in ErrorCategory}
        self._gui_callback: Optional[Callable[[str, str], None]] = None
        self._show_dialogs = show_dialogs
        
    def set_gui_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Set callback function for GUI error display.
        
        Args:
            callback: Function to call for GUI error display (title, message)
        """
        self._gui_callback = callback
    
    def handle_error(self, error: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.ERROR,
                    context: Optional[Dict[str, Any]] = None, show_dialog: bool = True) -> None:
        """
        Handle an error with appropriate logging and user notification.
        
        Args:
            error: The exception that occurred
            category: Category of the error for organization
            severity: Severity level of the error
            context: Optional context information
            show_dialog: Whether to show a dialog to the user
        """
        # Increment error count for this category
        self._error_counts[category] += 1
        
        # Generate error details
        error_details = self._generate_error_details(error, category, severity, context)
        
        # Display user-friendly message
        if show_dialog:
            self._show_error_dialog(error_details["user_message"], severity, error_details)
    
    def handle_file_error(self, operation: str, filepath: str, error: Exception, 
                         show_dialog: bool = True) -> None:
        """
        Handle file system related errors.
        
        Args:
            operation: Description of the file operation that failed
            filepath: Path to the file that caused the error
            error: The exception that occurred
            show_dialog: Whether to show a dialog to the user
        """
        context = {
            "operation": operation,
            "filepath": filepath,
            "file_exists": os.path.exists(filepath) if filepath else False
        }
        
        self.handle_error(
            error, 
            ErrorCategory.FILE_SYSTEM, 
            ErrorSeverity.ERROR,
            context,
            show_dialog
        )
    
    def handle_video_processing_error(self, error: Exception, video_path: str = "", 
                                    show_dialog: bool = True) -> None:
        """
        Handle video processing related errors.
        
        Args:
            error: The exception that occurred
            video_path: Path to the video file being processed
            show_dialog: Whether to show a dialog to the user
        """
        context = {
            "video_path": video_path,
            "video_exists": os.path.exists(video_path) if video_path else False
        }
        
        self.handle_error(
            error,
            ErrorCategory.VIDEO_PROCESSING,
            ErrorSeverity.ERROR,
            context,
            show_dialog
        )
    
    def handle_speech_recognition_error(self, error: Exception, show_dialog: bool = True) -> None:
        """
        Handle speech recognition related errors.
        
        Args:
            error: The exception that occurred
            show_dialog: Whether to show a dialog to the user
        """
        self.handle_error(
            error,
            ErrorCategory.SPEECH_RECOGNITION,
            ErrorSeverity.ERROR,
            show_dialog=show_dialog
        )
    
    def handle_settings_error(self, error: Exception, operation: str, show_dialog: bool = True) -> None:
        """
        Handle settings related errors.
        
        Args:
            error: The exception that occurred
            operation: Description of the settings operation that failed
            show_dialog: Whether to show a dialog to the user
        """
        context = {"operation": operation}
        
        self.handle_error(
            error,
            ErrorCategory.SETTINGS,
            ErrorSeverity.WARNING,
            context,
            show_dialog
        )
    
    def handle_gui_error(self, error: Exception, component: str = "", show_dialog: bool = True) -> None:
        """
        Handle GUI related errors.
        
        Args:
            error: The exception that occurred
            component: Name of the GUI component that caused the error
            show_dialog: Whether to show a dialog to the user
        """
        context = {"component": component}
        
        self.handle_error(
            error,
            ErrorCategory.GUI,
            ErrorSeverity.ERROR,
            context,
            show_dialog
        )
    
    def _generate_error_details(self, error: Exception, category: ErrorCategory,
                              severity: ErrorSeverity, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate detailed error information.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            severity: Severity level of the error
            context: Optional context information
            
        Returns:
            Dictionary containing detailed error information
        """
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": category.value,
            "severity": severity.value,
            "traceback": traceback.format_exc(),
            "context": context or {},
            "user_message": self._generate_user_friendly_message(error, category),
            "suggestions": self._generate_suggestions(error, category)
        }
    
    def _generate_user_friendly_message(self, error: Exception, category: ErrorCategory) -> str:
        """
        Generate a user-friendly error message.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            
        Returns:
            User-friendly error message
        """
        if category == ErrorCategory.FILE_SYSTEM:
            if isinstance(error, FileNotFoundError):
                return "The specified file could not be found. Please check the file path and try again."
            elif isinstance(error, PermissionError):
                return "Permission denied. Please check file permissions and try again."
            else:
                return f"File operation failed: {str(error)}"
        
        elif category == ErrorCategory.VIDEO_PROCESSING:
            return f"Video processing failed: {str(error)}"
        
        elif category == ErrorCategory.SPEECH_RECOGNITION:
            return f"Speech recognition failed: {str(error)}"
        
        elif category == ErrorCategory.SETTINGS:
            return f"Settings operation failed: {str(error)}"
        
        elif category == ErrorCategory.GUI:
            return f"Interface error: {str(error)}"
        
        else:
            return f"An error occurred: {str(error)}"
    
    def _show_error_dialog(self, message: str, severity: ErrorSeverity,
                          error_details: Dict[str, Any]) -> None:
        """
        Show an error dialog to the user.
        
        Args:
            message: User-friendly error message
            severity: Severity level of the error
            error_details: Detailed error information
        """
        if not self._show_dialogs:
            return

        if self._gui_callback:
            # Use custom GUI callback if available
            title = f"{severity.value}: {error_details['category']}"
            self._gui_callback(title, message)
        else:
            # Fallback to standard messagebox
            if severity == ErrorSeverity.CRITICAL:
                messagebox.showerror("Critical Error", message)
            elif severity == ErrorSeverity.ERROR:
                messagebox.showerror("Error", message)
            elif severity == ErrorSeverity.WARNING:
                messagebox.showwarning("Warning", message)
            else:
                messagebox.showinfo("Information", message)
    
    def _generate_suggestions(self, error: Exception, category: ErrorCategory) -> List[str]:
        """
        Generate helpful suggestions for resolving the error.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            
        Returns:
            List of suggestions for resolving the error
        """
        suggestions = []
        
        if category == ErrorCategory.FILE_SYSTEM:
            if isinstance(error, FileNotFoundError):
                suggestions.extend([
                    "Check that the file path is correct",
                    "Verify that the file exists",
                    "Try browsing for the file instead of typing the path"
                ])
            elif isinstance(error, PermissionError):
                suggestions.extend([
                    "Check file permissions",
                    "Try running the application as administrator",
                    "Make sure the file is not open in another program"
                ])
        
        elif category == ErrorCategory.VIDEO_PROCESSING:
            suggestions.extend([
                "Check that the video file is not corrupted",
                "Try a different video format",
                "Ensure the video file is not too large"
            ])
        
        elif category == ErrorCategory.SPEECH_RECOGNITION:
            suggestions.extend([
                "Check your internet connection",
                "Try a video with clearer audio",
                "Ensure the video contains speech"
            ])
        
        # Add general suggestions
        suggestions.extend([
            "Try the operation again",
            "Restart the application"
        ])
        
        return suggestions
    
    def get_error_counts(self) -> Dict[str, int]:
        """
        Get error count statistics.
        
        Returns:
            Dictionary mapping error categories to their counts
        """
        return {cat.value: count for cat, count in self._error_counts.items()}
    
    def clear_error_counts(self) -> None:
        """Clear error count statistics."""
        self._error_counts = {cat: 0 for cat in ErrorCategory}


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> Optional[ErrorHandler]:
    """
    Get the global error handler instance.
    
    Returns:
        The global ErrorHandler instance, or None if not initialized
    """
    return _global_error_handler


def initialize_error_handler(settings: Optional[ApplicationSettings] = None, show_dialogs: bool = True) -> ErrorHandler:
    """
    Initialize the global error handler.
    
    Args:
        settings: Application settings
        
    Returns:
        The initialized ErrorHandler instance
    """
    global _global_error_handler
    _global_error_handler = ErrorHandler(settings, show_dialogs)
    return _global_error_handler