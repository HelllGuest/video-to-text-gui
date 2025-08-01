"""
Cross-platform utility functions for the Video-to-Text application.

This module provides platform-specific functionality for file dialogs,
path handling, native look and feel adaptations, and screen resolution handling.
"""

import os
import sys
import platform
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path


class PlatformInfo:
    """Information about the current platform."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.release = platform.release()
        self.version = platform.version()
        self.machine = platform.machine()
        self.processor = platform.processor()
        
    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.system == 'windows'
    
    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.system == 'darwin'
    
    @property
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.system == 'linux'
    
    @property
    def is_unix_like(self) -> bool:
        """Check if running on Unix-like system (macOS or Linux)."""
        return self.is_macos or self.is_linux
    
    def get_platform_name(self) -> str:
        """Get user-friendly platform name."""
        if self.is_windows:
            return "Windows"
        elif self.is_macos:
            return "macOS"
        elif self.is_linux:
            return "Linux"
        else:
            return self.system.title()


# Global platform info instance
PLATFORM = PlatformInfo()


class FileDialogConfig:
    """Platform-specific file dialog configurations."""
    
    @staticmethod
    def get_video_file_types() -> List[Tuple[str, str]]:
        """
        Get platform-appropriate video file type filters.
        
        Returns:
            List of (description, pattern) tuples for file dialog
        """
        base_types = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("MP4 files", "*.mp4 *.m4v"),
            ("AVI files", "*.avi"),
            ("MOV files", "*.mov"),
            ("MKV files", "*.mkv"),
            ("WMV files", "*.wmv"),
            ("All files", "*.*")
        ]
        
        if PLATFORM.is_macos:
            # macOS prefers specific extensions and may handle some formats differently
            return [
                ("Video files", "*.mp4 *.mov *.m4v *.avi *.mkv *.webm"),
                ("MP4 files", "*.mp4 *.m4v"),
                ("QuickTime files", "*.mov"),
                ("AVI files", "*.avi"),
                ("MKV files", "*.mkv"),
                ("All files", "*")
            ]
        elif PLATFORM.is_windows:
            # Windows supports WMV and has different handling
            return base_types
        else:  # Linux and others
            # Linux typically has good support for open formats
            return [
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.ogv"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MKV files", "*.mkv"),
                ("WebM files", "*.webm"),
                ("All files", "*")
            ]
    
    @staticmethod
    def get_transcript_file_types() -> List[Tuple[str, str]]:
        """
        Get platform-appropriate transcript file type filters.
        
        Returns:
            List of (description, pattern) tuples for file dialog
        """
        return [
            ("Text files", "*.txt"),
            ("JSON files", "*.json"),
            ("All files", "*.*" if PLATFORM.is_windows else "*")
        ]
    
    @staticmethod
    def get_dialog_options() -> Dict[str, Any]:
        """
        Get platform-specific dialog options.
        
        Returns:
            Dictionary of dialog options
        """
        options = {}
        
        if PLATFORM.is_macos:
            # macOS specific options
            options.update({
                'message': None,  # Use title instead of message on macOS
            })
        elif PLATFORM.is_windows:
            # Windows specific options
            options.update({
                'parent': None,  # Let Windows handle parent window
            })
        else:  # Linux
            # Linux specific options
            options.update({
                'parent': None,
            })
        
        return options


class PathUtils:
    """Platform-specific path handling utilities."""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalize path for the current platform.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path string
        """
        if not path:
            return path
        
        # Convert to Path object for cross-platform handling
        path_obj = Path(path)
        
        # Resolve to absolute path and normalize
        try:
            normalized = path_obj.resolve()
            return str(normalized)
        except (OSError, ValueError):
            # If resolution fails, just normalize separators
            return str(path_obj)
    
    @staticmethod
    def get_default_directory(dir_type: str = "home") -> str:
        """
        Get platform-appropriate default directory.
        
        Args:
            dir_type: Type of directory ('home', 'documents', 'videos', 'desktop')
            
        Returns:
            Default directory path
        """
        if dir_type == "home":
            return str(Path.home())
        elif dir_type == "documents":
            if PLATFORM.is_windows:
                return str(Path.home() / "Documents")
            elif PLATFORM.is_macos:
                return str(Path.home() / "Documents")
            else:  # Linux
                return str(Path.home() / "Documents")
        elif dir_type == "videos":
            if PLATFORM.is_windows:
                return str(Path.home() / "Videos")
            elif PLATFORM.is_macos:
                return str(Path.home() / "Movies")
            else:  # Linux
                return str(Path.home() / "Videos")
        elif dir_type == "desktop":
            return str(Path.home() / "Desktop")
        else:
            return str(Path.home())
    
    @staticmethod
    def is_valid_path(path: str) -> bool:
        """
        Check if path is valid for the current platform.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid, False otherwise
        """
        if not path:
            return False
        
        try:
            Path(path)
            return True
        except (ValueError, OSError):
            return False
    
    @staticmethod
    def get_file_extension(path: str) -> str:
        """
        Get file extension in a platform-appropriate way.
        
        Args:
            path: File path
            
        Returns:
            File extension (including dot)
        """
        return Path(path).suffix.lower()
    
    @staticmethod
    def join_paths(*parts: str) -> str:
        """
        Join path parts using platform-appropriate separator.
        
        Args:
            *parts: Path parts to join
            
        Returns:
            Joined path string
        """
        return str(Path(*parts))


