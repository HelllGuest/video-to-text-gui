"""
Help dialog for the Video-to-Text application.

This module provides a comprehensive help dialog with detailed usage instructions,
tips, and troubleshooting information for users.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional

from ..utils.version_info import APP_NAME


class HelpDialog:
    """
    Comprehensive help dialog displaying usage instructions and tips.
    """
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the help dialog.
        
        Args:
            parent: Parent window for the dialog
        """
        self.parent = parent
        self.dialog: Optional[tk.Toplevel] = None
        
    def show(self) -> None:
        """Show the help dialog."""
        if self.dialog and self.dialog.winfo_exists():
            # Dialog already exists, bring it to front
            self.dialog.lift()
            self.dialog.focus_force()
            return
        
        self._create_dialog()
        self._setup_content()
        self._center_dialog()
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Focus the dialog
        self.dialog.focus_force()
    
    def _create_dialog(self) -> None:
        """Create the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Help - {APP_NAME}")
        self.dialog.resizable(True, True)
        
        # Set dialog size
        dialog_width = 700
        dialog_height = 600
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        
        # Configure dialog properties
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Configure grid
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
    
    def _setup_content(self) -> None:
        """Set up the dialog content."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self._create_header(main_frame)
        
        # Content area with notebook for organized sections
        self._create_content_notebook(main_frame)
        
        # Button area
        self._create_buttons(main_frame)
    
    def _create_header(self, parent: ttk.Frame) -> None:
        """Create the header section."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="How to Use",
            font=("TkDefaultFont", 16, "bold"),
            anchor="center"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame,
            text="Complete guide to transcribing video files to text",
            font=("TkDefaultFont", 10),
            foreground="gray",
            anchor="center"
        )
        subtitle_label.grid(row=1, column=0, sticky="ew", pady=(5, 0))
    
    def _create_content_notebook(self, parent: ttk.Frame) -> None:
        """Create the content notebook with organized sections."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        # Create different help sections
        self._create_quick_start_tab()
        self._create_detailed_guide_tab()
        self._create_troubleshooting_tab()
        self._create_tips_tab()
    
    def _create_quick_start_tab(self) -> None:
        """Create the quick start guide tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="Quick Start")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Quick start content
        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            state="disabled",
            font=("TkDefaultFont", 10),
            relief="flat",
            borderwidth=1
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Insert content
        text_widget.configure(state="normal")
        
        text_widget.insert(tk.END, "Quick Start Guide\n", "heading")
        text_widget.insert(tk.END, "\n")
        
        text_widget.insert(tk.END, "Step 1: Select Your Video File\n", "subheading")
        text_widget.insert(tk.END, "• Click the 'Browse' button next to 'Video File'\n")
        text_widget.insert(tk.END, "• Choose a video file from your computer\n")
        text_widget.insert(tk.END, "• Supported formats: MP4, AVI, MOV, MKV, WMV, FLV, WebM, 3GP, OGV, TS, MTS, M2TS\n\n")
        
        text_widget.insert(tk.END, "Step 2: Choose Output Location\n", "subheading")
        text_widget.insert(tk.END, "• Click the 'Browse' button next to 'Output File'\n")
        text_widget.insert(tk.END, "• Select where to save your transcript\n")
        text_widget.insert(tk.END, "• Choose a filename for your transcript\n\n")
        
        text_widget.insert(tk.END, "Step 3: Configure Settings\n", "subheading")
        text_widget.insert(tk.END, "• Select output format: TXT (plain text) or JSON (with metadata)\n")
        text_widget.insert(tk.END, "• Enable 'Verbose Mode' for detailed processing information\n\n")
        
        text_widget.insert(tk.END, "Step 4: Start Transcription\n", "subheading")
        text_widget.insert(tk.END, "• Click 'Start Transcription' button\n")
        text_widget.insert(tk.END, "• Monitor progress in the Progress section\n")
        text_widget.insert(tk.END, "• View results when complete\n\n")
        
        text_widget.insert(tk.END, "Step 5: Save Your Transcript\n", "subheading")
        text_widget.insert(tk.END, "• Review the transcribed text in the Results section\n")
        text_widget.insert(tk.END, "• Click 'Save Transcript' to save to your chosen location\n")
        text_widget.insert(tk.END, "• Use 'Copy to Clipboard' to copy text for immediate use\n\n")
        
        text_widget.configure(state="disabled")
        self._configure_text_tags(text_widget)
    
    def _create_detailed_guide_tab(self) -> None:
        """Create the detailed guide tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="Detailed Guide")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Detailed guide content
        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            state="disabled",
            font=("TkDefaultFont", 10),
            relief="flat",
            borderwidth=1
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Insert content
        text_widget.configure(state="normal")
        
        text_widget.insert(tk.END, "Detailed Usage Guide\n", "heading")
        text_widget.insert(tk.END, "\n")
        
        text_widget.insert(tk.END, "File Selection\n", "subheading")
        text_widget.insert(tk.END, "The application supports a wide range of video formats:\n")
        text_widget.insert(tk.END, "• MP4, AVI, MOV, MKV, WMV, FLV, WebM\n")
        text_widget.insert(tk.END, "• M4V, 3GP, OGV, TS, MTS, M2TS\n\n")
        text_widget.insert(tk.END, "Requirements:\n")
        text_widget.insert(tk.END, "• Video file must contain audio track\n")
        text_widget.insert(tk.END, "• File size: 1KB to 10GB\n")
        text_widget.insert(tk.END, "• Clear audio quality for better transcription\n\n")
        
        text_widget.insert(tk.END, "Output Formats\n", "subheading")
        text_widget.insert(tk.END, "TXT Format:\n")
        text_widget.insert(tk.END, "• Plain text transcript\n")
        text_widget.insert(tk.END, "• Simple and readable\n")
        text_widget.insert(tk.END, "• Easy to edit and share\n\n")
        text_widget.insert(tk.END, "JSON Format:\n")
        text_widget.insert(tk.END, "• Structured data with metadata\n")
        text_widget.insert(tk.END, "• Includes timestamp, word count, processing time\n")
        text_widget.insert(tk.END, "• Suitable for further processing\n\n")
        
        text_widget.insert(tk.END, "Progress Monitoring\n", "subheading")
        text_widget.insert(tk.END, "The Progress section shows:\n")
        text_widget.insert(tk.END, "• Current processing stage\n")
        text_widget.insert(tk.END, "• Completion percentage\n")
        text_widget.insert(tk.END, "• Detailed status messages\n")
        text_widget.insert(tk.END, "• Performance metrics (in verbose mode)\n\n")
        
        text_widget.insert(tk.END, "Cancellation\n", "subheading")
        text_widget.insert(tk.END, "• Click 'Cancel' during processing to stop\n")
        text_widget.insert(tk.END, "• Processing will stop gracefully\n")
        text_widget.insert(tk.END, "• Temporary files will be cleaned up\n\n")
        
        text_widget.insert(tk.END, "Settings\n", "subheading")
        text_widget.insert(tk.END, "• Default output format: Set your preferred format\n")
        text_widget.insert(tk.END, "• Verbose mode: Enable for detailed logging\n")
        text_widget.insert(tk.END, "• Directory memory: Remembers last used folders\n")
        text_widget.insert(tk.END, "• Window preferences: Size and position are saved\n\n")
        
        text_widget.configure(state="disabled")
        self._configure_text_tags(text_widget)
    
    def _create_troubleshooting_tab(self) -> None:
        """Create the troubleshooting tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="Troubleshooting")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Troubleshooting content
        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            state="disabled",
            font=("TkDefaultFont", 10),
            relief="flat",
            borderwidth=1
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Insert content
        text_widget.configure(state="normal")
        
        text_widget.insert(tk.END, "Troubleshooting Guide\n", "heading")
        text_widget.insert(tk.END, "\n")
        
        text_widget.insert(tk.END, "Common Issues and Solutions\n", "subheading")
        text_widget.insert(tk.END, "\n")
        
        text_widget.insert(tk.END, "• \"File not found\" or \"Permission denied\"\n", "error")
        text_widget.insert(tk.END, "Solutions:\n")
        text_widget.insert(tk.END, "• Check if the file path is correct\n")
        text_widget.insert(tk.END, "• Ensure the file hasn't been moved or deleted\n")
        text_widget.insert(tk.END, "• Check file permissions\n")
        text_widget.insert(tk.END, "• Close any applications using the file\n")
        text_widget.insert(tk.END, "• Try running as administrator (Windows)\n\n")
        
        text_widget.insert(tk.END, "• \"Unsupported video format\"\n", "error")
        text_widget.insert(tk.END, "Solutions:\n")
        text_widget.insert(tk.END, "• Convert video to MP4, AVI, or MOV format\n")
        text_widget.insert(tk.END, "• Use a video converter tool\n")
        text_widget.insert(tk.END, "• Try a different video file\n\n")
        
        text_widget.insert(tk.END, "• \"No audio track found\"\n", "error")
        text_widget.insert(tk.END, "Solutions:\n")
        text_widget.insert(tk.END, "• Ensure the video contains audio\n")
        text_widget.insert(tk.END, "• Check audio settings in the video file\n")
        text_widget.insert(tk.END, "• Try a different video with clear audio\n\n")
        
        text_widget.insert(tk.END, "• \"Network error\" during transcription\n", "error")
        text_widget.insert(tk.END, "Solutions:\n")
        text_widget.insert(tk.END, "• Check your internet connection\n")
        text_widget.insert(tk.END, "• Verify firewall settings allow the application\n")
        text_widget.insert(tk.END, "• Try again later if service is unavailable\n\n")
        
        text_widget.insert(tk.END, "• \"Could not understand the audio\"\n", "error")
        text_widget.insert(tk.END, "Solutions:\n")
        text_widget.insert(tk.END, "• Use video with clearer audio quality\n")
        text_widget.insert(tk.END, "• Reduce background noise in the video\n")
        text_widget.insert(tk.END, "• Ensure speech is clearly audible\n")
        text_widget.insert(tk.END, "• Try shorter video segments\n\n")
        
        text_widget.insert(tk.END, "• \"Memory error\" or \"Out of memory\"\n", "error")
        text_widget.insert(tk.END, "Solutions:\n")
        text_widget.insert(tk.END, "• Close other applications to free memory\n")
        text_widget.insert(tk.END, "• Use a smaller video file\n")
        text_widget.insert(tk.END, "• Split large videos into smaller segments\n")
        text_widget.insert(tk.END, "• Restart the application\n\n")
        
        text_widget.insert(tk.END, "Performance Tips\n", "subheading")
        text_widget.insert(tk.END, "• Use MP4 format for best compatibility\n")
        text_widget.insert(tk.END, "• Keep video files under 2GB for optimal performance\n")
        text_widget.insert(tk.END, "• Ensure stable internet connection\n")
        text_widget.insert(tk.END, "• Close unnecessary applications during processing\n\n")
        
        text_widget.configure(state="disabled")
        self._configure_text_tags(text_widget)
    
    def _create_tips_tab(self) -> None:
        """Create the tips and best practices tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="Tips & Best Practices")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Tips content
        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            state="disabled",
            font=("TkDefaultFont", 10),
            relief="flat",
            borderwidth=1
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Insert content
        text_widget.configure(state="normal")
        
        text_widget.insert(tk.END, "Tips & Best Practices\n", "heading")
        text_widget.insert(tk.END, "\n")
        
        text_widget.insert(tk.END, "For Best Transcription Results\n", "subheading")
        text_widget.insert(tk.END, "• Use videos with clear, high-quality audio\n")
        text_widget.insert(tk.END, "• Minimize background noise and music\n")
        text_widget.insert(tk.END, "• Ensure speakers speak clearly and at normal pace\n")
        text_widget.insert(tk.END, "• Use videos with consistent audio levels\n")
        text_widget.insert(tk.END, "• Avoid videos with multiple overlapping speakers\n\n")
        
        text_widget.insert(tk.END, "Performance Optimization\n", "subheading")
        text_widget.insert(tk.END, "• Convert videos to MP4 format before processing\n")
        text_widget.insert(tk.END, "• Use videos with reasonable file sizes (under 1GB)\n")
        text_widget.insert(tk.END, "• Close other applications during transcription\n")
        text_widget.insert(tk.END, "• Ensure stable internet connection\n")
        text_widget.insert(tk.END, "• Use wired internet connection for large files\n\n")
        
        text_widget.insert(tk.END, "File Organization\n", "subheading")
        text_widget.insert(tk.END, "• Create a dedicated folder for your transcripts\n")
        text_widget.insert(tk.END, "• Use descriptive filenames for easy identification\n")
        text_widget.insert(tk.END, "• Keep original video files for reference\n")
        text_widget.insert(tk.END, "• Use JSON format if you need metadata\n")
        text_widget.insert(tk.END, "• Backup important transcripts\n\n")
        
        text_widget.insert(tk.END, "Advanced Features\n", "subheading")
        text_widget.insert(tk.END, "• Enable verbose mode for detailed processing information\n")
        text_widget.insert(tk.END, "• Use the reset button to start fresh\n")
        text_widget.insert(tk.END, "• Copy results to clipboard for immediate use\n")
        text_widget.insert(tk.END, "• Save transcripts in both formats for flexibility\n")
        text_widget.insert(tk.END, "• Use keyboard shortcuts for faster workflow\n\n")
        
        text_widget.insert(tk.END, "Internet Requirements\n", "subheading")
        text_widget.insert(tk.END, "• Stable internet connection required\n")
        text_widget.insert(tk.END, "• Google Speech Recognition API is used\n")
        text_widget.insert(tk.END, "• No account or API key required\n")
        text_widget.insert(tk.END, "• Processing time depends on video length and internet speed\n")
        text_widget.insert(tk.END, "• Offline processing is not supported\n\n")
        
        text_widget.insert(tk.END, "Pro Tips\n", "subheading")
        text_widget.insert(tk.END, "• Process videos in batches during off-peak hours\n")
        text_widget.insert(tk.END, "• Use the application's memory of last directories\n")
        text_widget.insert(tk.END, "• Keep the application updated for best performance\n")
        text_widget.insert(tk.END, "• Check the log files if you encounter issues\n")
        text_widget.insert(tk.END, "• Use shorter video segments for complex content\n\n")
        
        text_widget.configure(state="disabled")
        self._configure_text_tags(text_widget)
    
    def _configure_text_tags(self, text_widget: scrolledtext.ScrolledText) -> None:
        """Configure text formatting tags."""
        text_widget.tag_configure("heading", font=("TkDefaultFont", 14, "bold"))
        text_widget.tag_configure("subheading", font=("TkDefaultFont", 12, "bold"))
        text_widget.tag_configure("error", foreground="red", font=("TkDefaultFont", 10, "bold"))
    
    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create the button area."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Close button (centered)
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self._on_close,
            width=12
        )
        close_button.grid(row=0, column=0)
        
        # Set focus to close button
        close_button.focus_set()
        
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
        
        # Calculate centered position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Ensure dialog stays on screen
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        x = max(0, min(x, screen_width - dialog_width))
        y = max(0, min(y, screen_height - dialog_height))
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _on_close(self) -> None:
        """Handle dialog close."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None


def show_help_dialog(parent: tk.Tk) -> None:
    """
    Show the help dialog.
    
    Args:
        parent: Parent window for the dialog
    """
    dialog = HelpDialog(parent)
    dialog.show()


if __name__ == "__main__":
    # Test the help dialog
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("400x300")
    
    def show_help():
        show_help_dialog(root)
    
    button = ttk.Button(root, text="Show Help", command=show_help)
    button.pack(pady=50)
    
    root.mainloop() 