"""
Enhanced validation utilities for the Video-to-Text application.

This module provides comprehensive validation functions with detailed
error messages and user feedback for file selection and settings.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

from .error_handler import get_error_handler, ErrorCategory


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    
    Attributes:
        is_valid: Whether the validation passed
        error_message: Error message if validation failed
        warning_message: Optional warning message
        suggestions: List of suggestions to fix the issue
        details: Additional validation details
    """
    is_valid: bool
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    suggestions: List[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.details is None:
            self.details = {}


class FileValidator:
    """
    Enhanced file validation with detailed error messages and suggestions.
    """
    
    # Supported video file extensions with descriptions
    SUPPORTED_EXTENSIONS = {
        '.mp4': 'MPEG-4 Video',
        '.avi': 'Audio Video Interleave',
        '.mov': 'QuickTime Movie',
        '.mkv': 'Matroska Video',
        '.wmv': 'Windows Media Video',
        '.flv': 'Flash Video',
        '.webm': 'WebM Video',
        '.m4v': 'iTunes Video',
        '.3gp': '3GPP Video',
        '.ogv': 'Ogg Video',
        '.ts': 'MPEG Transport Stream',
        '.mts': 'AVCHD Video',
        '.m2ts': 'Blu-ray Video'
    }
    
    # Minimum and maximum file sizes (in bytes)
    MIN_FILE_SIZE = 1024  # 1 KB
    MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB
    
    def __init__(self):
        """Initialize the file validator."""
        self.error_handler = get_error_handler()
    
    def validate_video_file(self, filepath: str) -> ValidationResult:
        """
        Validate a video file with comprehensive checks.
        
        Args:
            filepath: Path to the video file to validate
            
        Returns:
            ValidationResult containing validation outcome and details
        """
        if not filepath:
            return ValidationResult(
                is_valid=False,
                error_message="No file path provided",
                suggestions=["Please select a video file"]
            )
        
        try:
            path = Path(filepath)
            
            if not path.exists():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File does not exist: {filepath}",
                    suggestions=[
                        "Check if the file path is correct",
                        "Ensure the file hasn't been moved or deleted",
                        "Try browsing for the file again"
                    ]
                )
            
            if not path.is_file():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Path is not a file: {filepath}",
                    suggestions=["Please select a file, not a directory"]
                )
            
            extension = path.suffix.lower()
            if extension not in self.SUPPORTED_EXTENSIONS:
                supported_list = ', '.join(sorted(self.SUPPORTED_EXTENSIONS.keys()))
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Unsupported file format: {extension}",
                    suggestions=[
                        f"Supported formats: {supported_list}",
                        "Convert your video to a supported format",
                        "Try using a different video file"
                    ],
                    details={"extension": extension, "supported": list(self.SUPPORTED_EXTENSIONS.keys())}
                )
            
            if not os.access(filepath, os.R_OK):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File is not readable: {filepath}",
                    suggestions=[
                        "Check file permissions",
                        "Ensure the file is not locked by another application",
                        "Try running the application as administrator"
                    ]
                )
            
            file_size = path.stat().st_size
            if file_size == 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="File is empty",
                    suggestions=[
                        "The video file appears to be empty or corrupted",
                        "Try using a different video file"
                    ]
                )
            
            if file_size < self.MIN_FILE_SIZE:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File is too small ({file_size} bytes)",
                    suggestions=[
                        f"Minimum file size is {self.MIN_FILE_SIZE} bytes",
                        "The file may be corrupted or incomplete"
                    ]
                )
            
            if file_size > self.MAX_FILE_SIZE:
                size_gb = file_size / (1024 * 1024 * 1024)
                max_gb = self.MAX_FILE_SIZE / (1024 * 1024 * 1024)
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File is too large ({size_gb:.1f} GB)",
                    suggestions=[
                        f"Maximum file size is {max_gb:.1f} GB",
                        "Try compressing the video or using a smaller file",
                        "Split large videos into smaller segments"
                    ]
                )
            
            format_name = self.SUPPORTED_EXTENSIONS[extension]
            size_mb = file_size / (1024 * 1024)
            
            return ValidationResult(
                is_valid=True,
                details={
                    "file_size": file_size,
                    "size_mb": size_mb,
                    "extension": extension,
                    "format_name": format_name,
                    "path": str(path.resolve())
                }
            )
            
        except (OSError, PermissionError) as e:
            self.error_handler.handle_file_error("validate", filepath, e, show_dialog=False)
            return ValidationResult(
                is_valid=False,
                error_message=f"System error accessing file: {str(e)}",
                suggestions=[
                    "Check file permissions",
                    "Ensure the file is not locked",
                    "Try restarting the application"
                ]
            )
        except Exception as e:
            self.error_handler.handle_error(e, ErrorCategory.VALIDATION, show_dialog=False)
            return ValidationResult(
                is_valid=False,
                error_message=f"Unexpected error validating file: {str(e)}",
                suggestions=["Try selecting a different file"]
            )
    
    def validate_output_path(self, filepath: str) -> ValidationResult:
        """
        Validate an output file path with comprehensive checks.
        
        Args:
            filepath: Path to validate for output
            
        Returns:
            ValidationResult containing validation outcome and details
        """
        if not filepath:
            return ValidationResult(
                is_valid=False,
                error_message="No output path provided",
                suggestions=["Please specify where to save the transcript"]
            )
        
        try:
            path = Path(filepath)
            
            # Check parent directory
            parent_dir = path.parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError) as e:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Cannot create output directory: {parent_dir}",
                        suggestions=[
                            "Choose a different output location",
                            "Check directory permissions",
                            "Ensure the path is valid"
                        ]
                    )
            
            # Check if parent directory is writable
            if not os.access(parent_dir, os.W_OK):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Output directory is not writable: {parent_dir}",
                    suggestions=[
                        "Choose a different output location",
                        "Check directory permissions",
                        "Try running as administrator"
                    ]
                )
            
            # Check if file already exists and is writable
            if path.exists():
                if not path.is_file():
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Output path exists but is not a file: {filepath}",
                        suggestions=["Choose a different filename"]
                    )
                
                if not os.access(filepath, os.W_OK):
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Cannot overwrite existing file: {filepath}",
                        suggestions=[
                            "Choose a different filename",
                            "Check file permissions",
                            "Close any applications using the file"
                        ]
                    )
                
                # Warn about overwriting
                return ValidationResult(
                    is_valid=True,
                    warning_message=f"File already exists and will be overwritten: {path.name}",
                    details={"exists": True, "path": str(path.resolve())}
                )
            
            # Validate filename
            filename = path.name
            if not filename:
                return ValidationResult(
                    is_valid=False,
                    error_message="Invalid filename",
                    suggestions=["Provide a valid filename for the output"]
                )
            
            # Check for invalid characters in filename
            invalid_chars = '<>:"|?*'
            if any(char in filename for char in invalid_chars):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Filename contains invalid characters: {filename}",
                    suggestions=[
                        f"Remove these characters: {invalid_chars}",
                        "Use only letters, numbers, spaces, and basic punctuation"
                    ]
                )
            
            # Check filename length
            if len(filename) > 255:
                return ValidationResult(
                    is_valid=False,
                    error_message="Filename is too long",
                    suggestions=["Use a shorter filename (maximum 255 characters)"]
                )
            
            # Validation passed
            return ValidationResult(
                is_valid=True,
                details={
                    "path": str(path.resolve()),
                    "directory": str(parent_dir.resolve()),
                    "filename": filename,
                    "exists": False
                }
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, ErrorCategory.VALIDATION, show_dialog=False)
            return ValidationResult(
                is_valid=False,
                error_message=f"Error validating output path: {str(e)}",
                suggestions=["Try a different output location"]
            )
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported video file extensions.
        
        Returns:
            List of supported file extensions
        """
        return list(self.SUPPORTED_EXTENSIONS.keys())
    
    def get_extension_description(self, extension: str) -> str:
        """
        Get description for a file extension.
        
        Args:
            extension: File extension (with or without dot)
            
        Returns:
            Description of the file format
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        return self.SUPPORTED_EXTENSIONS.get(extension.lower(), "Unknown format")


