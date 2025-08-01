"""
About dialog for the Video-to-Text application.

This module provides a simple about dialog with version information
and application details.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional
import webbrowser

from ..utils.version_info import APP_NAME, VERSION, APP_GITHUB_URL


class AboutDialog:
    """
    Simple about dialog displaying application information and version details.
    """
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the about dialog.
        
        Args:
            parent: Parent window for the dialog
        """
        self.parent = parent
        self.dialog: Optional[tk.Toplevel] = None
        
    def show(self) -> None:
        """Show the about dialog."""
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
        self.dialog.title(f"About {APP_NAME}")
        self.dialog.resizable(False, False)
        
        # Set dialog size
        dialog_width = 450
        dialog_height = 350
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
        
        # Header with app icon and title
        self._create_header(main_frame)
        
        # Content area
        self._create_content(main_frame)
        
        # Button area
        self._create_buttons(main_frame)
    
    def _create_header(self, parent: ttk.Frame) -> None:
        """Create the header section with app info."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # App title (centered)
        title_label = ttk.Label(
            header_frame,
            text=APP_NAME,
            font=("TkDefaultFont", 16, "bold"),
            anchor="center"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        # Version (centered)
        version_label = ttk.Label(
            header_frame,
            text=f"Version {VERSION}",
            font=("TkDefaultFont", 11),
            anchor="center"
        )
        version_label.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Brief description (centered)
        desc_label = ttk.Label(
            header_frame,
            text="Cross-platform video transcription tool",
            font=("TkDefaultFont", 10),
            foreground="gray",
            anchor="center"
        )
        desc_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
    
    def _create_content(self, parent: ttk.Frame) -> None:
        """Create the main content area."""
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # About text area
        about_text = scrolledtext.ScrolledText(
            content_frame,
            height=10,
            width=50,
            wrap=tk.WORD,
            state="disabled",
            font=("TkDefaultFont", 10),
            relief="flat",
            borderwidth=1
        )
        about_text.grid(row=0, column=0, sticky="nsew")
        
        # Insert content
        about_text.configure(state="normal")
        
        # Application description
        about_text.insert(tk.END, "About This Application\n", "heading")
        about_text.insert(tk.END, "\n")
        about_text.insert(tk.END, "Video-to-Text is a cross-platform desktop application that converts video files to text transcripts using speech recognition technology.\n\n")
        
        # Features section
        about_text.insert(tk.END, "Key Features:\n", "subheading")
        about_text.insert(tk.END, "• Support for multiple video formats (MP4, AVI, MOV, MKV, etc.)\n")
        about_text.insert(tk.END, "• Text and JSON output formats\n")
        about_text.insert(tk.END, "• Real-time progress tracking\n")
        about_text.insert(tk.END, "• Intuitive graphical interface\n")
        about_text.insert(tk.END, "• Settings persistence\n")
        about_text.insert(tk.END, "• Cross-platform compatibility\n\n")
        
        # License section
        about_text.insert(tk.END, "License:\n", "subheading")
        about_text.insert(tk.END, "This software is released under the MIT License.\n\n")
        
        # Author and Copyright
        about_text.insert(tk.END, "Author:\n", "subheading")
        about_text.insert(tk.END, "Anoop Kumar\n\n")
        
        # Source Code
        about_text.insert(tk.END, "Source Code:\n", "subheading")
        about_text.insert(tk.END, APP_GITHUB_URL + "\n\n", "link")
        
        # Copyright
        about_text.insert(tk.END, "Copyright © 2025 Anoop Kumar\n")
        
        about_text.configure(state="disabled")
        
        # Configure text tags
        about_text.tag_configure("heading", font=("TkDefaultFont", 12, "bold"))
        about_text.tag_configure("subheading", font=("TkDefaultFont", 10, "bold"))
        about_text.tag_configure("link", foreground="blue", underline=True)
        
        # Bind click event to link
        about_text.tag_bind("link", "<Button-1>", lambda e: self._open_github_link())
        about_text.tag_bind("link", "<Enter>", lambda e: about_text.config(cursor="hand2"))
        about_text.tag_bind("link", "<Leave>", lambda e: about_text.config(cursor=""))
    
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
    
    def _open_github_link(self) -> None:
        """Open the GitHub repository link in the default browser."""
        try:
            webbrowser.open(APP_GITHUB_URL)
        except Exception:
            # If opening browser fails, silently ignore
            pass
    
    def _on_close(self) -> None:
        """Handle dialog close."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None


def show_about_dialog(parent: tk.Tk) -> None:
    """
    Show the about dialog.
    
    Args:
        parent: Parent window for the dialog
    """
    dialog = AboutDialog(parent)
    dialog.show()


if __name__ == "__main__":
    # Test the about dialog
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("400x300")
    
    def show_about():
        show_about_dialog(root)
    
    button = ttk.Button(root, text="Show About", command=show_about)
    button.pack(pady=50)
    
    root.mainloop()