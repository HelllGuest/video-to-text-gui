"""
File management utilities for the Video-to-Text application.

This module provides the FileManager class that handles video file validation,
transcript saving in multiple formats, and temporary file management with
proper cleanup.
"""

import os
import json
import tempfile
import shutil
import threading
import weakref
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime

from ..core.interfaces import IFileManager
from .error_handler import get_error_handler, ErrorCategory
from .validation import FileValidator, ValidationResult
from .platform_utils import PathUtils, PLATFORM


class FileManager(IFileManager):
    """
    Handles file operations for video processing and transcript management.
    
    This class provides methods for validating video files, saving transcripts
    in different formats, and managing temporary files with automatic cleanup.
    """
    
    # Supported video file extensions
    SUPPORTED_VIDEO_EXTENSIONS = {
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', 
        '.m4v', '.3gp', '.ogv', '.ts', '.mts', '.m2ts'
    }
    
    def __init__(self):
        """Initialize the FileManager with temporary file tracking."""
        self._temp_files: Set[str] = set()
        self._temp_dirs: Set[str] = set()
        self._cleanup_lock = threading.Lock()
        self._cleanup_callbacks = weakref.WeakSet()
        self.error_handler = get_error_handler()
        self.validator = FileValidator()
        
        self._max_temp_files = 50
        self._cleanup_threshold = 10
    
    def validate_video_file(self, filepath: str) -> bool:
        """
        Validate that a video file exists and is in a supported format.
        
        Args:
            filepath: Path to the video file to validate
            
        Returns:
            True if the file is valid, False otherwise
        """
        try:
            result = self.validator.validate_video_file(filepath)
            return result.is_valid
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                category=ErrorCategory.FILE_SYSTEM,
                user_message=f"Error validating video file: {str(e)}",
                show_dialog=False
            )
            return False
    
    def get_video_validation_result(self, filepath: str) -> ValidationResult:
        """
        Get detailed validation result for a video file.
        
        Args:
            filepath: Path to the video file to validate
            
        Returns:
            ValidationResult with detailed information
        """
        try:
            return self.validator.validate_video_file(filepath)
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                category=ErrorCategory.FILE_SYSTEM,
                show_dialog=False
            )
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported video file extensions.
        
        Returns:
            List of supported file extensions including the dot
        """
        return sorted(list(self.SUPPORTED_VIDEO_EXTENSIONS))
    
    def save_transcript(self, text: str, filepath: str, format: str) -> bool:
        """
        Save transcript text to a file in the specified format.
        
        Args:
            text: The transcript text to save
            filepath: Path where the transcript should be saved
            format: Output format ('txt' or 'json')
            
        Returns:
            True if save was successful, False otherwise
        """
        if not text or not filepath:
            self.error_handler.handle_validation_error(
                "transcript save",
                "Text or filepath is empty",
                show_dialog=False
            )
            return False
        
        try:
            path = Path(filepath)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            format_lower = format.lower()
            
            if format_lower == 'txt':
                return self._save_as_txt(text, path)
            elif format_lower == 'json':
                return self._save_as_json(text, path)
            else:
                self.error_handler.handle_validation_error(
                    "output format",
                    f"Unsupported format: {format}",
                    show_dialog=False
                )
                return False
                
        except (OSError, PermissionError) as e:
            self.error_handler.handle_file_error("save transcript", filepath, e, show_dialog=True)
            return False
        except (ValueError, json.JSONDecodeError) as e:
            self.error_handler.handle_error(e, category=ErrorCategory.FILE_SYSTEM, 
                                          user_message=f"Error saving transcript: {str(e)}", show_dialog=True)
            return False
        except Exception as e:
            self.error_handler.handle_error(e, category=ErrorCategory.FILE_SYSTEM, 
                                          user_message=f"Unexpected error saving transcript: {str(e)}", show_dialog=True)
            return False
    
    def _save_as_txt(self, text: str, path: Path) -> bool:
        """
        Save transcript as plain text file.
        
        Args:
            text: The transcript text to save
            path: Path object for the output file
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            return True
        except (OSError, PermissionError) as e:
            self.error_handler.handle_file_error("save as TXT", str(path), e, show_dialog=False)
            return False
    
    def _save_as_json(self, text: str, path: Path) -> bool:
        """
        Save transcript as JSON file with metadata.
        
        Args:
            text: The transcript text to save
            path: Path object for the output file
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            transcript_data = {
                "transcript": text,
                "timestamp": datetime.now().isoformat(),
                "format_version": "1.0",
                "word_count": len(text.split()) if text else 0,
                "character_count": len(text)
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, PermissionError) as e:
            self.error_handler.handle_file_error("save as JSON", str(path), e, show_dialog=False)
            return False
        except json.JSONDecodeError as e:
            self.error_handler.handle_error(e, category=ErrorCategory.FILE_SYSTEM, 
                                          user_message=f"Error encoding JSON data: {str(e)}", show_dialog=False)
            return False
    
    def create_temp_file(self, suffix: str = '', prefix: str = 'vid2text_') -> Optional[str]:
        """
        Create a temporary file and track it for cleanup with automatic management.
        
        Args:
            suffix: File extension or suffix for the temp file
            prefix: Prefix for the temp file name
            
        Returns:
            Path to the created temporary file, or None if creation failed
        """
        with self._cleanup_lock:
            if len(self._temp_files) >= self._cleanup_threshold:
                self._cleanup_old_temp_files()
        
        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)
            
            with self._cleanup_lock:
                self._temp_files.add(temp_path)
                
                if len(self._temp_files) > self._max_temp_files:
                    self._cleanup_old_temp_files()
            
            return temp_path
            
        except (OSError, PermissionError):
            return None
    
    def create_temp_dir(self, prefix: str = 'vid2text_') -> Optional[str]:
        """
        Create a temporary directory and track it for cleanup.
        
        Args:
            prefix: Prefix for the temp directory name
            
        Returns:
            Path to the created temporary directory, or None if creation failed
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix=prefix)
            self._temp_dirs.add(temp_dir)
            return temp_dir
            
        except (OSError, PermissionError):
            return None
    
    def cleanup_temp_files(self) -> None:
        """Clean up any temporary files and directories created during processing."""
        with self._cleanup_lock:
            self._cleanup_temp_files_internal()
            self._cleanup_temp_dirs_internal()
            
            for callback in list(self._cleanup_callbacks):
                try:
                    callback()
                except Exception:
                    pass
    
    def _cleanup_temp_files_internal(self) -> None:
        """Internal method to clean up temporary files."""
        files_to_remove = []
        
        for temp_file in self._temp_files.copy():
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                files_to_remove.append(temp_file)
            except (OSError, PermissionError):
                pass
        for temp_file in files_to_remove:
            self._temp_files.discard(temp_file)
    
    def _cleanup_temp_dirs_internal(self) -> None:
        """Internal method to clean up temporary directories."""
        dirs_to_remove = []
        
        for temp_dir in self._temp_dirs.copy():
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                dirs_to_remove.append(temp_dir)
            except (OSError, PermissionError):
                pass
        for temp_dir in dirs_to_remove:
            self._temp_dirs.discard(temp_dir)
    
    def _cleanup_old_temp_files(self) -> None:
        """Clean up old temporary files to prevent accumulation."""
        temp_files_with_time = []
        
        for temp_file in list(self._temp_files):
            try:
                if os.path.exists(temp_file):
                    mtime = os.path.getmtime(temp_file)
                    temp_files_with_time.append((temp_file, mtime))
                else:
                    self._temp_files.discard(temp_file)
            except (OSError, PermissionError):
                continue
        
        temp_files_with_time.sort(key=lambda x: x[1])
        files_to_remove = temp_files_with_time[:len(temp_files_with_time) - self._cleanup_threshold]
        
        for temp_file, _ in files_to_remove:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                self._temp_files.discard(temp_file)
            except (OSError, PermissionError):
                pass
    
    def get_temp_file_count(self) -> int:
        """
        Get the number of temporary files currently being tracked.
        
        Returns:
            Number of temporary files and directories being tracked
        """
        return len(self._temp_files) + len(self._temp_dirs)
    
    def validate_output_path(self, filepath: str) -> bool:
        """
        Validate that an output path is writable and in a valid location.
        
        Args:
            filepath: Path to validate for output
            
        Returns:
            True if the path is valid for output, False otherwise
        """
        try:
            result = self.validator.validate_output_path(filepath)
            return result.is_valid
        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.FILE_SYSTEM,
                user_message=f"Error validating output path: {str(e)}",
                show_dialog=False
            )
            return False
    
    def get_output_validation_result(self, filepath: str) -> ValidationResult:
        """
        Get detailed validation result for an output path.
        
        Args:
            filepath: Path to validate for output
            
        Returns:
            ValidationResult with detailed information
        """
        try:
            return self.validator.validate_output_path(filepath)
        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.FILE_SYSTEM,
                show_dialog=False
            )
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    def get_file_size(self, filepath: str) -> Optional[int]:
        """
        Get the size of a file in bytes.
        
        Args:
            filepath: Path to the file
            
        Returns:
            File size in bytes, or None if file doesn't exist or can't be accessed
        """
        try:
            return Path(filepath).stat().st_size
        except (OSError, PermissionError):
            return None
    
    def ensure_extension(self, filepath: str, format: str) -> str:
        """
        Ensure the filepath has the correct extension for the given format.
        
        Args:
            filepath: Original file path
            format: Output format ('txt' or 'json')
            
        Returns:
            File path with correct extension
        """
        path = Path(filepath)
        format_lower = format.lower()
        
        if format_lower == 'txt' and path.suffix.lower() != '.txt':
            return str(path.with_suffix('.txt'))
        elif format_lower == 'json' and path.suffix.lower() != '.json':
            return str(path.with_suffix('.json'))
        
        return filepath
    
    def normalize_path(self, filepath: str) -> str:
        """
        Normalize a file path for the current platform.
        
        Args:
            filepath: Path to normalize
            
        Returns:
            Platform-normalized path
        """
        return PathUtils.normalize_path(filepath)
    
    def is_path_valid(self, filepath: str) -> bool:
        """
        Check if a path is valid for the current platform.
        
        Args:
            filepath: Path to validate
            
        Returns:
            True if path is valid, False otherwise
        """
        return PathUtils.is_valid_path(filepath)
    
    def get_platform_default_directory(self, dir_type: str = "home") -> str:
        """
        Get platform-appropriate default directory.
        
        Args:
            dir_type: Type of directory ('home', 'documents', 'videos', 'desktop')
            
        Returns:
            Default directory path for the platform
        """
        return PathUtils.get_default_directory(dir_type)
    
    def join_paths(self, *parts: str) -> str:
        """
        Join path parts using platform-appropriate separator.
        
        Args:
            *parts: Path parts to join
            
        Returns:
            Joined path string
        """
        return PathUtils.join_paths(*parts)
    
    def get_platform_file_extension(self, filepath: str) -> str:
        """
        Get file extension in a platform-appropriate way.
        
        Args:
            filepath: File path
            
        Returns:
            File extension (including dot)
        """
        return PathUtils.get_file_extension(filepath)
    
    def register_cleanup_callback(self, callback) -> None:
        """
        Register a callback to be called during cleanup.
        
        Args:
            callback: Function to call during cleanup
        """
        self._cleanup_callbacks.add(callback)
    
    def get_temp_file_stats(self) -> dict:
        """
        Get statistics about temporary file usage.
        
        Returns:
            Dictionary containing temp file statistics
        """
        with self._cleanup_lock:
            existing_files = 0
            total_size = 0
            
            for temp_file in self._temp_files:
                try:
                    if os.path.exists(temp_file):
                        existing_files += 1
                        total_size += os.path.getsize(temp_file)
                except (OSError, PermissionError):
                    pass
            
            return {
                'tracked_files': len(self._temp_files),
                'tracked_dirs': len(self._temp_dirs),
                'existing_files': existing_files,
                'total_size_mb': total_size / (1024 * 1024),
                'cleanup_threshold': self._cleanup_threshold,
                'max_temp_files': self._max_temp_files
            }
    
    def optimize_temp_file_management(self) -> None:
        """Optimize temporary file management by cleaning up and adjusting thresholds."""
        with self._cleanup_lock:
            # Clean up non-existent files from tracking
            self._temp_files = {f for f in self._temp_files if os.path.exists(f)}
            self._temp_dirs = {d for d in self._temp_dirs if os.path.exists(d)}
            
            # Adjust cleanup threshold based on usage
            current_count = len(self._temp_files)
            if current_count > self._cleanup_threshold * 2:
                self._cleanup_threshold = min(self._cleanup_threshold + 5, 20)
            elif current_count < self._cleanup_threshold // 2:
                self._cleanup_threshold = max(self._cleanup_threshold - 2, 5)