class SettingsValidator:
    """
    Enhanced settings validation with detailed error messages.
    """
    
    VALID_OUTPUT_FORMATS = ['txt', 'json']
    GEOMETRY_PATTERN = re.compile(r'^\d+x\d+[+-]\d+[+-]\d+$')
    
    def __init__(self):
        """Initialize the settings validator."""
        self.error_handler = get_error_handler()
    
    def validate_output_format(self, format_value: str) -> ValidationResult:
        """
        Validate output format setting.
        
        Args:
            format_value: Output format to validate
            
        Returns:
            ValidationResult containing validation outcome
        """
        if not format_value:
            return ValidationResult(
                is_valid=False,
                error_message="Output format not specified",
                suggestions=["Choose either 'txt' or 'json' format"]
            )
        
        if format_value.lower() not in self.VALID_OUTPUT_FORMATS:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid output format: {format_value}",
                suggestions=[
                    f"Valid formats: {', '.join(self.VALID_OUTPUT_FORMATS)}",
                    "Use 'txt' for plain text or 'json' for structured data"
                ]
            )
        
        return ValidationResult(
            is_valid=True,
            details={"format": format_value.lower()}
        )
    
    def validate_verbose_mode(self, verbose_value: Any) -> ValidationResult:
        """
        Validate verbose mode setting.
        
        Args:
            verbose_value: Verbose mode value to validate
            
        Returns:
            ValidationResult containing validation outcome
        """
        if not isinstance(verbose_value, bool):
            return ValidationResult(
                is_valid=False,
                error_message=f"Verbose mode must be boolean, got {type(verbose_value).__name__}",
                suggestions=["Use True or False for verbose mode"]
            )
        
        return ValidationResult(
            is_valid=True,
            details={"verbose": verbose_value}
        )
    
    def validate_directory_path(self, path: str, path_name: str) -> ValidationResult:
        """
        Validate a directory path setting.
        
        Args:
            path: Directory path to validate
            path_name: Name of the path setting for error messages
            
        Returns:
            ValidationResult containing validation outcome
        """
        if not isinstance(path, str):
            return ValidationResult(
                is_valid=False,
                error_message=f"{path_name} must be a string",
                suggestions=["Provide a valid directory path"]
            )
        
        # Empty path is valid (will use default)
        if not path:
            return ValidationResult(
                is_valid=True,
                details={"path": path, "exists": False}
            )
        
        try:
            path_obj = Path(path)
            
            # Check if path exists
            if not path_obj.exists():
                return ValidationResult(
                    is_valid=True,  # Non-existent paths are valid, will use default
                    warning_message=f"{path_name} does not exist: {path}",
                    details={"path": path, "exists": False}
                )
            
            # Check if it's a directory
            if not path_obj.is_dir():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"{path_name} is not a directory: {path}",
                    suggestions=["Provide a valid directory path"]
                )
            
            # Check if directory is accessible
            if not os.access(path, os.R_OK):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"{path_name} is not accessible: {path}",
                    suggestions=["Check directory permissions"]
                )
            
            return ValidationResult(
                is_valid=True,
                details={"path": str(path_obj.resolve()), "exists": True}
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid {path_name}: {str(e)}",
                suggestions=["Provide a valid directory path"]
            )
    
    def validate_window_geometry(self, geometry: str) -> ValidationResult:
        """
        Validate window geometry string.
        
        Args:
            geometry: Geometry string to validate
            
        Returns:
            ValidationResult containing validation outcome
        """
        if not isinstance(geometry, str):
            return ValidationResult(
                is_valid=False,
                error_message=f"Window geometry must be a string, got {type(geometry).__name__}",
                suggestions=["Use format: 'widthxheight+x+y'"]
            )
        
        # Empty geometry is valid (will use default)
        if not geometry:
            return ValidationResult(
                is_valid=True,
                details={"geometry": geometry}
            )
        
        # Validate geometry format
        if not self.GEOMETRY_PATTERN.match(geometry):
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid window geometry format: {geometry}",
                suggestions=[
                    "Use format: 'widthxheight+x+y' (e.g., '800x600+100+100')",
                    "Width and height must be positive numbers",
                    "Position can be positive or negative"
                ]
            )
        
        try:
            # Parse and validate dimensions
            parts = geometry.replace('+', ' +').replace('-', ' -').split()
            size_part = parts[0]
            width, height = map(int, size_part.split('x'))
            
            # Validate reasonable dimensions
            if width < 300 or height < 200:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Window size too small: {width}x{height}",
                    suggestions=["Minimum window size is 300x200"]
                )
            
            if width > 3840 or height > 2160:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Window size too large: {width}x{height}",
                    suggestions=["Maximum window size is 3840x2160"]
                )
            
            return ValidationResult(
                is_valid=True,
                details={
                    "geometry": geometry,
                    "width": width,
                    "height": height
                }
            )
            
        except (ValueError, IndexError) as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Error parsing geometry: {str(e)}",
                suggestions=["Use format: 'widthxheight+x+y'"]
            )


def validate_transcription_request(video_path: str, output_path: str, 
                                 output_format: str, verbose: bool) -> Tuple[bool, List[str]]:
    """
    Validate a complete transcription request.
    
    Args:
        video_path: Path to the video file
        output_path: Path for the output file
        output_format: Output format ('txt' or 'json')
        verbose: Verbose mode setting
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    file_validator = FileValidator()
    settings_validator = SettingsValidator()
    
    errors = []
    
    # Validate video file
    video_result = file_validator.validate_video_file(video_path)
    if not video_result.is_valid:
        errors.append(f"Video file: {video_result.error_message}")
    
    # Validate output path
    output_result = file_validator.validate_output_path(output_path)
    if not output_result.is_valid:
        errors.append(f"Output path: {output_result.error_message}")
    
    # Validate output format
    format_result = settings_validator.validate_output_format(output_format)
    if not format_result.is_valid:
        errors.append(f"Output format: {format_result.error_message}")
    
    # Validate verbose setting
    verbose_result = settings_validator.validate_verbose_mode(verbose)
    if not verbose_result.is_valid:
        errors.append(f"Verbose mode: {verbose_result.error_message}")
    
    return len(errors) == 0, errors