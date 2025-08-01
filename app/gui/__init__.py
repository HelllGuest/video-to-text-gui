"""
Video-to-Text GUI Components: User Interface Package.

This package contains all graphical user interface components for the Video-to-Text
application, built with tkinter for cross-platform compatibility. The GUI follows
a modular design with separate panels for different functionality areas, providing
an intuitive and user-friendly interface for video transcription operations.

Features:
- Cross-Platform GUI: Built with tkinter for Windows, macOS, and Linux support.
- Modular Design: Separate panels for different functionality areas.
- Responsive Layout: Adaptive interface that works on different screen sizes.
- Progress Tracking: Real-time progress updates with visual feedback.
- Error Handling: User-friendly error dialogs with helpful messages.
- Settings Management: Intuitive configuration interface.
- File Management: Easy file selection with drag-and-drop support.
- Results Display: Formatted transcript display with copy/save options.

Components:
- VideoToTextApp: Main application controller and entry point
- MainWindow: Primary application window with menu and layout
- FileSelectionPanel: Video file selection and output configuration
- ConfigurationPanel: Settings and preferences management
- ProgressPanel: Real-time progress tracking and status display
- ResultsPanel: Transcript display and export functionality
- Dialog Components: About, help, and error dialog windows

Usage:
Import and use GUI components to build the interface:
    from app.gui import VideoToTextApp
    app = VideoToTextApp()
    app.run()

Dependencies:
- Python 3.8+: Core programming language
- tkinter: Standard Python GUI library
- Platform-specific styling libraries for native look and feel

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

from .app import VideoToTextApp
from .main_window import MainWindow
from .file_selection_panel import FileSelectionPanel
from .configuration_panel import ConfigurationPanel
from .progress_panel import ProgressPanel
from .results_panel import ResultsPanel

__all__ = [
    'VideoToTextApp',
    'MainWindow',
    'FileSelectionPanel',
    'ConfigurationPanel',
    'ProgressPanel',
    'ResultsPanel'
]