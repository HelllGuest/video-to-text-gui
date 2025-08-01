"""
Transcription service implementation with threading support.

This module contains the TranscriptionService class that handles video-to-text
transcription operations with progress reporting and cancellation support.
"""

import os
import time
import threading
import logging
import gc
import psutil
import tempfile
from datetime import datetime
from typing import Callable, Optional
import moviepy as mp
import speech_recognition as sr

from ..core.interfaces import ITranscriptionService
from ..core.models import TranscriptionResult, ProgressUpdate
from ..utils.error_handler import get_error_handler, ErrorCategory


class TranscriptionService(ITranscriptionService):
    """
    Service for transcribing video files to text with threading support.
    
    This class extracts and refactors the core transcription logic from the CLI
    script, adding progress callbacks, thread safety, and cancellation support.
    """
    
    def __init__(self):
        """Initialize the transcription service."""
        self._cancel_event = threading.Event()
        self._current_thread: Optional[threading.Thread] = None
        self._temp_audio_file = None  # Will be created dynamically
        
        # Performance optimization settings
        self._memory_threshold_mb = 500
        self._progress_update_interval = 0.1
        self._last_progress_update = 0
        self._chunk_size_mb = 50
        
        # Set up logging and error handling
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._logger = logging.getLogger(__name__)
        self.error_handler = get_error_handler()
    
    def _create_temp_audio_file(self) -> str:
        """
        Create a unique temporary audio file.
        
        Returns:
            Path to the created temporary audio file
        """
        if self._temp_audio_file is None:
            fd, self._temp_audio_file = tempfile.mkstemp(
                suffix='.wav', 
                prefix='vid2text_audio_',
                dir=tempfile.gettempdir()
            )
            os.close(fd)
            self._logger.info(f"Created temporary audio file: {self._temp_audio_file}")
        
        return self._temp_audio_file
    
    def transcribe_video(self, video_path: str, progress_callback: Callable[[ProgressUpdate], None]) -> TranscriptionResult:
        """
        Transcribe a video file to text with progress reporting.
        
        Args:
            video_path: Path to the video file to transcribe
            progress_callback: Function to call with progress updates
            
        Returns:
            TranscriptionResult containing the transcription outcome
        """
        start_time = time.time()
        
        try:
            # Reset cancellation event
            self._cancel_event.clear()
            
            # Validate video file existence
            if not self._validate_file_existence(video_path):
                error_msg = f"Video file not found: {video_path}"
                self.error_handler.handle_file_error(
                    "access video file",
                    video_path,
                    FileNotFoundError(error_msg),
                    show_dialog=True
                )
                return TranscriptionResult(
                    success=False,
                    transcript="",
                    error_message=error_msg,
                    processing_time=time.time() - start_time,
                    output_file_path=None
                )
            
            # Step 1: Load video with memory optimization (10% progress)
            self._report_progress_throttled(progress_callback, 10.0, "Loading video", "Loading video file...")
            if self._cancel_event.is_set():
                return self._create_cancelled_result(start_time)
            
            try:
                file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                self._logger.info(f"Video file size: {file_size_mb:.1f} MB")
                
                if file_size_mb > self._chunk_size_mb:
                    video = mp.VideoFileClip(video_path, audio_buffersize=200000, audio_fps=22050)
                    self._logger.info("Using memory-optimized loading for large video file")
                else:
                    video = mp.VideoFileClip(video_path)
                
                self._logger.info("Video loaded successfully")
                self._monitor_memory_usage("After video loading")
            except Exception as e:
                self.error_handler.handle_video_processing_error(e, video_path, show_dialog=True)
                return TranscriptionResult(
                    success=False,
                    transcript="",
                    error_message=f"Failed to load video: {str(e)}",
                    processing_time=time.time() - start_time,
                    output_file_path=None
                )
            
            # Step 2: Extract audio with memory optimization (30% progress)
            self._report_progress_throttled(progress_callback, 30.0, "Extracting audio", "Extracting audio from video...")
            if self._cancel_event.is_set():
                self._cleanup_video_resources(video)
                return self._create_cancelled_result(start_time)
            
            try:
                audio = video.audio
                if audio is None:
                    raise ValueError("Video file contains no audio track")
                
                if hasattr(audio, 'fps') and audio.fps > 22050:
                    audio = audio.with_fps(22050)
                    self._logger.info("Audio sample rate optimized for memory efficiency")
                
                self._logger.info("Audio extracted successfully")
                self._monitor_memory_usage("After audio extraction")
            except Exception as e:
                self._cleanup_video_resources(video)
                self.error_handler.handle_video_processing_error(e, video_path, show_dialog=True)
                return TranscriptionResult(
                    success=False,
                    transcript="",
                    error_message=f"Failed to extract audio: {str(e)}",
                    processing_time=time.time() - start_time,
                    output_file_path=None
                )
            
            # Step 3: Write audio to temp file with progress tracking (50% progress)
            self._report_progress_throttled(progress_callback, 50.0, "Creating audio file", "Writing audio to temporary file...")
            if self._cancel_event.is_set():
                self._cleanup_video_resources(video, audio)
                return self._create_cancelled_result(start_time)
            
            try:
                temp_audio_path = self._create_temp_audio_file()
                
                def audio_progress_callback(t):
                    if self._cancel_event.is_set():
                        return False
                    
                    if hasattr(audio, 'duration') and audio.duration > 0:
                        progress = 50.0 + (t / audio.duration) * 20.0
                        self._report_progress_throttled(progress_callback, progress, "Creating audio file", 
                                                     f"Writing audio... {t:.1f}s/{audio.duration:.1f}s")
                    return True
                
                audio.write_audiofile(
                    temp_audio_path, 
                    logger=None,
                    codec='pcm_s16le',
                    ffmpeg_params=['-ac', '1']
                )
                self._logger.info("Audio written to temp file successfully")
                self._monitor_memory_usage("After audio file creation")
            except Exception as e:
                self._cleanup_video_resources(video, audio)
                self.error_handler.handle_video_processing_error(e, video_path, show_dialog=True)
                return TranscriptionResult(
                    success=False,
                    transcript="",
                    error_message=f"Failed to write audio file: {str(e)}",
                    processing_time=time.time() - start_time,
                    output_file_path=None
                )
            
            self._cleanup_video_resources(video, audio)
            self._force_garbage_collection()
            
            # Step 4: Transcribe audio with progress tracking (80% progress)
            self._report_progress_throttled(progress_callback, 80.0, "Transcribing audio", "Performing speech recognition...")
            if self._cancel_event.is_set():
                self._cleanup_temp_files()
                return self._create_cancelled_result(start_time)
            
            try:
                transcript = self._transcribe_audio_file_optimized(progress_callback)
            except Exception as e:
                self._cleanup_temp_files()
                self.error_handler.handle_speech_recognition_error(e, show_dialog=True)
                return TranscriptionResult(
                    success=False,
                    transcript="",
                    error_message=f"Speech recognition failed: {str(e)}",
                    processing_time=time.time() - start_time,
                    output_file_path=None
                )
            
            # Step 5: Complete (100% progress)
            self._report_progress_throttled(progress_callback, 100.0, "Complete", "Transcription completed successfully")
            
            self._cleanup_temp_files()
            
            processing_time = time.time() - start_time
            self._logger.info(f"Transcription completed in {processing_time:.2f} seconds")
            
            return TranscriptionResult(
                success=True,
                transcript=transcript,
                error_message=None,
                processing_time=processing_time,
                output_file_path=None  # Will be set by file manager when saving
            )
            
        except Exception as e:
            self._cleanup_temp_files()
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.VIDEO_PROCESSING,
                user_message=f"Transcription failed: {str(e)}",
                show_dialog=True
            )
            
            return TranscriptionResult(
                success=False,
                transcript="",
                error_message=f"Transcription failed: {str(e)}",
                processing_time=time.time() - start_time,
                output_file_path=None
            )
    
    def cancel_transcription(self) -> None:
        """Cancel the current transcription operation if running."""
        self._logger.info("Cancellation requested")
        self._cancel_event.set()
        
        # If there's a current thread, wait for it to finish
        if self._current_thread and self._current_thread.is_alive():
            self._current_thread.join(timeout=5.0)  # Wait up to 5 seconds
    
    def transcribe_video_threaded(self, video_path: str, progress_callback: Callable[[ProgressUpdate], None]) -> threading.Thread:
        """
        Start transcription in a separate thread.
        
        Args:
            video_path: Path to the video file to transcribe
            progress_callback: Function to call with progress updates
            
        Returns:
            Thread object for the transcription operation
        """
        def thread_target():
            try:
                result = self.transcribe_video(video_path, progress_callback)
                # Notify completion through progress callback
                completion_update = ProgressUpdate(
                    percentage=100.0,
                    current_step="Complete" if result.success else "Failed",
                    message="Transcription completed" if result.success else f"Transcription failed: {result.error_message}",
                    timestamp=datetime.now()
                )
                progress_callback(completion_update)
            except Exception as e:
                self._logger.error(f"Thread execution failed: {str(e)}")
                error_update = ProgressUpdate(
                    percentage=0.0,
                    current_step="Error",
                    message=f"Thread execution failed: {str(e)}",
                    timestamp=datetime.now()
                )
                progress_callback(error_update)
        
        self._current_thread = threading.Thread(target=thread_target, daemon=True)
        self._current_thread.start()
        return self._current_thread
    
    def _validate_file_existence(self, file_path: str) -> bool:
        """
        Validate that a file exists.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file exists, False otherwise
        """
        if not os.path.isfile(file_path):
            self._logger.error(f"File not found: {file_path}")
            return False
        return True
    
    def _transcribe_audio_file(self) -> str:
        """
        Transcribe the temporary audio file using speech recognition.
        
        Returns:
            Transcribed text
            
        Raises:
            Exception: If speech recognition fails
        """
        recognizer = sr.Recognizer()
        
        try:
            if not self._temp_audio_file or not os.path.exists(self._temp_audio_file):
                raise Exception("Temporary audio file not found")
                
            with sr.AudioFile(self._temp_audio_file) as source:
                # Check for cancellation before processing
                if self._cancel_event.is_set():
                    raise Exception("Transcription was cancelled")
                
                # Read the entire audio file instead of just listening for a phrase
                audio_data = recognizer.record(source)
                
                # Check for cancellation before recognition
                if self._cancel_event.is_set():
                    raise Exception("Transcription was cancelled")
                
                text = recognizer.recognize_google(audio_data)
                self._logger.info("Speech recognition completed successfully")
                return text
                
        except sr.UnknownValueError as e:
            error_msg = "Google Speech Recognition could not understand the audio"
            self._logger.error(error_msg)
            self.error_handler.handle_speech_recognition_error(
                Exception(error_msg),
                show_dialog=False
            )
            raise Exception(error_msg)
            
        except sr.RequestError as e:
            error_msg = f"Could not request results from Google Speech Recognition service: {e}"
            self._logger.error(error_msg)
            self.error_handler.handle_speech_recognition_error(e, show_dialog=False)
            raise Exception(error_msg)
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files created during processing."""
        try:
            if self._temp_audio_file and os.path.exists(self._temp_audio_file):
                os.remove(self._temp_audio_file)
                self._logger.info(f"Temporary audio file cleaned up: {self._temp_audio_file}")
                self._temp_audio_file = None  # Reset for next use
        except Exception as e:
            self._logger.warning(f"Failed to clean up temporary file: {str(e)}")
    
    def _report_progress(self, callback: Callable[[ProgressUpdate], None], percentage: float, step: str, message: str) -> None:
        """
        Report progress to the callback function.
        
        Args:
            callback: Progress callback function
            percentage: Completion percentage
            step: Current processing step
            message: Progress message
        """
        update = ProgressUpdate(
            percentage=percentage,
            current_step=step,
            message=message,
            timestamp=datetime.now()
        )
        callback(update)
    
    def _create_cancelled_result(self, start_time: float) -> TranscriptionResult:
        """
        Create a result object for cancelled transcription.
        
        Args:
            start_time: When the transcription started
            
        Returns:
            TranscriptionResult indicating cancellation
        """
        return TranscriptionResult(
            success=False,
            transcript="",
            error_message="Transcription was cancelled by user",
            processing_time=time.time() - start_time,
            output_file_path=None
        )
    
    def _report_progress_throttled(self, callback: Callable[[ProgressUpdate], None], 
                                 percentage: float, step: str, message: str) -> None:
        """
        Report progress with throttling to prevent excessive GUI updates.
        
        Args:
            callback: Progress callback function
            percentage: Completion percentage
            step: Current processing step
            message: Progress message
        """
        current_time = time.time()
        
        # Only update if enough time has passed or if it's a significant milestone
        if (current_time - self._last_progress_update >= self._progress_update_interval or 
            percentage in [0.0, 10.0, 30.0, 50.0, 80.0, 100.0]):
            
            self._report_progress(callback, percentage, step, message)
            self._last_progress_update = current_time
    
    def _monitor_memory_usage(self, context: str) -> None:
        """
        Monitor and log memory usage for optimization.
        
        Args:
            context: Context description for logging
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            self._logger.info(f"Memory usage {context}: {memory_mb:.1f} MB")
            
            # Trigger garbage collection if memory usage is high
            if memory_mb > self._memory_threshold_mb:
                self._logger.info("High memory usage detected, triggering garbage collection")
                self._force_garbage_collection()
                
        except Exception as e:
            self._logger.warning(f"Could not monitor memory usage: {e}")
    
    def _force_garbage_collection(self) -> None:
        """Force garbage collection to free memory."""
        try:
            collected = gc.collect()
            self._logger.info(f"Garbage collection freed {collected} objects")
        except Exception as e:
            self._logger.warning(f"Garbage collection failed: {e}")
    
    def _cleanup_video_resources(self, video: Optional[mp.VideoFileClip] = None, 
                               audio: Optional[mp.AudioClip] = None) -> None:
        """
        Clean up video and audio resources properly.
        
        Args:
            video: Video clip to clean up
            audio: Audio clip to clean up
        """
        try:
            if audio is not None:
                audio.close()
                self._logger.debug("Audio resources cleaned up")
        except Exception as e:
            self._logger.warning(f"Error cleaning up audio resources: {e}")
        
        try:
            if video is not None:
                video.close()
                self._logger.debug("Video resources cleaned up")
        except Exception as e:
            self._logger.warning(f"Error cleaning up video resources: {e}")
    
    def _transcribe_audio_file_optimized(self, progress_callback: Callable[[ProgressUpdate], None]) -> str:
        """
        Transcribe the temporary audio file using speech recognition with progress updates.
        
        Args:
            progress_callback: Callback for progress updates
            
        Returns:
            Transcribed text
            
        Raises:
            Exception: If speech recognition fails
        """
        recognizer = sr.Recognizer()
        
        # Optimize recognizer settings for better performance
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.3
        
        try:
            # Update progress for audio file loading
            self._report_progress_throttled(progress_callback, 82.0, "Transcribing audio", 
                                          "Loading audio file for recognition...")
            
            if not self._temp_audio_file or not os.path.exists(self._temp_audio_file):
                raise Exception("Temporary audio file not found")
                
            with sr.AudioFile(self._temp_audio_file) as source:
                # Check for cancellation before processing
                if self._cancel_event.is_set():
                    raise Exception("Transcription was cancelled")
                
                # Update progress for audio processing
                self._report_progress_throttled(progress_callback, 85.0, "Transcribing audio", 
                                              "Processing audio data...")
                
                # Adjust for ambient noise to improve recognition
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Update progress for listening
                self._report_progress_throttled(progress_callback, 90.0, "Transcribing audio", 
                                              "Analyzing speech patterns...")
                
                # Process audio in chunks to handle longer files
                transcript_parts = []
                chunk_duration = 30  # Process 30-second chunks
                
                # Get total duration
                source_duration = source.DURATION
                if source_duration is None:
                    # Fallback: read entire file if duration unknown
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    self._logger.info("Speech recognition completed successfully")
                    return text
                
                # Process in chunks
                num_chunks = int(source_duration / chunk_duration) + 1
                
                for i in range(num_chunks):
                    if self._cancel_event.is_set():
                        raise Exception("Transcription was cancelled")
                    
                    # Calculate chunk boundaries
                    start_time = i * chunk_duration
                    end_time = min((i + 1) * chunk_duration, source_duration)
                    
                    if start_time >= source_duration:
                        break
                    
                    # Update progress
                    chunk_progress = 95.0 + (i / num_chunks) * 5.0
                    self._report_progress_throttled(progress_callback, chunk_progress, "Transcribing audio", 
                                                  f"Processing chunk {i+1}/{num_chunks}...")
                    
                    # Record chunk
                    audio_data = recognizer.record(source, duration=end_time - start_time, offset=start_time)
                    
                    try:
                        chunk_text = recognizer.recognize_google(audio_data)
                        if chunk_text.strip():
                            transcript_parts.append(chunk_text.strip())
                    except sr.UnknownValueError:
                        # Skip chunks that couldn't be understood
                        self._logger.warning(f"Could not understand audio in chunk {i+1}")
                        continue
                
                # Combine all transcript parts
                full_transcript = " ".join(transcript_parts)
                self._logger.info(f"Speech recognition completed successfully - processed {len(transcript_parts)} chunks")
                return full_transcript
                
        except sr.UnknownValueError as e:
            error_msg = "Google Speech Recognition could not understand the audio"
            self._logger.error(error_msg)
            self.error_handler.handle_speech_recognition_error(
                Exception(error_msg),
                show_dialog=False
            )
            raise Exception(error_msg)
            
        except sr.RequestError as e:
            error_msg = f"Could not request results from Google Speech Recognition service: {e}"
            self._logger.error(error_msg)
            self.error_handler.handle_speech_recognition_error(e, show_dialog=False)
            raise Exception(error_msg)