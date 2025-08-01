"""
Enhanced error dialog for the Video-to-Text application.

This module provides a comprehensive error dialog that displays user-friendly
error messages with detailed information and suggested actions.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..utils.error_handler import ErrorSeverity, ErrorCategory


class ErrorDialog:
    """
    Enhanced error dialog with detailed information and suggestions.
    
    This dialog provides a user-friendly way to display errors with
    detailed information, suggestions for resolution, and error logging.
    """
    
    def __init__(self, parent: tk.Tk, title: str, message: str,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 details: Optional[str] = None,
                 suggestions: Optional[List[str]] = None,
                 error_info: Optional[Dict[str, Any]] = None):
        """
        Initialize the error dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Main error message
            severity: Error severity level
            details: Detailed error information
            suggestions: List of suggested actions
            error_info: Additional error information
        """
        self.parent = parent
        self.title = title
        self.message = message
        self.severity = severity
        self.details = details
        self.suggestions = suggestions or []
        self.error_info = error_info or {}
        
        self.dialog = None
        self.result = None
        
    def show(self) -> Optional[str]:
        """
        Show the error dialog and return user's choice.
        
        Returns:
            User's choice ('ok', 'retry', 'ignore', etc.) or None if closed
        """
        self._create_dialog()
        self._setup_ui()
        
        # Center the dialog
        self._center_dialog()
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Wait for user response
        self.dialog.wait_window()
        
        return self.result
    
    def _create_dialog(self) -> None:
        """Create the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.resizable(True, True)
        self.dialog.minsize(400, 300)
        
        # Handle window closing
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_ui(self) -> None:
        """Set up the dialog user interface."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header frame with message
        self._create_header(main_frame)
        
        # Content notebook for organized information
        self._create_content_notebook(main_frame)
        
        # Button frame
        self._create_buttons(main_frame)
    
    def _create_header(self, parent: ttk.Frame) -> None:
        """Create the header section with main message."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Main message
        message_label = ttk.Label(
            header_frame,
            text=self.message,
            font=("TkDefaultFont", 10, "bold"),
            wraplength=350,
            justify="left"
        )
        message_label.grid(row=0, column=0, sticky="ew")
    
    def _create_content_notebook(self, parent: ttk.Frame) -> None:
        """Create the content notebook with different information tabs."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        # Suggestions tab
        if self.suggestions:
            self._create_suggestions_tab()
        
        # Details tab
        if self.details:
            self._create_details_tab()
        
        # Error info tab
        if self.error_info:
            self._create_error_info_tab()
    
    def _create_suggestions_tab(self) -> None:
        """Create the suggestions tab."""
        suggestions_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(suggestions_frame, text="Suggestions")
        
        suggestions_frame.grid_rowconfigure(0, weight=1)
        suggestions_frame.grid_columnconfigure(0, weight=1)
        
        # Suggestions text
        suggestions_text = scrolledtext.ScrolledText(
            suggestions_frame,
            height=8,
            width=50,
            wrap=tk.WORD,
            state="disabled",
            font=("TkDefaultFont", 9)
        )
        suggestions_text.grid(row=0, column=0, sticky="nsew")
        
        # Add suggestions content
        suggestions_text.configure(state="normal")
        suggestions_text.insert(tk.END, "Suggested actions to resolve this issue:\n\n")
        
        for i, suggestion in enumerate(self.suggestions, 1):
            suggestions_text.insert(tk.END, f"{i}. {suggestion}\n\n")
        
        suggestions_text.configure(state="disabled")
    
    def _create_details_tab(self) -> None:
        """Create the details tab."""
        details_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(details_frame, text="Details")
        
        details_frame.grid_rowconfigure(0, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)
        
        # Details text
        details_text = scrolledtext.ScrolledText(
            details_frame,
            height=8,
            width=50,
            wrap=tk.WORD,
            state="disabled",
            font=("Consolas", 9)
        )
        details_text.grid(row=0, column=0, sticky="nsew")
        
        # Add details content
        details_text.configure(state="normal")
        details_text.insert(tk.END, self.details)
        details_text.configure(state="disabled")
    
    def _create_error_info_tab(self) -> None:
        """Create the error information tab."""
        info_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(info_frame, text="Error Info")
        
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Info text
        info_text = scrolledtext.ScrolledText(
            info_frame,
            height=8,
            width=50,
            wrap=tk.WORD,
            state="disabled",
            font=("Consolas", 9)
        )
        info_text.grid(row=0, column=0, sticky="nsew")
        
        # Add error info content
        info_text.configure(state="normal")
        info_text.insert(tk.END, "Error Information:\n\n")
        
        for key, value in self.error_info.items():
            info_text.insert(tk.END, f"{key}: {value}\n")
        
        info_text.configure(state="disabled")
    
    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create the button frame."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky="ew")
        
        # Configure button layout
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Button container (right-aligned)
        button_container = ttk.Frame(button_frame)
        button_container.grid(row=0, column=0, sticky="e")
        
        # Determine buttons based on severity
        if self.severity == ErrorSeverity.CRITICAL:
            # Critical errors: only OK button
            ok_button = ttk.Button(
                button_container,
                text="OK",
                command=self._on_ok,
                width=10
            )
            ok_button.grid(row=0, column=0, padx=(0, 5))
            
        elif self.severity == ErrorSeverity.ERROR:
            # Errors: OK and Retry buttons
            retry_button = ttk.Button(
                button_container,
                text="Retry",
                command=self._on_retry,
                width=10
            )
            retry_button.grid(row=0, column=0, padx=(0, 5))
            
            ok_button = ttk.Button(
                button_container,
                text="OK",
                command=self._on_ok,
                width=10
            )
            ok_button.grid(row=0, column=1, padx=(0, 5))
            
        elif self.severity == ErrorSeverity.WARNING:
            # Warnings: Continue, Ignore, and Cancel buttons
            continue_button = ttk.Button(
                button_container,
                text="Continue",
                command=self._on_continue,
                width=10
            )
            continue_button.grid(row=0, column=0, padx=(0, 5))
            
            ignore_button = ttk.Button(
                button_container,
                text="Ignore",
                command=self._on_ignore,
                width=10
            )
            ignore_button.grid(row=0, column=1, padx=(0, 5))
            
            cancel_button = ttk.Button(
                button_container,
                text="Cancel",
                command=self._on_cancel,
                width=10
            )
            cancel_button.grid(row=0, column=2, padx=(0, 5))
            
        else:
            # Info: just OK button
            ok_button = ttk.Button(
                button_container,
                text="OK",
                command=self._on_ok,
                width=10
            )
            ok_button.grid(row=0, column=0, padx=(0, 5))
        
        # Set default button focus
        if hasattr(self, 'ok_button'):
            ok_button.focus_set()
    
    def _center_dialog(self) -> None:
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get dialog dimensions
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Ensure dialog is on screen
        x = max(0, x)
        y = max(0, y)
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _on_ok(self) -> None:
        """Handle OK button click."""
        self.result = "ok"
        self.dialog.destroy()
    
    def _on_retry(self) -> None:
        """Handle Retry button click."""
        self.result = "retry"
        self.dialog.destroy()
    
    def _on_continue(self) -> None:
        """Handle Continue button click."""
        self.result = "continue"
        self.dialog.destroy()
    
    def _on_ignore(self) -> None:
        """Handle Ignore button click."""
        self.result = "ignore"
        self.dialog.destroy()
    
    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.result = "cancel"
        self.dialog.destroy()
    
    def _on_close(self) -> None:
        """Handle window close event."""
        self.result = None
        self.dialog.destroy()


def show_error_dialog(parent: tk.Tk, title: str, message: str,
                     severity: ErrorSeverity = ErrorSeverity.ERROR,
                     details: Optional[str] = None,
                     suggestions: Optional[List[str]] = None,
                     error_info: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Show an error dialog with enhanced information.
    
    Args:
        parent: Parent window
        title: Dialog title
        message: Main error message
        severity: Error severity level
        details: Detailed error information
        suggestions: List of suggested actions
        error_info: Additional error information
        
    Returns:
        User's choice or None if closed
    """
    dialog = ErrorDialog(parent, title, message, severity, details, suggestions, error_info)
    return dialog.show()