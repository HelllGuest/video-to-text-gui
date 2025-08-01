"""
Results panel for the Video-to-Text application.

This module contains the ResultsPanel class which provides
transcript display, copy-to-clipboard functionality, and result formatting.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, Callable
from threading import Lock

from ..core.interfaces import IGUIPanel
from ..core.models import TranscriptionResult
from ..utils.platform_utils import StyleUtils, PLATFORM


class ResultsPanel(IGUIPanel):
    """
    GUI panel for displaying transcription results and handling output.
    
    This class provides a scrollable text area for transcript display,
    copy-to-clipboard functionality, success/error message display,
    and text formatting for long transcripts.
    """
    
    def __init__(self, parent_frame: ttk.Frame,
                 on_save_request: Optional[Callable[[str], None]] = None):
        """
        Initialize the results panel.
        
        Args:
            parent_frame: Parent tkinter frame to contain this panel
            on_save_request: Optional callback when user requests to save results
        """
        self.parent_frame = parent_frame
        self.on_save_request = on_save_request
        
        # Initialize variables
        self.result_text_var = tk.StringVar()
        self.status_var = tk.StringVar()
        
        self._update_lock = Lock()
        self._pending_updates = []
        
        self._current_transcript = ""
        self._current_result: Optional[TranscriptionResult] = None
        self._has_results = False
        
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
        self.parent_frame.grid_rowconfigure(1, weight=1)  # Results text area
        
        # Status section
        status_frame = ttk.Frame(self.parent_frame)
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("TkDefaultFont", 9, "bold")
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Action buttons frame
        buttons_frame = ttk.Frame(status_frame)
        buttons_frame.grid(row=0, column=1, sticky="e")
        
        # Copy to clipboard button
        self.copy_button = ttk.Button(
            buttons_frame,
            text="Copy to Clipboard",
            command=self._on_copy_clicked,
            state="disabled"
        )
        self.copy_button.grid(row=0, column=0, padx=(0, 5))
        
        # Save to file button
        self.save_button = ttk.Button(
            buttons_frame,
            text="Save to File",
            command=self._on_save_clicked,
            state="disabled"
        )
        self.save_button.grid(row=0, column=1, padx=(0, 5))
        
        # Clear results button
        self.clear_button = ttk.Button(
            buttons_frame,
            text="Clear",
            command=self.clear_results
        )
        self.clear_button.grid(row=0, column=2)
        
        # Results text area with scrolling
        text_frame = ttk.Frame(self.parent_frame)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        fonts = StyleUtils.get_platform_fonts()
        default_font = fonts.get('default', ('TkDefaultFont', 10))
        
        self.results_text = scrolledtext.ScrolledText(
            text_frame,
            height=12,
            width=60,
            wrap=tk.WORD,
            state="disabled",
            font=default_font,
            padx=10,
            pady=10
        )
        self.results_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure text tags for different content types
        self._setup_text_tags()
        
        # Results info section
        info_frame = ttk.Frame(self.parent_frame)
        info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Character/word count
        self.info_var = tk.StringVar()
        self.info_label = ttk.Label(
            info_frame,
            textvariable=self.info_var,
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        self.info_label.grid(row=0, column=0, sticky="w")
        
        # Processing time info
        self.time_var = tk.StringVar()
        self.time_label = ttk.Label(
            info_frame,
            textvariable=self.time_var,
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        self.time_label.grid(row=0, column=2, sticky="e")
    
    def _setup_text_tags(self) -> None:
        """Set up text tags for different types of content."""
        colors = StyleUtils.get_platform_colors()
        fonts = StyleUtils.get_platform_fonts()
        default_font = fonts.get('default', ('TkDefaultFont', 10))
        small_font = fonts.get('small', (default_font[0], max(9, default_font[1] - 1)))
        heading_font = fonts.get('heading', (default_font[0], default_font[1] + 1))
        self.results_text.tag_configure("success", foreground=colors.get('success', 'green'), font=(default_font[0], default_font[1], "bold"))
        self.results_text.tag_configure("error", foreground=colors.get('error', 'red'), font=(default_font[0], default_font[1], "bold"))
        self.results_text.tag_configure("warning", foreground=colors.get('warning', 'orange'), font=(default_font[0], default_font[1], "bold"))
        self.results_text.tag_configure("transcript", foreground="black", font=default_font)
        self.results_text.tag_configure("metadata", foreground="gray", font=(small_font[0], small_font[1], "italic"))
        self.results_text.tag_configure("header", foreground=colors.get('accent', 'blue'), font=(heading_font[0], heading_font[1], "bold"))
    
    def _setup_bindings(self) -> None:
        """Set up event bindings for the widgets."""
        # Set up periodic update checking for thread safety
        self._schedule_update_check()
        

    def _schedule_update_check(self) -> None:
        """Schedule periodic checking for pending updates."""
        try:
            self._process_pending_updates()
            # Schedule next check
            self.parent_frame.after(100, self._schedule_update_check)
        except tk.TclError:
            # Widget has been destroyed, stop scheduling
            pass
    
    def _process_pending_updates(self) -> None:
        """Process any pending updates from background threads."""
        with self._update_lock:
            if self._pending_updates:
                for update_func in self._pending_updates:
                    try:
                        update_func()
                    except Exception as e:
                        # Log error but continue processing other updates
                        pass
                self._pending_updates.clear()
    
    def _select_all(self, event=None) -> str:
        """Select all text in the results area."""
        if self._has_results:
            self.results_text.tag_add(tk.SEL, "1.0", tk.END)
        return "break"
    
    def _on_copy_clicked(self) -> None:
        """Handle copy to clipboard button click."""
        if not self._has_results or not self._current_transcript:
            messagebox.showwarning("No Content", "No transcript content to copy.")
            return
        
        try:
            # Clear clipboard and set new content
            self.parent_frame.clipboard_clear()
            self.parent_frame.clipboard_append(self._current_transcript)
            
            # Show temporary feedback
            original_text = self.copy_button.cget("text")
            self.copy_button.configure(text="Copied!")
            self.parent_frame.after(2000, lambda: self.copy_button.configure(text=original_text))
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy to clipboard:\n{str(e)}")
    
    def _on_save_clicked(self) -> None:
        """Handle save to file button click."""
        if not self._has_results or not self._current_transcript:
            messagebox.showwarning("No Content", "No transcript content to save.")
            return
        
        if self.on_save_request:
            self.on_save_request(self._current_transcript)
    
    def display_transcript(self, text: str) -> None:
        """
        Display transcribed text in the results area (thread-safe).
        
        Args:
            text: Transcribed text to display
        """
        def _update():
            self._display_transcript_internal(text)
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def _display_transcript_internal(self, text: str) -> None:
        """
        Internal method to display transcribed text.
        
        Args:
            text: Transcribed text to display
        """
        # Enable text widget for editing
        self.results_text.configure(state="normal")
        
        try:
            # Clear existing content
            self.results_text.delete("1.0", tk.END)
            
            # Add header
            self.results_text.insert(tk.END, "Transcription Results\n", "header")
            self.results_text.insert(tk.END, "=" * 50 + "\n\n", "metadata")
            
            # Add transcript content
            if text.strip():
                self.results_text.insert(tk.END, text, "transcript")
                self._current_transcript = text.strip()
                self._has_results = True
                
                # Update status
                self.status_var.set("Transcription completed successfully")
                self.status_label.configure(foreground="green")
                
                # Enable action buttons
                self.copy_button.configure(state="normal")
                self.save_button.configure(state="normal")
                
                # Update info
                self._update_text_info(text)
                
            else:
                self.results_text.insert(tk.END, "No transcript content available.", "warning")
                self._current_transcript = ""
                self._has_results = False
                
                # Update status
                self.status_var.set("No content transcribed")
                self.status_label.configure(foreground="orange")
                
                # Disable action buttons
                self.copy_button.configure(state="disabled")
                self.save_button.configure(state="disabled")
                
                # Clear info
                self.info_var.set("")
                self.time_var.set("")
            
        finally:
            # Disable text widget to prevent user editing
            self.results_text.configure(state="disabled")
    
    def display_result(self, result: TranscriptionResult) -> None:
        """
        Display a complete transcription result (thread-safe).
        
        Args:
            result: TranscriptionResult object containing all result information
        """
        def _update():
            self._display_result_internal(result)
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def _display_result_internal(self, result: TranscriptionResult) -> None:
        """
        Internal method to display a complete transcription result.
        
        Args:
            result: TranscriptionResult object containing all result information
        """
        self._current_result = result
        
        # Enable text widget for editing
        self.results_text.configure(state="normal")
        
        try:
            # Clear existing content
            self.results_text.delete("1.0", tk.END)
            
            if result.success:
                # Success case
                self.results_text.insert(tk.END, "Transcription Results\n", "header")
                self.results_text.insert(tk.END, "=" * 50 + "\n\n", "metadata")
                
                if result.transcript and result.transcript.strip():
                    self.results_text.insert(tk.END, result.transcript, "transcript")
                    self._current_transcript = result.transcript.strip()
                    self._has_results = True
                    
                    # Update status
                    self.status_var.set("Transcription completed successfully")
                    self.status_label.configure(foreground="green")
                    
                    # Enable action buttons
                    self.copy_button.configure(state="normal")
                    self.save_button.configure(state="normal")
                    
                    # Update info
                    self._update_text_info(result.transcript)
                    
                    # Update processing time
                    if result.processing_time > 0:
                        self.time_var.set(f"Processing time: {result.processing_time:.1f}s")
                    
                    # Add file info if available
                    if result.output_file_path:
                        self.results_text.insert(tk.END, f"\n\nSaved to: {result.output_file_path}", "metadata")
                    
                else:
                    self.results_text.insert(tk.END, "No transcript content available.", "warning")
                    self._current_transcript = ""
                    self._has_results = False
                    
                    # Update status
                    self.status_var.set("No content transcribed")
                    self.status_label.configure(foreground="orange")
                    
                    # Disable action buttons
                    self.copy_button.configure(state="disabled")
                    self.save_button.configure(state="disabled")
            
            else:
                # Error case
                self.results_text.insert(tk.END, "Transcription Failed\n", "header")
                self.results_text.insert(tk.END, "=" * 50 + "\n\n", "metadata")
                
                error_message = result.error_message or "Unknown error occurred"
                self.results_text.insert(tk.END, f"Error: {error_message}", "error")
                
                self._current_transcript = ""
                self._has_results = False
                
                # Update status
                self.status_var.set(f"Transcription failed: {error_message}")
                self.status_label.configure(foreground="red")
                
                # Disable action buttons
                self.copy_button.configure(state="disabled")
                self.save_button.configure(state="disabled")
                
                # Clear info
                self.info_var.set("")
                
                # Update processing time if available
                if result.processing_time > 0:
                    self.time_var.set(f"Processing time: {result.processing_time:.1f}s")
                else:
                    self.time_var.set("")
            
        finally:
            # Disable text widget to prevent user editing
            self.results_text.configure(state="disabled")
    
    def show_success(self, message: str) -> None:
        """
        Display a success message (thread-safe).
        
        Args:
            message: Success message to display
        """
        def _update():
            self.status_var.set(message)
            self.status_label.configure(foreground="green")
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def show_error(self, message: str) -> None:
        """
        Display an error message (thread-safe).
        
        Args:
            message: Error message to display
        """
        def _update():
            self._show_error_internal(message)
        
        # Schedule update on main thread
        with self._update_lock:
            self._pending_updates.append(_update)
    
    def _show_error_internal(self, message: str) -> None:
        """
        Internal method to display an error message.
        
        Args:
            message: Error message to display
        """
        # Enable text widget for editing
        self.results_text.configure(state="normal")
        
        try:
            # Clear existing content
            self.results_text.delete("1.0", tk.END)
            
            # Add error header
            self.results_text.insert(tk.END, "Error\n", "header")
            self.results_text.insert(tk.END, "=" * 50 + "\n\n", "metadata")
            
            # Add error message
            self.results_text.insert(tk.END, message, "error")
            
            # Update state
            self._current_transcript = ""
            self._has_results = False
            
            # Update status
            self.status_var.set(f"Error: {message}")
            self.status_label.configure(foreground="red")
            
            # Disable action buttons
            self.copy_button.configure(state="disabled")
            self.save_button.configure(state="disabled")
            
            # Clear info
            self.info_var.set("")
            self.time_var.set("")
            
        finally:
            # Disable text widget to prevent user editing
            self.results_text.configure(state="disabled")
    
    def _update_text_info(self, text: str) -> None:
        """
        Update the text information display.
        
        Args:
            text: Text to analyze for information
        """
        if not text or not text.strip():
            self.info_var.set("")
            return
        
        # Count characters and words
        char_count = len(text)
        word_count = len(text.split())
        line_count = text.count('\n') + 1
        
        # Format info string
        info_parts = []
        if char_count > 0:
            info_parts.append(f"{char_count:,} characters")
        if word_count > 0:
            info_parts.append(f"{word_count:,} words")
        if line_count > 1:
            info_parts.append(f"{line_count} lines")
        
        self.info_var.set(" • ".join(info_parts))
    
    def clear_results(self) -> None:
        """Clear all results and reset the panel."""
        def _update():
            self._clear_results_internal()
        
        # For clear, apply immediately if called from main thread
        try:
            _update()
        except tk.TclError:
            # If not on main thread, schedule update
            with self._update_lock:
                self._pending_updates.append(_update)
    
    def _clear_results_internal(self) -> None:
        """Internal method to clear all results."""
        # Enable text widget for editing
        self.results_text.configure(state="normal")
        
        try:
            # Clear text content
            self.results_text.delete("1.0", tk.END)
            
            # Add placeholder text
            self.results_text.insert(tk.END, "No results to display.\n\n", "metadata")
            self.results_text.insert(tk.END, "Start a transcription to see results here.", "metadata")
            
        finally:
            # Disable text widget to prevent user editing
            self.results_text.configure(state="disabled")
        
        # Reset state
        self._current_transcript = ""
        self._current_result = None
        self._has_results = False
        
        # Update status
        self.status_var.set("Ready for transcription")
        self.status_label.configure(foreground="black")
        
        # Disable action buttons
        self.copy_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        
        # Clear info
        self.info_var.set("")
        self.time_var.set("")
    
    def reset(self) -> None:
        """Reset the panel to its initial state."""
        self.clear_results()
    
    def validate(self) -> bool:
        """
        Validate the current state of the panel.
        
        Returns:
            True if the panel state is valid, False otherwise
        """
        # Results panel is always in a valid state
        return True
    
    def has_results(self) -> bool:
        """
        Check if the panel currently has results to display.
        
        Returns:
            True if results are available, False otherwise
        """
        return self._has_results
    
    def get_current_transcript(self) -> str:
        """
        Get the current transcript text.
        
        Returns:
            Current transcript text, or empty string if none
        """
        return self._current_transcript
    
    def get_current_result(self) -> Optional[TranscriptionResult]:
        """
        Get the current transcription result object.
        
        Returns:
            Current TranscriptionResult object, or None if none
        """
        return self._current_result
    
    def copy_to_clipboard(self) -> bool:
        """
        Copy current transcript to clipboard programmatically.
        
        Returns:
            True if copy was successful, False otherwise
        """
        if not self._has_results or not self._current_transcript:
            return False
        
        try:
            self.parent_frame.clipboard_clear()
            self.parent_frame.clipboard_append(self._current_transcript)
            return True
        except Exception:
            return False
    
    def set_font_size(self, size: int) -> None:
        """
        Set the font size for the results display.
        
        Args:
            size: Font size to set
        """
        try:
            # Update font for transcript text
            current_font = self.results_text.cget("font")
            if isinstance(current_font, str):
                font_family = "TkDefaultFont"
            else:
                font_family = current_font[0] if current_font else "TkDefaultFont"
            
            new_font = (font_family, size)
            self.results_text.configure(font=new_font)
            
            # Update text tags with new font size
            self.results_text.tag_configure("transcript", font=(font_family, size))
            self.results_text.tag_configure("success", font=(font_family, size, "bold"))
            self.results_text.tag_configure("error", font=(font_family, size, "bold"))
            self.results_text.tag_configure("warning", font=(font_family, size, "bold"))
            self.results_text.tag_configure("header", font=(font_family, size + 1, "bold"))
            self.results_text.tag_configure("metadata", font=(font_family, max(8, size - 1), "italic"))
            
        except Exception:
            # If font setting fails, continue silently
            pass
    
    def export_results(self, format_type: str = "txt") -> str:
        """
        Export current results in the specified format.
        
        Args:
            format_type: Export format ('txt' or 'json')
            
        Returns:
            Formatted results string, or empty string if no results
        """
        if not self._has_results or not self._current_transcript:
            return ""
        
        if format_type.lower() == "json":
            import json
            from datetime import datetime
            
            export_data = {
                "transcript": self._current_transcript,
                "export_timestamp": datetime.now().isoformat(),
                "character_count": len(self._current_transcript),
                "word_count": len(self._current_transcript.split())
            }
            
            if self._current_result:
                export_data.update({
                    "success": self._current_result.success,
                    "processing_time": self._current_result.processing_time,
                    "output_file_path": self._current_result.output_file_path
                })
            
            return json.dumps(export_data, indent=2)
        
        else:  # Default to txt format
            return self._current_transcript