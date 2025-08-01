"""
Video-to-Text Version Information: Application Metadata and Build Details.

This module provides comprehensive version information, build details, and
application metadata for the Video-to-Text application. It serves as the
central source of truth for version numbers, application details, and
system information used throughout the application in about dialogs,
help systems, and debugging information.

Features:
- Version Management: Centralized version number and build information.
- Application Metadata: Complete application details and descriptions.
- System Information: Platform and dependency information gathering.
- Build Details: Build date, environment, and configuration information.
- About Dialog Support: Formatted text for user-facing dialogs.
- Debug Information: Comprehensive system details for troubleshooting.
- Dependency Tracking: Information about installed libraries and versions.

Information Provided:
- Version numbers (major, minor, patch, build)
- Application name, description, and author information
- Copyright and license information
- Build date and environment details
- System platform and Python version
- Dependency versions and availability

Usage:
Import version information for use in dialogs and system info:
    from app.utils.version_info import APP_NAME, VERSION, get_version_string
    print(f"{APP_NAME} {VERSION}")

Dependencies:
- Python 3.8+: Core programming language
- datetime: For build date and timestamp information
- sys: For system information gathering
- os: For environment and platform details

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any


# Application version information
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_BUILD = "beta"

# Full version string
VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
if VERSION_BUILD:
    VERSION += f"-{VERSION_BUILD}"

# Application metadata
APP_NAME = "Video-to-Text"
APP_DESCRIPTION = "A cross-platform GUI application for transcribing video files to text using speech recognition"
APP_AUTHOR = "Anoop Kumar"
APP_COPYRIGHT = f"© {datetime.now().year} {APP_AUTHOR}"
APP_LICENSE = "MIT License"
APP_GITHUB_URL = "https://github.com/HelllGuest/video-to-text-gui"

# Build information
BUILD_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
PLATFORM = sys.platform


def get_version_info() -> Dict[str, Any]:
    """
    Get comprehensive version and build information.
    
    Returns:
        Dictionary containing version and build details
    """
    return {
        "version": VERSION,
        "version_major": VERSION_MAJOR,
        "version_minor": VERSION_MINOR,
        "version_patch": VERSION_PATCH,
        "version_build": VERSION_BUILD,
        "app_name": APP_NAME,
        "description": APP_DESCRIPTION,
        "author": APP_AUTHOR,
        "copyright": APP_COPYRIGHT,
        "license": APP_LICENSE,
        "github_url": APP_GITHUB_URL,
        "build_date": BUILD_DATE,
        "python_version": PYTHON_VERSION,
        "platform": PLATFORM
    }


def get_version_string() -> str:
    """
    Get a formatted version string for display.
    
    Returns:
        Formatted version string
    """
    return f"{APP_NAME} v{VERSION}"


def get_about_text() -> str:
    """
    Get formatted about text for display in dialogs.
    
    Returns:
        Multi-line about text
    """
    return f"""{APP_NAME}
Version {VERSION}

{APP_DESCRIPTION}

{APP_COPYRIGHT}
Licensed under {APP_LICENSE}

Built with Python {PYTHON_VERSION} on {PLATFORM}
Build Date: {BUILD_DATE}"""


def get_system_info() -> Dict[str, str]:
    """
    Get system information for debugging and support.
    
    Returns:
        Dictionary containing system information
    """
    import platform
    
    try:
        # Get detailed platform information
        system_info = {
            "Operating System": platform.system(),
            "OS Version": platform.version(),
            "OS Release": platform.release(),
            "Architecture": platform.machine(),
            "Processor": platform.processor(),
            "Python Version": PYTHON_VERSION,
            "Python Implementation": platform.python_implementation(),
            "Python Compiler": platform.python_compiler(),
            "Platform": PLATFORM
        }
        
        # Add memory information if available
        try:
            import psutil
            memory = psutil.virtual_memory()
            system_info["Total Memory"] = f"{memory.total // (1024**3)} GB"
            system_info["Available Memory"] = f"{memory.available // (1024**3)} GB"
        except ImportError:
            pass
        
        return system_info
        
    except Exception as e:
        return {"Error": f"Could not retrieve system information: {str(e)}"}


def get_dependencies_info() -> Dict[str, str]:
    """
    Get information about key dependencies.
    
    Returns:
        Dictionary containing dependency versions
    """
    dependencies = {}
    
    # Check for key dependencies
    dependency_modules = [
        ("tkinter", "tkinter"),
        ("moviepy", "moviepy"),
        ("speech_recognition", "speech_recognition"),
        ("psutil", "psutil")
    ]
    
    for display_name, module_name in dependency_modules:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'Unknown')
            dependencies[display_name] = version
        except ImportError:
            dependencies[display_name] = "Not installed"
        except Exception:
            dependencies[display_name] = "Error"
    
    return dependencies


def print_version_info() -> None:
    """Print version information to console."""
    print(get_version_string())
    print(f"Python {PYTHON_VERSION} on {PLATFORM}")
    print(f"Build: {BUILD_DATE}")


def print_full_info() -> None:
    """Print comprehensive application and system information."""
    print("=" * 50)
    print(get_about_text())
    print("=" * 50)
    
    print("\nSystem Information:")
    for key, value in get_system_info().items():
        print(f"  {key}: {value}")
    
    print("\nDependencies:")
    for key, value in get_dependencies_info().items():
        print(f"  {key}: {value}")
    
    print("=" * 50)


if __name__ == "__main__":
    print_full_info()