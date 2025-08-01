"""
Enhanced Configuration panel for the Video-to-Text application.

This module contains the ConfigurationPanel class which provides organized
settings management with proper grouping, validation, and user-friendly controls.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
import os
from pathlib import Path

from ..core.interfaces import IGUIPanel, ISettingsManager
from ..core.models import ApplicationSettings
from ..utils.platform_utils import PathUtils


class ConfigurationPanel(IGUIPanel):
    """
    Enhanced GUI panel for configuring application settings.
    
    This class provides organized settings with proper grouping:
    - Output Settings (format, location preferences)
    - Processing Settings (verbose mode, performance options)
    - Application Settings (logging, auto-save, etc.)
    """
    
    def __init__(self, parent_frame: ttk.Frame, 
                 settings_manager: Optional[ISettingsManager] = None,
                 on_settings_change: Optional[Callable[[], None]] = None):
        """
        Initialize the enhanced configuration panel.
        
        Args:
            parent_frame: Parent tkinter frame to contain this panel
            settings_manager: Optional settings manager for persistence
            on_settings_change: Optional callback when settings change
        """
        self.parent_frame = parent_frame
        self.settings_manager = settings_manager
        self.on_settings_change = on_settings_change
        
        # Initialize variables for Output Settings
        self.output_format_var = tk.StringVar()
        self.default_output_dir_var = tk.StringVar()
        
        # Initialize variables for Processing Settings
        self.verbose_mode_var = tk.BooleanVar()
        
        # Track current settings
        self.settings: Optional[ApplicationSettings] = None
        self._change_handlers_enabled = True
        
        # Initialize the panel
        self.initialize()
        
    def initialize(self) -> None:
        """Initialize the panel and its components."""
        self._load_settings()
        self._create_widgets()
        self._setup_bindings()
        self._apply_settings()
    
    def _load_settings(self) -> None:
        """Load settings from the settings manager."""
        if self.settings_manager:
            try:
                self.settings = self.settings_manager.load_settings()
            except Exception:
                self.settings = self.settings_manager.get_default_settings()
        else:
            # Use default settings if no manager provided
            self.settings = ApplicationSettings(
                default_output_format='txt',
                verbose_mode=False,
                last_video_directory='',
                last_output_directory='',
                window_geometry='800x600+100+100'
            )
    
    def _create_widgets(self) -> None:
        """Create and arrange the GUI widgets with proper grouping."""
        # Configure parent frame
        self.parent_frame.grid_columnconfigure(0, weight=1)
        
        # Create main scrollable frame
        self._create_scrollable_frame()
        
        # Create grouped sections
        self._create_output_settings_group()
        self._create_processing_settings_group()
        self._create_advanced_settings_group()
        
        # Create action buttons
        self._create_action_buttons()
    
    def _create_scrollable_frame(self) -> None:
        """Create a scrollable frame for the settings."""
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.parent_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.parent_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid the canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure parent frame weights
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mousewheel to canvas
        self._bind_mousewheel()
    
    def _bind_mousewheel(self) -> None:
        """Bind mousewheel events to the canvas."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def _create_output_settings_group(self) -> None:
        """Create the Output Settings group."""
        group_frame = ttk.LabelFrame(
            self.scrollable_frame, 
            text="Output Settings", 
            padding="15"
        )
        group_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        group_frame.grid_columnconfigure(1, weight=1)
        
        # Output Format
        ttk.Label(group_frame, text="Output Format:").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        
        format_frame = ttk.Frame(group_frame)
        format_frame.grid(row=0, column=1, sticky="ew", pady=(0, 10))
        
        self.txt_radio = ttk.Radiobutton(
            format_frame,
            text="Plain Text (.txt)",
            variable=self.output_format_var,
            value="txt"
        )
        self.txt_radio.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        self.json_radio = ttk.Radiobutton(
            format_frame,
            text="JSON (.json)",
            variable=self.output_format_var,
            value="json"
        )
        self.json_radio.grid(row=0, column=1, sticky="w")
        
        # Format description
        self.format_desc_var = tk.StringVar()
        self.format_desc_label = ttk.Label(
            group_frame,
            textvariable=self.format_desc_var,
            font=("TkDefaultFont", 8),
            foreground="gray",
            wraplength=400
        )
        self.format_desc_label.grid(row=1, column=1, sticky="w", pady=(0, 15))
        
        # Default Output Directory
        ttk.Label(group_frame, text="Default Output Directory:").grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        
        dir_frame = ttk.Frame(group_frame)
        dir_frame.grid(row=2, column=1, sticky="ew", pady=(0, 5))
        dir_frame.grid_columnconfigure(0, weight=1)
        
        self.output_dir_entry = ttk.Entry(
            dir_frame,
            textvariable=self.default_output_dir_var,
            state="readonly"
        )
        self.output_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.browse_dir_btn = ttk.Button(
            dir_frame,
            text="Browse...",
            command=self._browse_output_directory,
            width=10
        )
        self.browse_dir_btn.grid(row=0, column=1)
        
        self.clear_dir_btn = ttk.Button(
            dir_frame,
            text="Clear",
            command=self._clear_output_directory,
            width=8
        )
        self.clear_dir_btn.grid(row=0, column=2, padx=(5, 0))
        

    
    def _create_processing_settings_group(self) -> None:
        """Create the Processing Settings group."""
        group_frame = ttk.LabelFrame(
            self.scrollable_frame, 
            text="Processing Settings", 
            padding="15"
        )
        group_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        group_frame.grid_columnconfigure(1, weight=1)
        
        # Verbose Mode
        self.verbose_cb = ttk.Checkbutton(
            group_frame,
            text="Enable verbose logging",
            variable=self.verbose_mode_var
        )
        self.verbose_cb.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        verbose_desc = ttk.Label(
            group_frame,
            text="Show detailed progress messages and debugging information during transcription.",
            font=("TkDefaultFont", 8),
            foreground="gray",
            wraplength=400
        )
        verbose_desc.grid(row=1, column=0, columnspan=2, sticky="w")
    
    def _create_advanced_settings_group(self) -> None:
        """Create the Advanced Settings group."""
        group_frame = ttk.LabelFrame(
            self.scrollable_frame, 
            text="Advanced Settings", 
            padding="15"
        )
        group_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        group_frame.grid_columnconfigure(1, weight=1)
        
        # Settings file management
        ttk.Label(group_frame, text="Settings Management:").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        
        settings_frame = ttk.Frame(group_frame)
        settings_frame.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        
        self.export_settings_btn = ttk.Button(
            settings_frame,
            text="Export Settings",
            command=self._export_settings,
            width=15
        )
        self.export_settings_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.import_settings_btn = ttk.Button(
            settings_frame,
            text="Import Settings",
            command=self._import_settings,
            width=15
        )
        self.import_settings_btn.grid(row=0, column=1)
    
    def _create_action_buttons(self) -> None:
        """Create action buttons at the bottom."""
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(15, 10))
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Center the buttons
        center_frame = ttk.Frame(button_frame)
        center_frame.grid(row=0, column=0)
        
        self.save_btn = ttk.Button(
            center_frame,
            text="Save Settings",
            command=self._save_settings,
            style="Accent.TButton",
            width=15
        )
        self.save_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.reset_btn = ttk.Button(
            center_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            width=15
        )
        self.reset_btn.grid(row=0, column=1)
    
    def _setup_bindings(self) -> None:
        """Set up event bindings for the widgets."""
        # Bind change events to all variables
        self.output_format_var.trace_add("write", self._on_setting_change)
        self.default_output_dir_var.trace_add("write", self._on_setting_change)
        self.verbose_mode_var.trace_add("write", self._on_setting_change)
    
    def _apply_settings(self) -> None:
        """Apply loaded settings to the GUI widgets."""
        if not self.settings:
            return
        
        self._change_handlers_enabled = False
        
        try:
            # Apply basic settings
            self.output_format_var.set(self.settings.default_output_format)
            self.verbose_mode_var.set(self.settings.verbose_mode)
            self.default_output_dir_var.set(self.settings.last_output_directory)
            
        finally:
            self._change_handlers_enabled = True
        
        # Update format description
        self._update_format_description()
    
    def _on_setting_change(self, *args) -> None:
        """Handle setting changes."""
        if not self._change_handlers_enabled:
            return
        
        # Update format description if format changed
        self._update_format_description()
        
        # Notify parent of changes
        if self.on_settings_change:
            self.on_settings_change()
    
    def _update_format_description(self) -> None:
        """Update the format description based on current selection."""
        format_type = self.output_format_var.get()
        
        if format_type == "txt":
            description = "Plain text format: Simple, readable text file containing only the transcribed content."
        elif format_type == "json":
            description = "JSON format: Structured data with metadata including timestamps, word count, and processing information."
        else:
            description = ""
        
        self.format_desc_var.set(description)
    
    def _browse_output_directory(self) -> None:
        """Browse for default output directory."""
        current_dir = self.default_output_dir_var.get()
        if not current_dir or not os.path.exists(current_dir):
            current_dir = PathUtils.get_default_directory("documents")
        
        directory = filedialog.askdirectory(
            title="Select Default Output Directory",
            initialdir=current_dir
        )
        
        if directory:
            self.default_output_dir_var.set(directory)
    
    def _clear_output_directory(self) -> None:
        """Clear the default output directory."""
        self.default_output_dir_var.set("")
    

    
    def _export_settings(self) -> None:
        """Export current settings to a file."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                import json
                settings_dict = self._get_current_settings_dict()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(settings_dict, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Settings exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export settings: {str(e)}")
    
    def _import_settings(self) -> None:
        """Import settings from a file."""
        try:
            filename = filedialog.askopenfilename(
                title="Import Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                import json
                
                with open(filename, 'r', encoding='utf-8') as f:
                    settings_dict = json.load(f)
                
                self._apply_settings_dict(settings_dict)
                messagebox.showinfo("Success", "Settings imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not import settings: {str(e)}")
    
    def _save_settings(self) -> None:
        """Save current settings."""
        if not self.settings_manager:
            messagebox.showwarning("Warning", "No settings manager available.")
            return
        
        try:
            # Update settings object with current values
            self._update_settings_object()
            
            # Save to persistent storage
            self.settings_manager.save_settings(self.settings)
            
            # Show brief confirmation
            self.parent_frame.after(100, lambda: self._show_save_confirmation())
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {str(e)}")
    
    def _show_save_confirmation(self) -> None:
        """Show a brief save confirmation."""
        # Create a temporary label to show save confirmation
        confirm_label = ttk.Label(
            self.scrollable_frame,
            text="Settings saved successfully",
            foreground="green",
            font=("TkDefaultFont", 8)
        )
        confirm_label.grid(row=4, column=0, pady=5)
        
        # Remove the label after 2 seconds
        self.parent_frame.after(2000, confirm_label.destroy)
    
    def _reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?"
        )
        
        if result:
            self.reset()
    

    
    def _get_current_settings_dict(self) -> dict:
        """Get current settings as a dictionary."""
        return {
            'default_output_format': self.output_format_var.get(),
            'verbose_mode': self.verbose_mode_var.get(),
            'last_output_directory': self.default_output_dir_var.get()
        }
    
    def _apply_settings_dict(self, settings_dict: dict) -> None:
        """Apply settings from a dictionary."""
        self._change_handlers_enabled = False
        
        try:
            for key, value in settings_dict.items():
                if key == 'default_output_format':
                    self.output_format_var.set(value)
                elif key == 'verbose_mode':
                    self.verbose_mode_var.set(value)
                elif key == 'last_output_directory':
                    self.default_output_dir_var.set(value)
        finally:
            self._change_handlers_enabled = True
        
        self._update_format_description()
    
    def _update_settings_object(self) -> None:
        """Update the settings object with current values."""
        if not self.settings:
            return
        
        # Update basic settings
        self.settings.default_output_format = self.output_format_var.get()
        self.settings.verbose_mode = self.verbose_mode_var.get()
        self.settings.last_output_directory = self.default_output_dir_var.get()
    
    # IGUIPanel interface methods
    def reset(self) -> None:
        """Reset the panel to its initial state."""
        if self.settings_manager:
            try:
                default_settings = self.settings_manager.get_default_settings()
                self.settings = default_settings
                self._apply_settings()
                
                # Save the reset settings
                self.settings_manager.save_settings(self.settings)
            except Exception:
                # Use hardcoded defaults if reset fails
                self._apply_hardcoded_defaults()
        else:
            self._apply_hardcoded_defaults()
    
    def _apply_hardcoded_defaults(self) -> None:
        """Apply hardcoded default values."""
        self._change_handlers_enabled = False
        
        try:
            self.output_format_var.set("txt")
            self.verbose_mode_var.set(False)
            self.default_output_dir_var.set("")
        finally:
            self._change_handlers_enabled = True
        
        self._update_format_description()
    
    def validate(self) -> bool:
        """Validate the current state of the panel."""
        try:
            # Check output format
            format_value = self.output_format_var.get()
            if format_value not in ['txt', 'json']:
                return False
            
            # Note: We don't validate the default output directory here because:
            # 1. It's just a default starting location for file dialogs
            # 2. If it doesn't exist, the file dialog will use a fallback
            # 3. The actual output path validation happens in file_selection_panel
            
            return True
        except Exception:
            return False
    
    # Public interface methods
    def get_output_format(self) -> str:
        """Get the selected output format."""
        return self.output_format_var.get()
    
    def set_output_format(self, format_type: str) -> None:
        """Set the output format programmatically."""
        if format_type in ['txt', 'json']:
            self.output_format_var.set(format_type)
    
    def is_verbose_enabled(self) -> bool:
        """Check if verbose mode is enabled."""
        return self.verbose_mode_var.get()
    
    def set_verbose_mode(self, enabled: bool) -> None:
        """Set verbose mode programmatically."""
        self.verbose_mode_var.set(enabled)
    
    def get_current_settings(self) -> dict:
        """Get current configuration settings as a dictionary."""
        return self._get_current_settings_dict()
    
    def apply_settings(self, settings) -> None:
        """Apply settings from a dictionary or ApplicationSettings object."""
        if hasattr(settings, 'default_output_format'):
            # ApplicationSettings object
            self.settings = settings
            self._apply_settings()
        else:
            # Dictionary
            self._apply_settings_dict(settings)