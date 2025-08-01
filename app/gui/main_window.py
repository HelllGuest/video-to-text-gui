"""
Main application window for the Video-to-Text application.

This module contains the MainWindow class which serves as the primary
GUI container and entry point for the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from pathlib import Path
from typing import Optional
from ..core.models import ApplicationSettings
from ..core.interfaces import ISettingsManager
from ..utils.error_handler import get_error_handler, ErrorCategory, initialize_error_handler
from ..utils.platform_utils import (
    get_platform_info, apply_platform_optimizations, StyleUtils, 
    ScreenUtils, PLATFORM
)
from .about_dialog import show_about_dialog
from .help_dialog import show_help_dialog


class MainWindow:
    """
    Main application window that serves as the primary GUI container.
    
    This class handles window initialization, layout management, and
    coordinates between different GUI sections.
    """
    
    def __init__(self, settings_manager: Optional[ISettingsManager] = None):
        """
        Initialize the main window.
        
        Args:
            settings_manager: Optional settings manager for persistence
        """
        self.settings_manager = settings_manager
        self.root = tk.Tk()
        self.settings = None
        
        # Callback for transcription start
        self.on_start_transcription = None
        
        # Initialize error handling
        settings = None
        if self.settings_manager:
            settings = self.settings_manager.load_settings()
        
        self.error_handler = initialize_error_handler(settings=settings)
        self.error_handler.set_gui_callback(self._show_error_dialog)
        

        
        # Initialize window
        self._setup_window()
        self._setup_ui()
        self._setup_event_handlers()

        self._setup_accessibility()
        
        # Load settings if manager is provided
        if self.settings_manager:
            self._load_settings()
    
    def _setup_window(self) -> None:
        """Set up the main window properties and configuration."""
        self.root.title("Video-to-Text")
        
        # Apply platform-specific optimizations
        apply_platform_optimizations(self.root)
        
        # Get screen information for responsive sizing
        screen_info = ScreenUtils.get_screen_info(self.root)
        window_width, window_height = ScreenUtils.calculate_window_size(800, 600, screen_info)
        
        # Set window size and center it
        ScreenUtils.center_window(self.root, window_width, window_height)
        self.root.minsize(600, 400)
        

        
        # Configure window closing behavior
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Apply platform-specific fonts
        self._apply_platform_fonts()
    
    def _setup_ui(self) -> None:
        """Create and arrange the main GUI layout."""
        # Create main container frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure main frame grid weights
        self.main_frame.grid_rowconfigure(0, weight=1)  # Content area
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create main content area with notebook for organized sections
        self.content_notebook = ttk.Notebook(self.main_frame)
        self.content_notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Create container frames for different GUI sections
        self._create_container_frames()
        
        # Create status bar at the bottom
        self._create_status_bar()
    
    def _create_container_frames(self) -> None:
        """Create container frames for different GUI sections."""
        # Main transcription tab
        self.transcription_frame = ttk.Frame(self.content_notebook, padding="10")
        self.content_notebook.add(self.transcription_frame, text="Transcription")
        
        # Configure transcription frame grid
        self.transcription_frame.grid_rowconfigure(3, weight=1)  # Progress/results area
        self.transcription_frame.grid_columnconfigure(0, weight=1)
        
        # File selection section
        self.file_section_frame = ttk.LabelFrame(
            self.transcription_frame,
            text="File Selection",
            padding="10"
        )
        self.file_section_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.file_section_frame.grid_columnconfigure(1, weight=1)
        
        # Control buttons section
        self.controls_frame = ttk.Frame(self.transcription_frame)
        self.controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.controls_frame.grid_columnconfigure(0, weight=1)
        
        # Create control buttons
        self._create_control_buttons()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Progress and results section
        self.progress_results_frame = ttk.Frame(self.transcription_frame)
        self.progress_results_frame.grid(row=2, column=0, sticky="nsew")
        self.progress_results_frame.grid_rowconfigure(1, weight=1)
        self.progress_results_frame.grid_columnconfigure(0, weight=1)
        
        # Progress section
        self.progress_section_frame = ttk.LabelFrame(
            self.progress_results_frame,
            text="Progress",
            padding="10"
        )
        self.progress_section_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.progress_section_frame.grid_columnconfigure(0, weight=1)
        
        # Results section
        self.results_section_frame = ttk.LabelFrame(
            self.progress_results_frame,
            text="Results",
            padding="10"
        )
        self.results_section_frame.grid(row=1, column=0, sticky="nsew")
        self.results_section_frame.grid_rowconfigure(0, weight=1)
        self.results_section_frame.grid_columnconfigure(0, weight=1)
        
        # Settings tab (for advanced configuration)
        self.settings_frame = ttk.Frame(self.content_notebook, padding="10")
        self.content_notebook.add(self.settings_frame, text="Settings")
        

    
    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(
            label="Open Video...",
            command=self._menu_open_video
        )
        file_menu.add_command(
            label="Save Transcript...",
            command=self._menu_save_transcript
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Reset Application",
            command=self._menu_reset
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self.on_closing
        )
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        edit_menu.add_command(
            label="Copy Results",
            command=self._menu_copy_results
        )
        edit_menu.add_command(
            label="Select All",
            command=self._menu_select_all
        )
        
        
        # Transcription menu
        self.transcription_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transcription", menu=self.transcription_menu)
        
        self.transcription_menu.add_command(
            label="Start Transcription",
            command=self._menu_start_transcription
        )
        self.transcription_menu.add_command(
            label="Cancel Transcription",
            command=self._menu_cancel_transcription,
            state="disabled"
        )
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(
            label="How to Use",
            command=self._menu_show_help
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="About",
            command=self._menu_show_about
        )
    
    def _create_control_buttons(self) -> None:
        """Create transcription control buttons."""
        # Center the buttons
        button_frame = ttk.Frame(self.controls_frame)
        button_frame.grid(row=0, column=0)
        
        # Start transcription button
        self.start_button = ttk.Button(
            button_frame,
            text="Start Transcription",
            command=self._on_start_button_clicked,
            style="Accent.TButton"
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Reset button
        self.reset_button = ttk.Button(
            button_frame,
            text="Reset",
            command=self._on_reset_button_clicked
        )
        self.reset_button.grid(row=0, column=1)
        
        # Initially disable start button
        self.start_button.configure(state="disabled")
    
    def _on_start_button_clicked(self) -> None:
        """Handle start transcription button click."""
        if self.on_start_transcription:
            self.on_start_transcription()
    
    def _on_reset_button_clicked(self) -> None:
        """Handle reset button click."""
        # This will be called by the app to reset all panels
        if hasattr(self, 'on_reset_request') and self.on_reset_request:
            self.on_reset_request()
        else:
            self.update_status("Application reset")
    
    def set_reset_callback(self, callback) -> None:
        """Set the callback for reset button."""
        self.on_reset_request = callback
    
    def set_start_transcription_callback(self, callback) -> None:
        """Set the callback for start transcription button."""
        self.on_start_transcription = callback
    
    def enable_start_button(self, enabled: bool = True) -> None:
        """Enable or disable the start transcription button and menu item."""
        state = "normal" if enabled else "disabled"
        self.start_button.configure(state=state)
        
        # Also update the menu item
        if hasattr(self, 'transcription_menu'):
            self.transcription_menu.entryconfig("Start Transcription", state=state)
    
    def set_start_button_text(self, text: str) -> None:
        """Set the text of the start button."""
        self.start_button.configure(text=text)
    
    def enable_cancel_menu(self, enabled: bool = True) -> None:
        """Enable or disable the cancel transcription menu item."""
        if hasattr(self, 'transcription_menu'):
            state = "normal" if enabled else "disabled"
            self.transcription_menu.entryconfig("Cancel Transcription", state=state)
    
    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom of the window."""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.status_frame,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding="5"
        )
        self.status_label.grid(row=0, column=0, sticky="ew")
    

    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for the window."""
        # Handle window resize events
        self.root.bind("<Configure>", self._on_window_configure)
        

    

    
    def _setup_accessibility(self) -> None:
        """Set up accessibility features including tab order."""
        # Define tab order for main controls
        tab_order = [
            # File selection would be added by the file selection panel
            # Configuration would be added by the configuration panel
            self.start_button,
            self.reset_button,
            # Progress and results panels will handle their own tab order
        ]
        
        # Set up tab order
        for i, widget in enumerate(tab_order):
            if widget and hasattr(widget, 'configure'):
                try:
                    # Set tab traversal order
                    if i == 0:
                        widget.focus_set()  # Set initial focus
                except:
                    pass  # Skip if widget doesn't support focus
    
    def _on_window_configure(self, event) -> None:
        """Handle window configuration changes."""
        # Only handle events for the root window
        if event.widget == self.root:
            # Update geometry in settings if available
            if self.settings_manager and self.settings:
                geometry = self.root.geometry()
                self.settings.window_geometry = geometry
                
                # Auto-save window state periodically (debounced)
                if hasattr(self, '_geometry_save_timer'):
                    self.root.after_cancel(self._geometry_save_timer)
                
                # Save after 1 second of no changes (debounced)
                self._geometry_save_timer = self.root.after(1000, self._save_window_state)
    
    def _load_settings(self) -> None:
        """Load application settings."""
        try:
            self.settings = self.settings_manager.load_settings()
            
            # Apply window geometry if available and valid
            if self.settings.window_geometry:
                self._apply_window_geometry(self.settings.window_geometry)
            

                    
        except Exception as e:
            self.error_handler.handle_settings_error(e, "load", show_dialog=False)
            # If loading fails, use defaults
            if self.settings_manager:
                self.settings = self.settings_manager.get_default_settings()
    
    def _apply_window_geometry(self, geometry: str) -> None:
        """
        Apply window geometry with validation and fallback.
        
        Args:
            geometry: Window geometry string in format 'widthxheight+x+y'
        """
        try:
            # Validate geometry is within screen bounds
            if self._is_geometry_valid(geometry):
                self.root.geometry(geometry)
            else:
                self.error_handler.log_warning(
                    f"Window geometry out of bounds: {geometry}, using default"
                )
                # Use default centered geometry
                self.center_window()
                
        except tk.TclError as e:
            self.error_handler.log_warning(
                f"Invalid window geometry: {geometry}",
                context={"error": str(e)}
            )
            # Fallback to default geometry
            self.center_window()
    
    def _is_geometry_valid(self, geometry: str) -> bool:
        """
        Validate that window geometry is within screen bounds.
        
        Args:
            geometry: Window geometry string
            
        Returns:
            True if geometry is valid and within screen bounds
        """
        try:
            # Parse geometry string (e.g., "800x600+100+100")
            if 'x' not in geometry or ('+' not in geometry and '-' not in geometry):
                return False
            
            # Extract dimensions and position
            size_part = geometry.split('+')[0].split('-')[0]
            width, height = map(int, size_part.split('x'))
            
            # Extract position
            if '+' in geometry:
                pos_parts = geometry.split('+')[1:]
                x = int(pos_parts[0])
                y = int(pos_parts[1]) if len(pos_parts) > 1 else 0
            else:
                # Handle negative coordinates
                pos_parts = geometry.split('-')[1:]
                x = -int(pos_parts[0]) if pos_parts else 0
                y = -int(pos_parts[1]) if len(pos_parts) > 1 else 0
            
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Validate dimensions are reasonable
            if width < 400 or height < 300:
                return False
            if width > screen_width or height > screen_height:
                return False
            
            # Validate position is at least partially on screen
            if x + width < 0 or y + height < 0:
                return False
            if x > screen_width or y > screen_height:
                return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def _save_settings(self) -> None:
        """Save current application settings."""
        if self.settings_manager and self.settings:
            try:
                # Update current window geometry
                self.settings.window_geometry = self.root.geometry()
                self.settings_manager.save_settings(self.settings)
            except Exception as e:
                self.error_handler.handle_settings_error(e, "save", show_dialog=False)
    
    def _save_window_state(self) -> None:
        """Save window state (debounced method for frequent updates)."""
        if self.settings_manager and self.settings:
            try:
                # Update current window geometry
                current_geometry = self.root.geometry()
                if current_geometry != self.settings.window_geometry:
                    self.settings.window_geometry = current_geometry
                    self.settings_manager.save_settings(self.settings)
            except Exception as e:
                # Silently handle errors for frequent updates
                pass
    
    def on_closing(self) -> None:
        """Handle application closing event."""
        try:
            # Check if we should confirm closing
            if self._should_confirm_close():
                if not self._confirm_close():
                    return  # User cancelled closing
            
            # Save settings before closing
            self._save_settings()
            
            # Destroy the window
            self.root.destroy()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.GUI,
                user_message="Error occurred while closing application",
                show_dialog=False
            )
            # Ensure window closes even if there are errors
            try:
                self.root.destroy()
            except:
                pass
            sys.exit(1)
    
    def _should_confirm_close(self) -> bool:
        """
        Check if closing should be confirmed.
        
        Returns:
            True if confirmation is needed, False otherwise
        """
        # This will be set by the application when transcription is running
        return getattr(self, '_transcription_running', False)
    
    def _confirm_close(self) -> bool:
        """
        Show confirmation dialog for closing.
        
        Returns:
            True if user confirms closing, False otherwise
        """
        try:
            result = messagebox.askyesno(
                "Confirm Exit",
                "Transcription is currently running. Are you sure you want to exit?\n\n"
                "This will cancel the current operation.",
                icon="warning"
            )
            return result
        except Exception:
            # If dialog fails, assume user wants to close
            return True
    
    def set_transcription_running(self, running: bool) -> None:
        """
        Set the transcription running state for close confirmation.
        
        Args:
            running: True if transcription is running, False otherwise
        """
        self._transcription_running = running
    
    def run(self) -> None:
        """Start the GUI application main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.GUI,
                user_message="An unexpected application error occurred",
                show_dialog=True
            )
            self.on_closing()
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """
        Show error dialog to user.
        
        Args:
            title: Dialog title
            message: Error message to display
        """
        try:
            messagebox.showerror(title, message)
        except Exception as e:
            # Fallback if messagebox fails
            # Log error silently to avoid console spam
            pass
    
    def update_status(self, message: str) -> None:
        """
        Update the status bar message.
        
        Args:
            message: Status message to display
        """
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def get_file_section_frame(self) -> ttk.Frame:
        """Get the file selection section frame for adding components."""
        return self.file_section_frame
    
    def get_progress_section_frame(self) -> ttk.Frame:
        """Get the progress section frame for adding components."""
        return self.progress_section_frame
    
    def get_results_section_frame(self) -> ttk.Frame:
        """Get the results section frame for adding components."""
        return self.results_section_frame
    
    def get_settings_frame(self) -> ttk.Frame:
        """Get the settings frame for adding components."""
        return self.settings_frame
    

    

    
    def _on_auto_logging_change(self) -> None:
        """Handle auto-logging checkbox change."""
        if self.settings_manager:
            try:
                settings = self.settings_manager.load_settings()
                settings.auto_logging = self.auto_logging_var.get()
                self.settings_manager.save_settings(settings)
                self.update_status("Auto-logging setting saved")
            except Exception as e:
                self.update_status(f"Failed to save auto-logging setting: {e}")
    
    def _on_logging_enabled_change(self) -> None:
        """Handle logging enabled checkbox change."""
        if self.logging_enabled_var.get():
            # Enable logging
            success = self.error_handler.enable_logging()
            if success:
                self.update_status("Logging enabled successfully")
                # Update settings if available
                if self.settings_manager:
                    settings = self.settings_manager.load_settings()
                    settings.auto_logging = True
                    self.settings_manager.save_settings(settings)
            else:
                self.update_status("Logging already enabled or failed to enable")
                # Uncheck the checkbox if enabling failed
                self.logging_enabled_var.set(False)
        else:
            # Disable logging
            self.error_handler.disable_logging()
            self.update_status("Logging disabled")
            # Update settings if available
            if self.settings_manager:
                settings = self.settings_manager.load_settings()
                settings.auto_logging = False
                self.settings_manager.save_settings(settings)
        
        # Update the status display
        self._update_logging_status()
    
    def _on_show_status_change(self) -> None:
        """Handle show status checkbox change."""
        if self.show_status_var.get():
            # Show log status
            status = self.error_handler.get_log_status()
            status_text = f"Logging Enabled: {status['enabled']}\n"
            status_text += f"Auto Logging: {status['auto_logging']}\n"
            status_text += f"Log File: {status['log_file_path'] or 'None'}"
            
            # Show status in a simple dialog
            from tkinter import messagebox
            messagebox.showinfo("Log Status", status_text)
            
            # Uncheck the checkbox after showing status
            self.show_status_var.set(False)
    
    def _on_open_log_file_change(self) -> None:
        """Handle open log file checkbox change."""
        if self.open_log_file_var.get():
            # Open log file
            log_path = self.error_handler.get_log_file_path()
            if log_path and log_path.exists():
                try:
                    import subprocess
                    import sys
                    import os
                    
                    if sys.platform == "win32":
                        os.startfile(str(log_path))
                    elif sys.platform == "darwin":  # macOS
                        subprocess.run(["open", str(log_path)])
                    else:  # Linux
                        subprocess.run(["xdg-open", str(log_path)])
                        
                    self.update_status(f"Opened log file: {log_path}")
                except Exception as e:
                    self.update_status(f"Failed to open log file: {e}")
            else:
                self.update_status("No log file available")
            
            # Uncheck the checkbox after opening
            self.open_log_file_var.set(False)
    
    def _on_clear_logs_change(self) -> None:
        """Handle clear logs checkbox change."""
        if self.clear_logs_var.get():
            try:
                from tkinter import messagebox
                result = messagebox.askyesno(
                    "Clear Logs",
                    "Are you sure you want to clear all log files? This action cannot be undone."
                )
                
                if result:
                    # Get log directory
                    status = self.error_handler.get_log_status()
                    if status['log_file_path']:
                        log_dir = Path(status['log_file_path']).parent
                        
                        # Clear all log files in the directory
                        cleared_count = 0
                        for log_file in log_dir.glob("*.log"):
                            try:
                                log_file.unlink()
                                cleared_count += 1
                            except Exception as e:
                                # Log deletion failure silently
                                pass
                        
                        self.update_status(f"Cleared {cleared_count} log files")
                    else:
                        self.update_status("No log directory found")
            except Exception as e:
                self.update_status(f"Failed to clear logs: {e}")
            
            # Uncheck the checkbox after clearing
            self.clear_logs_var.set(False)
    
    def _on_browse_log_dir_change(self) -> None:
        """Handle browse log directory checkbox change."""
        if self.browse_log_dir_var.get():
            try:
                import subprocess
                import sys
                import os
                
                # Get log directory
                status = self.error_handler.get_log_status()
                if status['log_file_path']:
                    log_dir = Path(status['log_file_path']).parent
                else:
                    # Use default log directory
                    main_script_path = Path(__file__).parent.parent.parent / 'main.py'
                    if main_script_path.exists():
                        log_dir = main_script_path.parent / 'logs'
                    else:
                        log_dir = Path.cwd() / 'logs'
                
                # Create directory if it doesn't exist
                log_dir.mkdir(parents=True, exist_ok=True)
                
                # Open directory in file explorer
                if sys.platform == "win32":
                    os.startfile(str(log_dir))
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(log_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(log_dir)])
                    
                self.update_status(f"Opened log directory: {log_dir}")
            except Exception as e:
                self.update_status(f"Failed to open log directory: {e}")
            
            # Uncheck the checkbox after browsing
            self.browse_log_dir_var.set(False)
    
    def _update_logging_status(self) -> None:
        """Update the logging status display."""
        status = self.error_handler.get_log_status()
        
        if status['enabled']:
            self.logging_status_var.set("Enabled")
            # Update the logging enabled checkbox to reflect current state
            if hasattr(self, 'logging_enabled_var'):
                self.logging_enabled_var.set(True)
        else:
            self.logging_status_var.set("Disabled")
            # Update the logging enabled checkbox to reflect current state
            if hasattr(self, 'logging_enabled_var'):
                self.logging_enabled_var.set(False)
        
        log_path = status['log_file_path']
        if log_path:
            # Show just the filename, not the full path
            from pathlib import Path
            self.log_file_var.set(Path(log_path).name)
        else:
            self.log_file_var.set("None")
        
        # Load current settings for the controls
        if self.settings_manager:
            try:
                settings = self.settings_manager.load_settings()
                self.auto_logging_var.set(settings.auto_logging)
            except Exception:
                pass  # Use default values if loading fails
    
    def _apply_platform_fonts(self) -> None:
        """Apply platform-appropriate fonts to the interface."""
        try:
            fonts = StyleUtils.get_platform_fonts()
            
            # Configure default font
            default_font = fonts.get('default', ('TkDefaultFont', 9))
            self.root.option_add('*Font', default_font)
            
            # Configure ttk styles with platform fonts
            style = ttk.Style()
            
            # Configure specific widget fonts
            style.configure('TLabel', font=default_font)
            style.configure('TButton', font=default_font)
            style.configure('TEntry', font=default_font)
            style.configure('TCheckbutton', font=default_font)
            style.configure('TRadiobutton', font=default_font)
            
            # Configure heading font
            heading_font = fonts.get('heading', (default_font[0], default_font[1] + 3))
            style.configure('Heading.TLabel', font=heading_font)
            
            # Configure small font
            small_font = fonts.get('small', (default_font[0], max(8, default_font[1] - 1)))
            style.configure('Small.TLabel', font=small_font)
            
        except Exception:
            # If font configuration fails, continue with defaults
            pass
    
    def center_window(self) -> None:
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        ScreenUtils.center_window(self.root, width, height)
    
    # Menu callback methods
    def _menu_open_video(self) -> None:
        """Handle File > Open Video menu item."""
        # This will be connected to the file selection panel
        if hasattr(self, '_file_selection_panel') and self._file_selection_panel:
            self._file_selection_panel.browse_video_file()
    
    def _menu_save_transcript(self) -> None:
        """Handle File > Save Transcript menu item."""
        # This will be connected to the results panel
        if hasattr(self, '_results_panel') and self._results_panel:
            if self._results_panel.has_results():
                transcript = self._results_panel.get_current_transcript()
                if transcript and hasattr(self, '_file_selection_panel'):
                    # Trigger save through the results panel
                    self._results_panel._on_save_clicked()
    
    def _menu_reset(self) -> None:
        """Handle File > Reset menu item."""
        if hasattr(self, 'on_reset_request') and self.on_reset_request:
            self.on_reset_request()
    
    def _menu_copy_results(self) -> None:
        """Handle Edit > Copy Results menu item."""
        if hasattr(self, '_results_panel') and self._results_panel:
            self._results_panel._on_copy_clicked()
    
    def _menu_select_all(self) -> None:
        """Handle Edit > Select All menu item."""
        # Focus the results panel and select all text
        if hasattr(self, '_results_panel') and self._results_panel:
            self._results_panel._select_all()
    

    
    def _menu_start_transcription(self) -> None:
        """Handle Transcription > Start menu item."""
        # Check if start button is enabled (same logic should apply to menu)
        if (hasattr(self, 'start_button') and 
            self.start_button.cget('state') == 'normal' and 
            self.on_start_transcription):
            self.on_start_transcription()
    
    def _menu_cancel_transcription(self) -> None:
        """Handle Transcription > Cancel menu item."""
        # This will be connected to the progress panel
        if hasattr(self, '_progress_panel') and self._progress_panel:
            if hasattr(self._progress_panel, 'on_cancel_request') and self._progress_panel.on_cancel_request:
                self._progress_panel.on_cancel_request()
    
    def _menu_show_help(self) -> None:
        """Handle Help > How to Use menu item."""
        show_help_dialog(self.root)
    
    def _menu_show_about(self) -> None:
        """Handle Help > About menu item."""
        show_about_dialog(self.root)
    

    
    # Panel reference methods for connecting with app
    def set_file_selection_panel(self, panel) -> None:
        """Set reference to file selection panel for menu/shortcut integration."""
        self._file_selection_panel = panel
    
    def set_configuration_panel(self, panel) -> None:
        """Set reference to configuration panel for menu/shortcut integration."""
        self._configuration_panel = panel
    
    def set_progress_panel(self, panel) -> None:
        """Set reference to progress panel for menu/shortcut integration."""
        self._progress_panel = panel
    
    def set_results_panel(self, panel) -> None:
        """Set reference to results panel for menu/shortcut integration."""
        self._results_panel = panel
    