class StyleUtils:
    """Platform-specific styling and appearance utilities."""
    
    @staticmethod
    def configure_native_style(root: tk.Tk) -> None:
        """
        Configure native look and feel for the platform.
        
        Args:
            root: Root tkinter window
        """
        try:
            if PLATFORM.is_windows:
                # Windows-specific styling
                root.tk.call('source', 'azure.tcl')
                root.tk.call('set_theme', 'light')
            elif PLATFORM.is_macos:
                # macOS-specific styling
                style = ttk.Style()
                style.theme_use('aqua')
                
                # Configure macOS-specific options
                root.option_add('*tearOff', False)
            else:  # Linux
                # Linux-specific styling
                style = ttk.Style()
                available_themes = style.theme_names()
                
                # Prefer modern themes
                preferred_themes = ['clam', 'alt', 'default']
                for theme in preferred_themes:
                    if theme in available_themes:
                        style.theme_use(theme)
                        break
        except Exception:
            # If styling fails, continue with default
            pass
    
    @staticmethod
    def get_platform_fonts() -> Dict[str, Tuple[str, int]]:
        """
        Get platform-appropriate font configurations.
        
        Returns:
            Dictionary mapping font types to (family, size) tuples
        """
        if PLATFORM.is_windows:
            return {
                'default': ('Segoe UI', 9),
                'monospace': ('Consolas', 9),
                'heading': ('Segoe UI', 12),
                'small': ('Segoe UI', 8)
            }
        elif PLATFORM.is_macos:
            return {
                'default': ('SF Pro Text', 13),
                'monospace': ('SF Mono', 12),
                'heading': ('SF Pro Display', 16),
                'small': ('SF Pro Text', 11)
            }
        else:  # Linux
            return {
                'default': ('Ubuntu', 10),
                'monospace': ('Ubuntu Mono', 10),
                'heading': ('Ubuntu', 13),
                'small': ('Ubuntu', 9)
            }
    
    @staticmethod
    def get_platform_colors() -> Dict[str, str]:
        """
        Get platform-appropriate color scheme.
        
        Returns:
            Dictionary mapping color names to hex values
        """
        if PLATFORM.is_windows:
            return {
                'accent': '#0078d4',
                'success': '#107c10',
                'warning': '#ff8c00',
                'error': '#d13438',
                'background': '#ffffff',
                'surface': '#f3f2f1'
            }
        elif PLATFORM.is_macos:
            return {
                'accent': '#007aff',
                'success': '#34c759',
                'warning': '#ff9500',
                'error': '#ff3b30',
                'background': '#ffffff',
                'surface': '#f2f2f7'
            }
        else:  # Linux
            return {
                'accent': '#e95420',
                'success': '#0e8420',
                'warning': '#f99500',
                'error': '#c7162b',
                'background': '#ffffff',
                'surface': '#f6f6f6'
            }


class ScreenUtils:
    """Screen resolution and DPI handling utilities."""
    
    @staticmethod
    def get_screen_info(root: tk.Tk) -> Dict[str, Any]:
        """
        Get screen information for the current display.
        
        Args:
            root: Root tkinter window
            
        Returns:
            Dictionary containing screen information
        """
        try:
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Get DPI information
            dpi_x = root.winfo_fpixels('1i')
            dpi_y = root.winfo_fpixels('1i')
            
            return {
                'width': screen_width,
                'height': screen_height,
                'dpi_x': dpi_x,
                'dpi_y': dpi_y,
                'scale_factor': dpi_x / 96.0  # 96 DPI is standard
            }
        except Exception:
            # Fallback values
            return {
                'width': 1920,
                'height': 1080,
                'dpi_x': 96,
                'dpi_y': 96,
                'scale_factor': 1.0
            }
    
    @staticmethod
    def calculate_window_size(base_width: int, base_height: int, 
                            screen_info: Dict[str, Any]) -> Tuple[int, int]:
        """
        Calculate appropriate window size based on screen resolution.
        
        Args:
            base_width: Base window width
            base_height: Base window height
            screen_info: Screen information from get_screen_info()
            
        Returns:
            Tuple of (width, height) for the window
        """
        screen_width = screen_info['width']
        screen_height = screen_info['height']
        scale_factor = screen_info.get('scale_factor', 1.0)
        
        # Scale base size by DPI scale factor
        scaled_width = int(base_width * scale_factor)
        scaled_height = int(base_height * scale_factor)
        
        # Ensure window doesn't exceed 80% of screen size
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        final_width = min(scaled_width, max_width)
        final_height = min(scaled_height, max_height)
        
        # Ensure minimum size
        min_width = 600
        min_height = 400
        
        return (max(final_width, min_width), max(final_height, min_height))
    
    @staticmethod
    def center_window(root: tk.Tk, width: int, height: int) -> None:
        """
        Center window on screen.
        
        Args:
            root: Root tkinter window
            width: Window width
            height: Window height
        """
        try:
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            # Fallback to default geometry
            root.geometry(f"{width}x{height}")

def get_platform_info() -> PlatformInfo:
    """
    Get platform information instance.
    
    Returns:
        PlatformInfo instance
    """
    return PLATFORM


def apply_platform_optimizations(root: tk.Tk) -> None:
    """
    Apply platform-specific optimizations to the root window.
    
    Args:
        root: Root tkinter window
    """
    try:
        # Configure native styling
        StyleUtils.configure_native_style(root)
        
        # Set platform-appropriate window properties
        if PLATFORM.is_macos:
            # macOS specific optimizations
            root.createcommand('tk::mac::ReopenApplication', root.deiconify)
            root.createcommand('tk::mac::Quit', root.quit)
        elif PLATFORM.is_windows:
            # Windows specific optimizations
            try:
                # Enable DPI awareness on Windows
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
        
        # Configure window manager properties
        root.wm_protocol("WM_DELETE_WINDOW", root.quit)
        
    except Exception:
        # If optimizations fail, continue without them
        pass