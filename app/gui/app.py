"""
Video-to-Text Main Application: GUI Application Controller.

This module provides the main VideoToTextApp class that serves as the central
controller for the entire Video-to-Text application. It coordinates between
GUI components, services, and utilities to provide a complete transcription
solution. The application follows a clean architecture pattern with proper
dependency injection and component lifecycle management.

Features:
- Application Lifecycle: Complete startup, running, and shutdown management.
- Component Coordination: Wires together GUI, services, and utilities.
- Dependency Injection: Proper service instantiation and injection.
- Error Handling: Centralized error management with user feedback.
- Settings Management: Persistent configuration across sessions.
- Threading Support: Background transcription with UI responsiveness.
- Resource Management: Proper cleanup of temporary files and resources.
- Cross-Platform: Native behavior on Windows, macOS, and Linux.

Architecture:
- Clean separation between GUI, business logic, and utilities
- Interface-based design for testability and maintainability
- Event-driven communication between components
- Centralized state management and coordination

Usage:
Create and run the main application:
    app = VideoToTextApp()
    app.initialize()
    app.run()

Dependencies:
- Python 3.8+: Core programming language
- tkinter: GUI framework
- threading: Background processing support
- All application modules (gui, core, services, utils)

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

import sys
import os
import time
import signal
import atexit
import threading
from typing import Optional
from datetime import datetime

from .main_window import MainWindow
from .file_selection_panel import FileSelectionPanel
from .configuration_panel import ConfigurationPanel
from .progress_panel import ProgressPanel
from .results_panel import ResultsPanel
from ..services.transcription_controller import TranscriptionController
from ..services.transcription_service import TranscriptionService
from ..utils.settings_manager import SettingsManager
from ..utils.file_manager import FileManager
from ..core.models import TranscriptionRequest, TranscriptionResult, ProgressUpdate
from ..utils.error_handler import initialize_error_handler


class VideoToTextApp:
    """
    Main application class that coordinates the GUI application startup
    and wires together all components with proper dependency injection.
    """
    
    def __init__(self, headless=False, input_file=None, output_file=None, output_format="txt", verbose=False):
        """Initialize the application."""
        self.headless = headless
        self.input_file = input_file
        self.output_file = output_file
        self.output_format = output_format
        self.verbose = verbose

        # Core services
        self.settings_manager: Optional[SettingsManager] = None
        self.file_manager: Optional[FileManager] = None
        self.transcription_service: Optional[TranscriptionService] = None
        self.transcription_controller: Optional[TranscriptionController] = None
        
        # GUI components
        self.main_window: Optional[MainWindow] = None
        self.file_selection_panel: Optional[FileSelectionPanel] = None
        self.configuration_panel: Optional[ConfigurationPanel] = None
        self.progress_panel: Optional[ProgressPanel] = None
        self.results_panel: Optional[ResultsPanel] = None
        
        # Application state
        self._is_initialized = False
        self._is_shutting_down = False
        self._shutdown_lock = threading.Lock()
        self._startup_time = datetime.now()
        

        
        # Register cleanup handlers
        self._register_cleanup_handlers()
        
    def initialize(self) -> None:
        """Initialize application components with proper dependency injection."""
        try:
            # Initialize settings manager (only if not already set)
            if not self.settings_manager:
                self.settings_manager = SettingsManager()

            settings = self.settings_manager.load_settings()

            # Initialize error handler immediately
            initialize_error_handler(settings=settings, show_dialogs=not self.headless)

            # Initialize core services
            self._initialize_services()
            
            if not self.headless:
                # Create main window
                self.main_window = MainWindow(self.settings_manager)

                # Initialize GUI panels
                self._initialize_gui_panels()

                # Wire up component communication
                self._setup_component_communication()

                # Set up event handlers
                self._setup_event_handlers()
            
            self._is_initialized = True
            
            if not self.headless:
                # Perform initial validation to set correct button state
                self._update_transcription_availability()
            
        except Exception as e:
            if not self.headless:
                # Error initializing application - create minimal window
                # Note: error handler might already be initialized so we can log this
                print(f"Error initializing: {e}")
                self.main_window = MainWindow()
            else:
                print(f"Error initializing in headless mode: {e}")
                sys.exit(1)
            
    def _register_cleanup_handlers(self) -> None:
        """Register cleanup handlers for graceful shutdown."""
        # Register atexit handler for normal program termination
        atexit.register(self._emergency_cleanup)
        
        # Register signal handlers for interruption
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Windows-specific signal handling
        if sys.platform == "win32":
            if hasattr(signal, 'SIGBREAK'):
                signal.signal(signal.SIGBREAK, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        self.shutdown()
    
    def _emergency_cleanup(self) -> None:
        """Emergency cleanup called by atexit handler."""
        if not self._is_shutting_down:
            self._cleanup_before_exit()
    
    def startup(self) -> bool:
        """
        Perform application startup sequence.
        
        Returns:
            True if startup was successful, False otherwise
        """
        try:
            # Initialize the application
            if not self._is_initialized:
                self.initialize()
            
            if not self._is_initialized:
                return False
            
            # Load and apply saved settings
            self._load_startup_settings()
            
            # Perform startup validation
            if not self._validate_startup_state():
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def _load_startup_settings(self) -> None:
        """Load and apply settings during startup."""
        if not self.settings_manager:
            return
        
        try:
            # Settings are already loaded in MainWindow initialization
            # But we can perform additional startup-specific settings here
            settings = self.settings_manager.load_settings()
            
            # Apply settings to panels
            if self.configuration_panel:
                self.configuration_panel.apply_settings(settings)
            
            if self.file_selection_panel:
                self.file_selection_panel.apply_settings(settings)
            
            # Startup settings loaded successfully
            
        except Exception as e:
            # Could not load startup settings
            pass
    
    def _validate_startup_state(self) -> bool:
        """
        Validate that the application is in a valid state after startup.
        
        Returns:
            True if startup state is valid, False otherwise
        """
        if not self.settings_manager:
            return False
        
        if not self.file_manager:
            return False

        if not self.headless:
            # Check that essential components are initialized
            if not self.main_window:
                return False

            # Check that GUI panels are properly initialized
            required_panels = [
                self.file_selection_panel,
                self.configuration_panel,
                self.progress_panel,
                self.results_panel
            ]

            for panel in required_panels:
                if panel is None:
                    return False
        
        return True
    
    def shutdown(self) -> None:
        """
        Perform graceful application shutdown.
        """
        with self._shutdown_lock:
            if self._is_shutting_down:
                return
            
            self._is_shutting_down = True
        
        try:
            # Cancel any running operations
            self._cancel_running_operations()
            
            # Save current state
            if not self.headless:
                self._save_shutdown_settings()
            
            # Cleanup resources
            self._cleanup_before_exit()
            
            # Close the main window
            if self.main_window and self.main_window.root:
                try:
                    self.main_window.root.quit()
                    self.main_window.root.destroy()
                except:
                    pass
            
        except Exception as e:
            # Error during shutdown
            pass
        finally:
            # Ensure we exit
            sys.exit(0)
    
    def _cancel_running_operations(self) -> None:
        """Cancel any running transcription operations."""
        try:
            if self.transcription_controller and self.transcription_controller.is_transcription_running():
                self.transcription_controller.cancel_transcription()
                
                # Wait briefly for cancellation to complete
                timeout = 3.0  # 3 second timeout
                start_time = time.time()
                while (self.transcription_controller.is_transcription_running() and 
                       time.time() - start_time < timeout):
                    time.sleep(0.1)
                    
        except Exception as e:
            # Error cancelling operations
            pass
    
    def _save_shutdown_settings(self) -> None:
        """Save application settings during shutdown."""
        try:
            if not self.settings_manager:
                return
            
            # Get current settings from components
            current_settings = self.settings_manager.load_settings()
            
            # Update settings with current state
            if self.configuration_panel:
                current_settings.default_output_format = self.configuration_panel.get_output_format()
                current_settings.verbose_mode = self.configuration_panel.is_verbose_enabled()
            
            if self.file_selection_panel:
                video_dir = self.file_selection_panel.get_last_video_directory()
                output_dir = self.file_selection_panel.get_last_output_directory()
                if video_dir:
                    current_settings.last_video_directory = video_dir
                if output_dir:
                    current_settings.last_output_directory = output_dir
            
            # Window geometry is already updated in MainWindow
            if self.main_window and self.main_window.root:
                try:
                    current_settings.window_geometry = self.main_window.root.geometry()
                except:
                    pass
            
            # Save the updated settings
            self.settings_manager.save_settings(current_settings)
            
        except Exception as e:
            # Could not save shutdown settings
            pass
    
    def get_uptime(self) -> float:
        """
        Get application uptime in seconds.
        
        Returns:
            Uptime in seconds since startup
        """
        return (datetime.now() - self._startup_time).total_seconds()
    
    def is_shutting_down(self) -> bool:
        """
        Check if the application is currently shutting down.
        
        Returns:
            True if shutdown is in progress, False otherwise
        """
        return self._is_shutting_down
    
    def _initialize_services(self) -> None:
        """Initialize core service components."""
        # Note: settings_manager and error_handler are already initialized in initialize()
        
        settings = self.settings_manager.load_settings()

        # Initialize file manager
        self.file_manager = FileManager()
        
        # Initialize transcription service
        self.transcription_service = TranscriptionService(settings=settings)
        
        # Initialize transcription controller with callbacks
        # For headless, we'll set callbacks later or differently
        self.transcription_controller = TranscriptionController(
            transcription_service=self.transcription_service,
            file_manager=self.file_manager,
            settings=settings,
            progress_callback=self._on_transcription_progress if not self.headless else None,
            completion_callback=self._on_transcription_complete if not self.headless else None
        )
    
    def _initialize_gui_panels(self) -> None:
        """Initialize GUI panel components."""
        if not self.main_window:
            raise RuntimeError("Main window must be initialized before panels")
        
        # Initialize file selection panel
        self.file_selection_panel = FileSelectionPanel(
            parent_frame=self.main_window.get_file_section_frame(),
            file_manager=self.file_manager,
            settings_manager=self.settings_manager,
            on_selection_change=self._on_file_selection_change
        )
        
        # Initialize configuration panel
        self.configuration_panel = ConfigurationPanel(
            parent_frame=self.main_window.get_settings_frame(),
            settings_manager=self.settings_manager,
            on_settings_change=self._on_configuration_change
        )
        
        # Initialize progress panel
        self.progress_panel = ProgressPanel(
            parent_frame=self.main_window.get_progress_section_frame(),
            on_cancel_request=self._on_cancel_request
        )
        
        # Initialize results panel
        self.results_panel = ResultsPanel(
            parent_frame=self.main_window.get_results_section_frame(),
            on_save_request=self._on_save_request
        )
        
        # Connect panels to main window for menu/shortcut integration
        self.main_window.set_file_selection_panel(self.file_selection_panel)
        self.main_window.set_configuration_panel(self.configuration_panel)
        self.main_window.set_progress_panel(self.progress_panel)
        self.main_window.set_results_panel(self.results_panel)
    
    def _setup_component_communication(self) -> None:
        """Set up communication between components."""
        # Connect configuration panel to file selection panel for format updates
        if self.configuration_panel and self.file_selection_panel:
            # Set up a callback for when output format changes
            def on_format_change():
                format_type = self.configuration_panel.get_output_format()
                if hasattr(self.file_selection_panel, 'update_output_format'):
                    self.file_selection_panel.update_output_format(format_type)
            
            # Store the callback for the configuration panel to use
            self.configuration_panel._format_change_callback = on_format_change
        
        # Connect progress panel verbose mode to configuration panel
        if self.progress_panel and self.configuration_panel:
            # Sync initial verbose mode state
            verbose_enabled = self.configuration_panel.is_verbose_enabled()
            if hasattr(self.progress_panel, 'set_verbose_mode'):
                self.progress_panel.set_verbose_mode(verbose_enabled)
    
    def _setup_event_handlers(self) -> None:
        """Set up application-level event handlers."""
        if self.main_window:
            # Override the main window's closing handler to use proper shutdown
            def enhanced_on_closing():
                if not self._is_shutting_down:
                    self.shutdown()
            
            self.main_window.on_closing = enhanced_on_closing
            
            # Set up start transcription callback
            self.main_window.set_start_transcription_callback(self.start_transcription)
            
            # Set up reset callback
            self.main_window.set_reset_callback(self.reset_application)
    
    def _on_file_selection_change(self) -> None:
        """Handle file selection changes."""
        if not self._is_initialized:
            return
        
        # Update main window status
        if self.file_selection_panel and self.main_window:
            if self.file_selection_panel.is_video_file_selected():
                video_path = self.file_selection_panel.get_video_file_path()
                filename = os.path.basename(video_path)
                self.main_window.update_status(f"Video selected: {filename}")
            else:
                self.main_window.update_status("Ready - Select a video file")
        
        # Enable/disable transcription based on file selection
        self._update_transcription_availability()
    
    def _on_configuration_change(self) -> None:
        """Handle configuration changes."""
        if not self._is_initialized:
            return
        
        # Update progress panel verbose mode
        if self.configuration_panel and self.progress_panel:
            verbose_enabled = self.configuration_panel.is_verbose_enabled()
            if hasattr(self.progress_panel, 'set_verbose_mode'):
                self.progress_panel.set_verbose_mode(verbose_enabled)
        
        # Call format change callback if it exists
        if self.configuration_panel and hasattr(self.configuration_panel, '_format_change_callback'):
            try:
                self.configuration_panel._format_change_callback()
            except Exception:
                pass  # Ignore callback errors
    
    def _on_cancel_request(self) -> None:
        """Handle transcription cancellation request."""
        if self.transcription_controller:
            self.transcription_controller.cancel_transcription()
        
        if self.main_window:
            self.main_window.update_status("Cancelling transcription...")
    
    def _on_save_request(self, transcript_text: str) -> None:
        """Handle save transcript request."""
        if not self.file_selection_panel or not self.configuration_panel:
            return
        
        # Use current output path and format from panels
        output_path = self.file_selection_panel.get_output_file_path()
        output_format = self.configuration_panel.get_output_format()
        
        if output_path and self.file_manager:
            success = self.file_manager.save_transcript(
                transcript_text, 
                output_path, 
                output_format
            )
            
            if success and self.main_window:
                self.main_window.update_status(f"Transcript saved to: {os.path.basename(output_path)}")
            elif self.main_window:
                self.main_window.update_status("Failed to save transcript")
    
    def _on_transcription_progress(self, update: ProgressUpdate) -> None:
        """Handle transcription progress updates."""
        if self.progress_panel:
            self.progress_panel.handle_progress_update(update)
        
        if self.main_window:
            self.main_window.update_status(f"{update.current_step}: {update.percentage:.1f}%")
            # Update transcription running state for close confirmation
            is_running = self.transcription_controller and self.transcription_controller.is_transcription_running()
            self.main_window.set_transcription_running(is_running)
            # Update button state during transcription
            self._update_transcription_availability()
    
    def _on_transcription_complete(self, result: TranscriptionResult) -> None:
        """Handle transcription completion."""
        def _update_ui():
            if self.progress_panel:
                self.progress_panel.complete_operation(
                    success=result.success,
                    message="Transcription completed" if result.success else result.error_message
                )
                # Reset progress panel after a brief delay to show completion
                if result.success:
                    self.main_window.root.after(3000, self.progress_panel.reset)
            
            if self.results_panel:
                self.results_panel.display_result(result)
            
            if self.main_window:
                if result.success:
                    self.main_window.update_status("Transcription completed successfully")
                else:
                    self.main_window.update_status(f"Transcription failed: {result.error_message}")
                
                # Update transcription running state
                self.main_window.set_transcription_running(False)
                
                # Force button text and state update after completion
                self.main_window.set_start_button_text("Start Transcription")
                self.main_window.enable_start_button(True)
                self.main_window.enable_cancel_menu(False)
            
            # Re-enable transcription controls with a small delay to ensure state is reset
            self.main_window.root.after(100, self._update_transcription_availability)
        
        # Schedule UI update on main thread
        if self.main_window and self.main_window.root:
            self.main_window.root.after(0, _update_ui)
        else:
            _update_ui()
    
    def force_ui_reset(self) -> None:
        """Force reset the UI state after transcription completion."""
        if self.main_window:
            self.main_window.set_start_button_text("Start Transcription")
            self.main_window.enable_start_button(True)
            self.main_window.enable_cancel_menu(False)
            self.main_window.set_transcription_running(False)
        self._update_transcription_availability()
    
    def _update_transcription_availability(self) -> None:
        """Update the availability of transcription controls based on current state."""
        if not self._is_initialized or not self.main_window:
            return
        
        def _do_update():
            
            if not self._is_initialized or not self.main_window:
                return
            
            # Check if transcription is running
            is_running = (self.transcription_controller and 
                         self.transcription_controller.is_transcription_running())
            
            # Check if transcription can be started
            can_start = (
                self.file_selection_panel and 
                self.file_selection_panel.validate() and
                self.configuration_panel and
                self.configuration_panel.validate() and
                self.transcription_controller and
                not is_running
            )
            
            # Update start button state
            self.main_window.enable_start_button(can_start)
            
            # Update menu states
            self.main_window.enable_cancel_menu(is_running)
            
            # Update button text based on state
            if is_running:
                self.main_window.set_start_button_text("Transcribing...")
            else:
                self.main_window.set_start_button_text("Start Transcription")
        
        self.main_window.root.after(10, _do_update)
    
    def start_transcription(self) -> bool:
        """
        Start transcription with current settings.
        
        Returns:
            True if transcription was started successfully, False otherwise
        """
        if not self._is_initialized:
            return False
        
        # Validate all components are ready
        if not (self.file_selection_panel and self.configuration_panel and 
                self.transcription_controller and self.progress_panel):
            return False
        
        # Validate inputs
        if not (self.file_selection_panel.validate() and 
                self.configuration_panel.validate()):
            return False
        
        # Check if already running
        if self.transcription_controller.is_transcription_running():
            return False
        
        try:
            # Create transcription request
            request = TranscriptionRequest(
                video_path=self.file_selection_panel.get_video_file_path(),
                output_path=self.file_selection_panel.get_output_file_path(),
                output_format=self.configuration_panel.get_output_format(),
                verbose=self.configuration_panel.is_verbose_enabled(),
                timestamp=datetime.now()
            )
            
            # Start progress tracking
            self.progress_panel.start_operation("Transcription")
            
            # Update menu states for transcription start
            if self.main_window:
                self.main_window.enable_cancel_menu(True)
            
            # Start transcription
            self.transcription_controller.start_transcription(request)
            
            if self.main_window:
                self.main_window.update_status("Starting transcription...")
            
            return True
            
        except Exception as e:
            if self.main_window:
                self.main_window.update_status(f"Failed to start transcription: {str(e)}")
            
            if self.progress_panel:
                self.progress_panel.show_error(str(e))
            
            return False
    
    def _cleanup_before_exit(self) -> None:
        """Perform cleanup before application exit."""
        try:
            # Cancel any running transcription
            if self.transcription_controller and self.transcription_controller.is_transcription_running():
                self.transcription_controller.cancel_transcription()
            
            # Clean up temporary files
            if self.file_manager:
                self.file_manager.cleanup_temp_files()
            
        except Exception as e:
            # Error during cleanup
            pass
    
    def run(self) -> None:
        """Run the application."""
        try:
            # Perform startup sequence
            if not self.startup():
                sys.exit(1)
            
            if not self.headless and self.main_window:
                # Center the window on first run
                self.main_window.center_window()
                
                # Start the GUI main loop
                self.main_window.run()
            elif self.headless:
                self._run_headless()

        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.shutdown()
            sys.exit(1)

    def _run_headless(self) -> None:
        """Run the application in headless mode."""
        if not self.input_file:
            print("Error: Input file is required in headless mode.")
            sys.exit(1)

        if not os.path.exists(self.input_file):
            print(f"Error: Input file not found: {self.input_file}")
            sys.exit(1)

        # Determine output file if not provided
        output_path = self.output_file
        if not output_path:
            base_name = os.path.splitext(self.input_file)[0]
            output_path = f"{base_name}_transcript.{self.output_format}"

        print(f"Starting transcription for: {self.input_file}")
        print(f"Output will be saved to: {output_path}")
        print("Format:", self.output_format)

        # Create request
        request = TranscriptionRequest(
            video_path=self.input_file,
            output_path=output_path,
            output_format=self.output_format,
            verbose=self.verbose,
            timestamp=datetime.now()
        )

        # Setup callbacks for console output
        completion_event = threading.Event()
        result_holder = {}

        def progress_callback(update: ProgressUpdate):
            print(f"[{update.percentage:.1f}%] {update.current_step}: {update.message}")

        def completion_callback(result: TranscriptionResult):
            result_holder['result'] = result
            completion_event.set()

        # Wire up callbacks
        self.transcription_controller.set_progress_callback(progress_callback)
        self.transcription_controller.set_completion_callback(completion_callback)

        # Start transcription
        try:
            self.transcription_controller.start_transcription(request)

            # Wait for completion
            while not completion_event.wait(timeout=1.0):
                # Check for keyboard interrupt logic here if needed,
                # but main thread is blocked here so KeyboardInterrupt handles it.
                pass

            result = result_holder.get('result')
            if result and result.success:
                print("\nTranscription completed successfully!")
                print(f"Transcript saved to: {result.output_file_path}")
                sys.exit(0)
            else:
                error = result.error_message if result else "Unknown error"
                print(f"\nTranscription failed: {error}")
                sys.exit(1)

        except Exception as e:
            print(f"Error starting transcription: {e}")
            sys.exit(1)
    
    def get_transcription_controller(self) -> Optional[TranscriptionController]:
        """Get the transcription controller for external access."""
        return self.transcription_controller
    
    def is_initialized(self) -> bool:
        """Check if the application is fully initialized."""
        return self._is_initialized
    
    def reset_application(self) -> None:
        """Reset the application to its initial state."""
        if not self._is_initialized:
            return
        
        try:
            # Cancel any running transcription first
            if self.transcription_controller and self.transcription_controller.is_transcription_running():
                self.transcription_controller.cancel_transcription()
                # Wait a moment for cancellation to complete
                time.sleep(0.5)
            
            # Reset all panels
            if self.file_selection_panel:
                self.file_selection_panel.reset()
            
            if self.configuration_panel:
                self.configuration_panel.reset()
            
            if self.progress_panel:
                self.progress_panel.reset()
            
            if self.results_panel:
                self.results_panel.reset()
            
            # Clean up temporary files
            if self.file_manager:
                self.file_manager.cleanup_temp_files()
            
            # Update UI state
            self._update_transcription_availability()
            
            if self.main_window:
                self.main_window.update_status("Application reset - Ready for new transcription")
            
        except Exception as e:
            if self.main_window:
                self.main_window.update_status(f"Error during reset: {str(e)}")


def main():
    """Main entry point for the application."""
    app = None
    try:
        app = VideoToTextApp()
        app.run()
    except KeyboardInterrupt:
        if app:
            app.shutdown()
        sys.exit(0)
    except Exception as e:
        if app:
            app.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()