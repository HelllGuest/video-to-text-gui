#!/usr/bin/env python3
"""
Video-to-Text: A Cross-Platform GUI Tool for Video Transcription.

This application provides a graphical interface for converting video files to text transcripts
using advanced speech recognition technology. It's built with Python and tkinter, offering
an intuitive interface for users who need to transcribe audio content from video files.
The application supports multiple video formats and provides real-time progress tracking
with comprehensive error handling.

Features:
- Graphical User Interface (GUI): Built with `tkinter` for cross-platform compatibility.
- Video File Processing: Support for MP4, AVI, MOV, MKV, WMV, and other popular formats.
- Speech Recognition: Uses Google Speech Recognition API for accurate transcription.
- Multiple Output Formats: Save transcripts as plain text (.txt) or structured JSON.
- Progress Tracking: Real-time progress updates with detailed status information.
- Cross-Platform Support: Works on Windows, macOS, and Linux systems.
- Error Handling: Comprehensive error handling with user-friendly messages.
- Settings Management: Persistent configuration with customizable preferences.
- Memory Optimization: Efficient processing of large video files with automatic cleanup.

Usage:
To run the application, ensure you have Python 3.8+ installed with required dependencies.
Then, execute the script:
    python main.py

Dependencies:
- Python 3.8+: The core programming language.
- tkinter: Standard Python GUI library (usually included with Python installation).
- moviepy: For video processing and audio extraction.
- SpeechRecognition: For speech-to-text conversion using Google's API.
- pyaudio: For audio processing support.
- pydub: Additional audio format support.

Author: Anoop Kumar
License: MIT
Date: 01/08/2025 (DD/MM/YYYY)
Version: 1.0.0-beta
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for the application."""
    import argparse
    parser = argparse.ArgumentParser(description="Video-to-Text Transcription Tool")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--video", type=str, help="Path to input video file (required for headless)")
    parser.add_argument("--output", type=str, help="Path to output transcript file")
    parser.add_argument("--format", type=str, default="txt", choices=["txt", "json"], help="Output format (default: txt)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Validate headless arguments
    if args.headless and not args.video:
        parser.error("--video is required when using --headless")

    try:
        from app import VideoToTextApp
        
        app = VideoToTextApp(
            headless=args.headless,
            input_file=args.video,
            output_file=args.output,
            output_format=args.format,
            verbose=args.verbose
        )
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except ImportError as e:
        print(f"Error importing dependencies: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()