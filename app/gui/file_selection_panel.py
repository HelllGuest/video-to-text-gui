"""
File selection panel for the Video-to-Text application.

This module contains the FileSelectionPanel class which provides
video file browser functionality and output location selection.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
from typing import Optional, Callable

from ..core.interfaces import IGUIPanel, IFileManager, ISettingsManager
from ..core.models import ApplicationSettings
from ..utils.error_handler import get_error_handler, ErrorCategory
from ..utils.platform_utils import FileDialogConfig, PathUtils, PLATFORM


class FileSelectionPanel(IGUIPanel):
    """
    GUI panel for selecting video files and output locations.
    
    This class provides file browser dialogs, file path display,
    validation feedback, and support for multiple video formats.
    """
    
    def __init__(self, parent_frame: ttk.Frame, file_manager: IFileManager, 
                 settings_manager: Optional[ISettingsManager] = None,
                 on_selection_change: Optional[Callable[[], None]] = None):
        """
        Initialize the file selection panel.
        
        Args:
            parent_frame: Parent tkinter frame to contain this panel
            file_manager: File manager for validation operations
            settings_manager: Optional settings manager for persistence
            on_selection_change: Optional callback when file selection changes
        """
        self.parent_frame = parent_frame
        self.file_manager = file_manager
        self.settings_manager = settings_manager
        self.on_selection_change = on_selection_change
        
        # Initialize variables
        self.video_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.video_validation_var = tk.StringVar()
        self.output_validation_var = tk.StringVar()
        
        # Track current settings
        self.settings: Optional[ApplicationSettings] = None
        
        # Error handling
        self.error_handler = get_error_handler()
        
        # Initialize the panel
        self.initialize()
        
    def initialize(self) -> None:
        """Initialize the panel and its components."""
        self._load_settings()
        self._create_widgets()
        self._setup_bindings()
        self._update_validation()
    
    def _load_settings(self) -> None:
        """Load settings for default directories."""
        if self.settings_manager:
            try:
                self.settings = self.settings_manager.load_settings()
            except Exception:
                self.settings = self.settings_manager.get_default_settings()
        else:
            # Use default settings if no manager provided
            from ..core.models import ApplicationSettings
            self.settings = ApplicationSettings(
                default_output_format='txt',
                verbose_mode=False,
                last_video_directory=os.path.expanduser('~'),
                last_output_directory=os.path.expanduser('~'),
                window_geometry='800x600'
            )
    
    def _create_widgets(self) -> None:
        """Create and arrange the GUI widgets."""
        # Configure parent frame grid
        self.parent_frame.grid_columnconfigure(1, weight=1)
        
        # Video file selection row
        video_label = ttk.Label(self.parent_frame, text="Video File:")
        video_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        
        self.video_entry = ttk.Entry(
            self.parent_frame, 
            textvariable=self.video_file_var,
            state="readonly"
        )
        self.video_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(0, 5))
        
        self.video_browse_btn = ttk.Button(
            self.parent_frame,
            text="Browse...",
            command=self.browse_video_file
        )
        self.video_browse_btn.grid(row=0, column=2, pady=(0, 5))
        
        # Video file validation feedback
        self.video_validation_label = ttk.Label(
            self.parent_frame,
            textvariable=self.video_validation_var,
            foreground="red",
            font=("TkDefaultFont", 8)
        )
        self.video_validation_label.grid(row=1, column=1, sticky="w", pady=(0, 10))
        
        # Output file selection row
        output_label = ttk.Label(self.parent_frame, text="Output File:")
        output_label.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        
        self.output_entry = ttk.Entry(
            self.parent_frame,
            textvariable=self.output_file_var
        )
        self.output_entry.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(0, 5))
        
        self.output_browse_btn = ttk.Button(
            self.parent_frame,
            text="Save As...",
            command=self.browse_output_location
        )
        self.output_browse_btn.grid(row=2, column=2, pady=(0, 5))
        
        # Output file validation feedback
        self.output_validation_label = ttk.Label(
            self.parent_frame,
            textvariable=self.output_validation_var,
            foreground="red",
            font=("TkDefaultFont", 8)
        )
        self.output_validation_label.grid(row=3, column=1, sticky="w", pady=(0, 5))
        
        # File info display
        self.info_frame = ttk.Frame(self.parent_frame)
        self.info_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        self.info_frame.grid_columnconfigure(1, weight=1)
        
        self.file_info_var = tk.StringVar()
        self.file_info_label = ttk.Label(
            self.info_frame,
            textvariable=self.file_info_var,
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        self.file_info_label.grid(row=0, column=0, sticky="w")
    
    def _setup_bindings(self) -> None:
        """Set up event bindings for the widgets."""
        # Bind validation to text changes
        self.video_file_var.trace_add("write", self._on_video_file_change)
        self.output_file_var.trace_add("write", self._on_output_file_change)
        
        # Allow manual editing of output path
        self.output_entry.bind("<KeyRelease>", self._on_output_entry_change)
        self.output_entry.bind("<FocusOut>", self._on_output_entry_change)
    
    def _on_video_file_change(self, *args) -> None:
        """Handle video file path changes."""
        video_path = self.video_file_var.get()
        
        # Auto-generate output path if video file is valid and output is empty
        if video_path and not self.output_file_var.get():
            self._auto_generate_output_path(video_path)
        
        self._update_validation()
        self._update_file_info()
        if self.on_selection_change:
            self.parent_frame.after_idle(self.on_selection_change)
    
    def _on_output_file_change(self, *args) -> None:
        """Handle output file path changes."""
        self._update_validation()
        if self.on_selection_change:
            self.parent_frame.after_idle(self.on_selection_change)
    
    def _on_output_entry_change(self, event=None) -> None:
        """Handle manual changes to output entry."""
        # Update the StringVar with the current entry content
        current_text = self.output_entry.get()
        if current_text != self.output_file_var.get():
            self.output_file_var.set(current_text)
    
    def browse_video_file(self) -> None:
        """Open file dialog to select a video file."""
        # Get platform-appropriate file types
        filetypes = FileDialogConfig.get_video_file_types()
        
        # Determine initial directory using platform utils
        initial_dir = self.settings.last_video_directory if self.settings else PathUtils.get_default_directory("videos")
        if not os.path.exists(initial_dir):
            initial_dir = PathUtils.get_default_directory("home")
        
        # Get platform-specific dialog options
        dialog_options = FileDialogConfig.get_dialog_options()
        
        try:
            filename = filedialog.askopenfilename(
                title="Select Video File",
                initialdir=initial_dir,
                filetypes=filetypes,
                **dialog_options
            )
            
            if filename:
                # Normalize path for platform
                normalized_path = PathUtils.normalize_path(filename)
                self.video_file_var.set(normalized_path)
                
                # Update last video directory in settings
                if self.settings:
                    self.settings.last_video_directory = os.path.dirname(normalized_path)
                    self._save_settings()
                
                # Auto-generate output filename if not set
                if not self.output_file_var.get():
                    self._auto_generate_output_path(normalized_path)
                
                # Force validation update after auto-generation
                self._update_validation()
                
                # Trigger selection change callback after everything is set up
                # Use idle_add to ensure it runs after all pending UI updates
                if self.on_selection_change:
                    self.parent_frame.after_idle(self.on_selection_change)
                    
        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.GUI,
                user_message="An error occurred while selecting the video file",
                show_dialog=True
            )
    
    def browse_output_location(self) -> None:
        """Open save dialog to select output location."""
        # Determine initial directory using platform utils
        initial_dir = self.settings.last_output_directory if self.settings else PathUtils.get_default_directory("documents")
        if not os.path.exists(initial_dir):
            initial_dir = PathUtils.get_default_directory("home")
        
        # Generate default filename based on video file
        default_name = ""
        video_path = self.video_file_var.get()
        if video_path:
            video_name = Path(video_path).stem
            default_name = f"{video_name}_transcript.txt"
        
        # Get platform-appropriate file types
        filetypes = FileDialogConfig.get_transcript_file_types()
        
        # Get platform-specific dialog options
        dialog_options = FileDialogConfig.get_dialog_options()
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Transcript As",
                initialdir=initial_dir,
                initialfile=default_name,
                filetypes=filetypes,
                defaultextension=".txt",
                **dialog_options
            )
            
            if filename:
                # Normalize path for platform
                normalized_path = PathUtils.normalize_path(filename)
                self.output_file_var.set(normalized_path)
                
                # Update last output directory in settings
                if self.settings:
                    self.settings.last_output_directory = os.path.dirname(normalized_path)
                    self._save_settings()
                    
        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.GUI,
                user_message="An error occurred while selecting the output location",
                show_dialog=True
            )
    
    def _auto_generate_output_path(self, video_path: str) -> None:
        """
        Auto-generate output path based on video file path.
        
        Args:
            video_path: Path to the selected video file
        """
        try:
            video_file = Path(video_path)
            output_dir = video_file.parent
            
            # Use default format from settings
            format_ext = ".txt"
            if self.settings and self.settings.default_output_format == "json":
                format_ext = ".json"
            
            output_filename = f"{video_file.stem}_transcript{format_ext}"
            output_path = output_dir / output_filename
            
            self.output_file_var.set(str(output_path))
            
        except Exception:
            # If auto-generation fails, leave output path empty
            pass
    
    def _update_validation(self) -> None:
        """Update validation feedback for both file selections."""
        # Validate video file
        video_path = self.video_file_var.get()
        if video_path:
            if hasattr(self.file_manager, 'get_video_validation_result'):
                result = self.file_manager.get_video_validation_result(video_path)
                if result.is_valid:
                    self.video_validation_var.set("")
                    self.video_validation_label.configure(foreground="green")
                else:
                    self.video_validation_var.set(result.error_message or "Invalid video file")
                    self.video_validation_label.configure(foreground="red")
            else:
                # Fallback to simple validation
                if self.file_manager.validate_video_file(video_path):
                    self.video_validation_var.set("")
                    self.video_validation_label.configure(foreground="green")
                else:
                    self.video_validation_var.set("Invalid video file or unsupported format")
                    self.video_validation_label.configure(foreground="red")
        else:
            self.video_validation_var.set("")
        
        # Validate output path
        output_path = self.output_file_var.get()
        if output_path:
            if hasattr(self.file_manager, 'get_output_validation_result'):
                result = self.file_manager.get_output_validation_result(output_path)
                if result.is_valid:
                    if result.warning_message:
                        self.output_validation_var.set(result.warning_message)
                        self.output_validation_label.configure(foreground="orange")
                    else:
                        self.output_validation_var.set("")
                        self.output_validation_label.configure(foreground="green")
                else:
                    self.output_validation_var.set(result.error_message or "Invalid output path")
                    self.output_validation_label.configure(foreground="red")
            else:
                # Fallback to simple validation
                if self.file_manager.validate_output_path(output_path):
                    self.output_validation_var.set("")
                    self.output_validation_label.configure(foreground="green")
                else:
                    self.output_validation_var.set("Invalid output path or location not writable")
                    self.output_validation_label.configure(foreground="red")
        else:
            self.output_validation_var.set("")
    
    def _update_file_info(self) -> None:
        """Update file information display."""
        video_path = self.video_file_var.get()
        if video_path and self.file_manager.validate_video_file(video_path):
            try:
                file_size = self.file_manager.get_file_size(video_path)
                if file_size is not None:
                    # Format file size
                    if file_size < 1024:
                        size_str = f"{file_size} bytes"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f} KB"
                    elif file_size < 1024 * 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
                    
                    file_ext = Path(video_path).suffix.upper()
                    self.file_info_var.set(f"File size: {size_str} | Format: {file_ext}")
                else:
                    self.file_info_var.set("")
            except Exception:
                self.file_info_var.set("")
        else:
            self.file_info_var.set("")
    
    def _save_settings(self) -> None:
        """Save current settings."""
        if self.settings_manager and self.settings:
            try:
                self.settings_manager.save_settings(self.settings)
            except Exception:
                # If saving fails, continue silently
                pass
    
    def reset(self) -> None:
        """Reset the panel to its initial state."""
        self.video_file_var.set("")
        self.output_file_var.set("")
        self.video_validation_var.set("")
        self.output_validation_var.set("")
        self.file_info_var.set("")
    
    def validate(self) -> bool:
        """
        Validate the current state of the panel.
        
        Returns:
            True if both video file and output path are valid, False otherwise
        """
        video_path = self.video_file_var.get()
        output_path = self.output_file_var.get()
        
        # Check if video file is selected and valid
        if not video_path:
            return False
        
        if not self.file_manager.validate_video_file(video_path):
            return False
        
        # Check if output path is specified and valid
        if not output_path:
            # Try to auto-generate if missing
            self._auto_generate_output_path(video_path)
            output_path = self.output_file_var.get()
            
        if not output_path:
            return False
        
        if not self.file_manager.validate_output_path(output_path):
            return False
        
        return True
    
    def get_video_file_path(self) -> str:
        """
        Get the selected video file path.
        
        Returns:
            Path to the selected video file
        """
        return self.video_file_var.get()
    
    def get_output_file_path(self) -> str:
        """
        Get the selected output file path.
        
        Returns:
            Path to the output file
        """
        return self.output_file_var.get()
    
    def set_video_file_path(self, path: str) -> None:
        """
        Set the video file path programmatically.
        
        Args:
            path: Path to the video file
        """
        self.video_file_var.set(path)
    
    def set_output_file_path(self, path: str) -> None:
        """
        Set the output file path programmatically.
        
        Args:
            path: Path to the output file
        """
        self.output_file_var.set(path)
    
    def update_output_format(self, format: str) -> None:
        """
        Update the output file extension based on format.
        
        Args:
            format: Output format ('txt' or 'json')
        """
        current_output = self.output_file_var.get()
        if current_output:
            # Update extension using file manager
            new_path = self.file_manager.ensure_extension(current_output, format)
            if new_path != current_output:
                self.output_file_var.set(new_path)
    
    def is_video_file_selected(self) -> bool:
        """
        Check if a valid video file is selected.
        
        Returns:
            True if a valid video file is selected, False otherwise
        """
        video_path = self.video_file_var.get()
        return bool(video_path and self.file_manager.validate_video_file(video_path))
    
    def is_output_path_valid(self) -> bool:
        """
        Check if the output path is valid.
        
        Returns:
            True if the output path is valid, False otherwise
        """
        output_path = self.output_file_var.get()
        return bool(output_path and self.file_manager.validate_output_path(output_path))
    
    def get_last_video_directory(self) -> str:
        """
        Get the last used video directory.
        
        Returns:
            Last video directory path, or empty string if not available
        """
        if self.settings:
            return self.settings.last_video_directory
        return ""
    
    def get_last_output_directory(self) -> str:
        """
        Get the last used output directory.
        
        Returns:
            Last output directory path, or empty string if not available
        """
        if self.settings:
            return self.settings.last_output_directory
        return ""
    
    def apply_settings(self, settings: ApplicationSettings) -> None:
        """
        Apply settings to the panel.
        
        Args:
            settings: ApplicationSettings object to apply
        """
        self.settings = settings
        # Settings are applied automatically when browsing files
        # No immediate UI updates needed