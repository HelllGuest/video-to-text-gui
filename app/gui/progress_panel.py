"""
Progress panel for the Video-to-Text application.

This module contains the ProgressPanel class which provides
progress tracking, status display, and verbose logging functionality.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import time
from datetime import datetime
from typing import Optional, Callable
from threading import Lock

from ..core.interfaces import IGUIPanel
from ..core.models import ProgressUpdate
from ..utils.platform_utils import StyleUtils, PLATFORM


class ProgressPanel(IGUIPanel):
    """
    GUI panel for displaying transcription progress and status.
    
    This class provides a progress bar, status messages, verbose logging
    with scrolling, and thread-safe progress update methods.
    """
    
    def __init__(self, parent_frame: ttk.Frame, 
                 on_cancel_request: Optional[Callable[[], None]] = None):
        """
        Initialize the progress panel.
        
        Args:
            parent_frame: Parent tkinter frame to contain this panel
            on_cancel_request: Optional callback when user requests cancellation
        """
        self.parent_frame = parent_frame
        self.on_cancel_request = on_cancel_request
        
        # Initialize variables
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        self.is_running_var = tk.BooleanVar()
        self.verbose_enabled_var = tk.BooleanVar()
        
        self._update_lock = Lock()
        self._pending_updates = []
        self._update_batch_size = 10
        self._last_update_time = 0
        self._update_throttle_ms = 50
        
        self._is_processing = False
        self._current_operation = ""
        
        self._update_count = 0
        self._dropped_updates = 0
        
        # Initialize the panel
        self.initialize()
        
    def initialize(self) -> None:
        """Initialize the panel and its components."""
        self._create_widgets()
        self._setup_bindings()
        self.reset()
    
    def _create_widgets(self) -> None:
        """Create and arrange the GUI widgets."""
        # Configure parent frame grid
        self.parent_frame.grid_columnconfigure(0, weight=1)
        self.parent_frame.grid_rowconfigure(2, weight=1)  # Verbose log area
        
        # Progress bar section
        progress_frame = ttk.Frame(self.parent_frame)
        progress_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Progress percentage label
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1)
        
        # Status section
        status_frame = ttk.Frame(self.parent_frame)
        status_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        status_label = ttk.Label(status_frame, text="Status:")
        status_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.status_display = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("TkDefaultFont", 9, "bold")
        )
        self.status_display.grid(row=0, column=1, sticky="w")
        
        # Cancel button (initially hidden)
        self.cancel_button = ttk.Button(
            status_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            state="disabled"
        )
        self.cancel_button.grid(row=0, column=2, padx=(10, 0))
        
        # Verbose logging section
        verbose_frame = ttk.LabelFrame(self.parent_frame, text="Detailed Log", padding="5")
        verbose_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 5))
        verbose_frame.grid_columnconfigure(0, weight=1)
        verbose_frame.grid_rowconfigure(0, weight=1)
        
        fonts = StyleUtils.get_platform_fonts()
        monospace_font = fonts.get('monospace', ('Consolas', 9))
        
        self.verbose_text = scrolledtext.ScrolledText(
            verbose_frame,
            height=8,
            width=60,
            wrap=tk.WORD,
            state="disabled",
            font=monospace_font
        )
        self.verbose_text.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
        # Verbose controls
        verbose_controls_frame = ttk.Frame(verbose_frame)
        verbose_controls_frame.grid(row=1, column=0, sticky="ew")
        verbose_controls_frame.grid_columnconfigure(1, weight=1)
        
        # Verbose mode checkbox
        self.verbose_checkbox = ttk.Checkbutton(
            verbose_controls_frame,
            text="Show detailed logging",
            variable=self.verbose_enabled_var,
            command=self._on_verbose_toggle
        )
        self.verbose_checkbox.grid(row=0, column=0, sticky="w")
        
        # Clear log button
        self.clear_log_button = ttk.Button(
            verbose_controls_frame,
            text="Clear Log",
            command=self.clear_verbose_log
        )
        self.clear_log_button.grid(row=0, column=2, padx=(5, 0))
        
        # Configure text tags for different message types
        self._setup_text_tags()
    
    def _setup_text_tags(self) -> None:
        """Set up text tags for different types of log messages."""
        colors = StyleUtils.get_platform_colors()
        fonts = StyleUtils.get_platform_fonts()
        monospace_font = fonts.get('monospace', ('Consolas', 9))
        small_monospace = (monospace_font[0], max(8, monospace_font[1] - 1))
        self.verbose_text.tag_configure("info", foreground="black")
        self.verbose_text.tag_configure("success", foreground=colors.get('success', 'green'))
        self.verbose_text.tag_configure("warning", foreground=colors.get('warning', 'orange'))
        self.verbose_text.tag_configure("error", foreground=colors.get('error', 'red'))
        self.verbose_text.tag_configure("timestamp", foreground="gray", font=small_monospace)
    
    def _setup_bindings(self) -> None:
        """Set up event bindings for the widgets."""
        # Bind verbose mode changes
        self.verbose_enabled_var.trace_add("write", self._on_verbose_mode_change)
        
        # Set up periodic update checking for thread safety
        self._schedule_update_check()
    
    def _schedule_update_check(self) -> None:
        """Schedule periodic checking for pending updates with adaptive timing."""
        try:
            self._process_pending_updates()
            
            # Adaptive scheduling based on update frequency
            update_interval = 50 if self._is_processing else 200
            self.parent_frame.after(update_interval, self._schedule_update_check)
        except tk.TclError:
            # Widget has been destroyed, stop scheduling
            pass
    
    def _process_pending_updates(self) -> None:
        """Process pending updates from background threads with batching and throttling."""
        current_time = time.time() * 1000  # Convert to milliseconds
        
        with self._update_lock:
            if not self._pending_updates:
                return
            
            if current_time - self._last_update_time < self._update_throttle_ms:
                return
            
            batch_size = min(self._update_batch_size, len(self._pending_updates))
            updates_to_process = self._pending_updates[:batch_size]
            self._pending_updates = self._pending_updates[batch_size:]
            
            if len(self._pending_updates) > 50:
                dropped = len(self._pending_updates) - 25
                self._pending_updates = self._pending_updates[-25:]
                self._dropped_updates += dropped
        
        # Process the batch outside the lock
        for update_func in updates_to_process:
            try:
                update_func()
                self._update_count += 1
            except Exception as e:
                try:
                    self._add_log_message_internal(
                        f"Error processing update: {str(e)}", 
                        "error"
                    )
                except:
                    pass
        
        self._last_update_time = current_time
    
    def _on_verbose_toggle(self) -> None:
        """Handle verbose mode checkbox toggle."""
        self._update_verbose_visibility()
    
    def _on_verbose_mode_change(self, *args) -> None:
        """Handle verbose mode variable changes."""
        self._update_verbose_visibility()
    
    def _update_verbose_visibility(self) -> None:
        """Update the visibility of verbose logging components."""
        if self.verbose_enabled_var.get():
            # Show verbose log area
            self.verbose_text.grid()
        else:
            # Hide verbose log area (but keep the frame)
            pass  # Keep visible for now, just disable updates
    
    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        if self.on_cancel_request:
            self.on_cancel_request()
        
        # Update UI to show cancellation in progress
        self.show_status("Cancelling...", "warning")
        self.cancel_button.configure(state="disabled", text="Cancelling...")
    
    def update_progress(self, percentage: float, message: str = "") -> None:
        """
        Update the progress bar and status message (thread-safe with throttling).
        
        Args:
            percentage: Progress percentage (0.0 to 100.0)
            message: Optional status message
        """
        # Throttle progress updates to prevent GUI overload
        current_time = time.time() * 1000
        if hasattr(self, '_last_progress_update'):
            if current_time - self._last_progress_update < 100:  # 100ms throttle
                # Skip non-critical updates
                if percentage not in [0.0, 100.0] and percentage % 10 != 0:
                    return
        
        def _update():
            # Clamp percentage to valid range
            percentage_clamped = max(0.0, min(100.0, percentage))
            
            # Update progress bar and label
            self.progress_var.set(percentage_clamped)
            self.progress_label.configure(text=f"{percentage_clamped:.1f}%")
            
            # Update status if message provided
            if message:
                self.status_var.set(message)
                self._current_operation = message
            
            # Update progress bar color based on state
            if percentage_clamped >= 100.0:
                self.progress_bar.configure(style="success.Horizontal.TProgressbar")
            else:
                self.progress_bar.configure(style="TProgressbar")
        
        # Schedule update on main thread with priority for important updates
        with self._update_lock:
            # Give priority to milestone updates
            if percentage in [0.0, 100.0] or percentage % 25 == 0:
                self._pending_updates.insert(0, _update)  # High priority
            else:
                self._pending_updates.append(_update)  # Normal priority
        
        self._last_progress_update = current_time
    
    def show_status(self, message: str, message_type: str = "info") -> None:
        """
        Display a status message (thread-safe).
        
        Args:
            message: Status message to display
            message_type: Type of message ('info', 'success', 'warning', 'error')
        """
        def _update():
            self.status_var.set(message)
            
            # Update status label color based on message type
            if message_type == "success":
                self.status_display.configure(foreground="green")
            elif message_type == "warning":
                self.status_display.configure(foreground="orange")
            elif message_type == "error":
                self.status_display.configure(foreground="red")
            else:
                self.status_display.configure(foreground="black")
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def add_log_message(self, message: str, message_type: str = "info") -> None:
        """
        Add a message to the verbose log (thread-safe).
        
        Args:
            message: Log message to add
            message_type: Type of message ('info', 'success', 'warning', 'error')
        """
        def _update():
            self._add_log_message_internal(message, message_type)
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def _add_log_message_internal(self, message: str, message_type: str = "info") -> None:
        """
        Internal method to add a message to the verbose log.
        
        Args:
            message: Log message to add
            message_type: Type of message ('info', 'success', 'warning', 'error')
        """
        if not self.verbose_enabled_var.get():
            return
        
        # Enable text widget for editing
        self.verbose_text.configure(state="normal")
        
        try:
            # Add timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.verbose_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
            # Add message with appropriate tag
            self.verbose_text.insert(tk.END, f"{message}\n", message_type)
            
            # Auto-scroll to bottom
            self.verbose_text.see(tk.END)
            
            # Limit log size to prevent memory issues
            self._limit_log_size()
            
        finally:
            # Disable text widget to prevent user editing
            self.verbose_text.configure(state="disabled")
    
    def _limit_log_size(self) -> None:
        """Limit the size of the verbose log to prevent memory issues."""
        # Get current line count
        line_count = int(self.verbose_text.index(tk.END).split('.')[0]) - 1
        
        # If too many lines, remove oldest ones
        max_lines = 1000
        if line_count > max_lines:
            lines_to_remove = line_count - max_lines + 100  # Remove extra for efficiency
            self.verbose_text.delete("1.0", f"{lines_to_remove}.0")
    
    def clear_verbose_log(self) -> None:
        """Clear the verbose log text area."""
        self.verbose_text.configure(state="normal")
        self.verbose_text.delete("1.0", tk.END)
        self.verbose_text.configure(state="disabled")
    
    def handle_progress_update(self, update: ProgressUpdate) -> None:
        """
        Handle a ProgressUpdate object (thread-safe).
        
        Args:
            update: ProgressUpdate containing progress information
        """
        # Update progress bar
        self.update_progress(update.percentage, update.current_step)
        
        # Add detailed message to verbose log
        if update.message and update.message != update.current_step:
            self.add_log_message(f"{update.current_step}: {update.message}")
        elif update.message:
            self.add_log_message(update.message)
    
    def start_operation(self, operation_name: str = "Processing") -> None:
        """
        Start a new operation and update UI accordingly.
        
        Args:
            operation_name: Name of the operation being started
        """
        def _update():
            self._is_processing = True
            self._current_operation = operation_name
            
            # Reset progress
            self.progress_var.set(0.0)
            self.progress_label.configure(text="0%")
            
            # Update status
            self.status_var.set(f"Starting {operation_name}...")
            self.status_display.configure(foreground="blue")
            
            # Enable cancel button
            self.cancel_button.configure(state="normal", text="Cancel")
            self.is_running_var.set(True)
            
            # Add log message
            if self.verbose_enabled_var.get():
                self._add_log_message_internal(f"Started {operation_name}", "info")
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def complete_operation(self, success: bool = True, message: str = "") -> None:
        """
        Complete the current operation and update UI accordingly.
        
        Args:
            success: Whether the operation completed successfully
            message: Optional completion message
        """
        def _update():
            self._is_processing = False
            
            if success:
                # Success state
                self.progress_var.set(100.0)
                self.progress_label.configure(text="100%")
                final_message = message or f"{self._current_operation} completed successfully"
                self.status_var.set(final_message)
                self.status_display.configure(foreground="green")
                
                if self.verbose_enabled_var.get():
                    self._add_log_message_internal(final_message, "success")
            else:
                # Error state
                final_message = message or f"{self._current_operation} failed"
                self.status_var.set(final_message)
                self.status_display.configure(foreground="red")
                
                if self.verbose_enabled_var.get():
                    self._add_log_message_internal(final_message, "error")
            
            # Disable cancel button
            self.cancel_button.configure(state="disabled", text="Cancel")
            self.is_running_var.set(False)
            
            self._current_operation = ""
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def show_error(self, error_message: str) -> None:
        """
        Display an error message.
        
        Args:
            error_message: Error message to display
        """
        self.show_status(f"Error: {error_message}", "error")
        self.add_log_message(f"ERROR: {error_message}", "error")
        
        # Complete operation with error
        self.complete_operation(success=False, message=error_message)
    
    def reset(self) -> None:
        """Reset the panel to its initial state."""
        def _update():
            # Reset progress
            self.progress_var.set(0.0)
            self.progress_label.configure(text="0%")
            
            # Reset status
            self.status_var.set("Ready")
            self.status_display.configure(foreground="black")
            
            # Reset state
            self._is_processing = False
            self._current_operation = ""
            self.is_running_var.set(False)
            
            # Reset cancel button
            self.cancel_button.configure(state="disabled", text="Cancel")
            
            # Reset progress bar style
            self.progress_bar.configure(style="TProgressbar")
        
        # For reset, apply immediately if called from main thread
        try:
            _update()
        except tk.TclError:
            # If not on main thread, schedule update
            with self._update_lock:
                self._pending_updates.append(_update)
    
    def validate(self) -> bool:
        """
        Validate the current state of the panel.
        
        Returns:
            True if the panel state is valid, False otherwise
        """
        # Progress panel is always in a valid state
        return True
    
    def is_operation_running(self) -> bool:
        """
        Check if an operation is currently running.
        
        Returns:
            True if an operation is in progress, False otherwise
        """
        return self._is_processing
    
    def set_verbose_mode(self, enabled: bool) -> None:
        """
        Set verbose mode programmatically.
        
        Args:
            enabled: Whether to enable verbose mode
        """
        self.verbose_enabled_var.set(enabled)
    
    def is_verbose_enabled(self) -> bool:
        """
        Check if verbose mode is enabled.
        
        Returns:
            True if verbose mode is enabled, False otherwise
        """
        return self.verbose_enabled_var.get()
    
    def get_current_progress(self) -> float:
        """
        Get the current progress percentage.
        
        Returns:
            Current progress percentage (0.0 to 100.0)
        """
        return self.progress_var.get()
    
    def get_current_status(self) -> str:
        """
        Get the current status message.
        
        Returns:
            Current status message
        """
        return self.status_var.get()
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics for monitoring.
        
        Returns:
            Dictionary containing performance metrics
        """
        with self._update_lock:
            pending_count = len(self._pending_updates)
        
        return {
            'total_updates': self._update_count,
            'dropped_updates': self._dropped_updates,
            'pending_updates': pending_count,
            'is_processing': self._is_processing
        }
    
    def optimize_performance(self) -> None:
        """Optimize performance by clearing old updates and resetting counters."""
        with self._update_lock:
            # Clear old pending updates if queue is too large
            if len(self._pending_updates) > 20:
                self._pending_updates = self._pending_updates[-10:]  # Keep only recent
                self._dropped_updates += len(self._pending_updates) - 10
        
        # Reset counters periodically
        if self._update_count > 1000:
            self._update_count = 0
            self._dropped_updates = 0