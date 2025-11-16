"""
Transcription controller with threading support.

This module contains the TranscriptionController class that coordinates
transcription operations between the GUI and service layers, providing
input validation, background thread management, and progress callbacks.
"""

import threading
import time
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any

from ..core.interfaces import ITranscriptionController, ITranscriptionService, IFileManager
from ..core.models import TranscriptionRequest, TranscriptionResult, ProgressUpdate, ApplicationSettings
from ..utils.error_handler import get_error_handler, ErrorCategory
from ..utils.validation import validate_transcription_request
from ..utils.performance_monitor import get_performance_monitor, PerformanceOptimizer


class TranscriptionController(ITranscriptionController):
    """
    Controller for coordinating transcription operations with threading support.
    
    This class manages the coordination between GUI components and the transcription
    service, providing input validation, background thread management, progress
    callbacks, and proper error handling.
    """
    
    def __init__(
        self,
        transcription_service: ITranscriptionService,
        file_manager: IFileManager,
        settings: Optional[ApplicationSettings] = None,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
        completion_callback: Optional[Callable[[TranscriptionResult], None]] = None
    ):
        """
        Initialize the transcription controller.
        
        Args:
            transcription_service: Service for performing transcription operations
            file_manager: Manager for file operations and validation
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback for completion notifications
        """
        self.transcription_service = transcription_service
        self.file_manager = file_manager
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        
        # Threading state
        self._current_thread: Optional[threading.Thread] = None
        self._current_request: Optional[TranscriptionRequest] = None
        self._is_running = False
        self._thread_lock = threading.Lock()
        
        # Set up logging and error handling
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._logger = logging.getLogger(__name__)
        self.error_handler = get_error_handler()
        
        # Performance monitoring
        self.performance_monitor = get_performance_monitor()
        self.performance_optimizer = PerformanceOptimizer()
    
    def start_transcription(self, request: TranscriptionRequest) -> None:
        """
        Start a transcription operation with input validation.
        
        Args:
            request: TranscriptionRequest containing operation parameters
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If transcription is already running
        """
        with self._thread_lock:
            # Check if already running
            if self._is_running:
                error_msg = "Transcription operation is already running"
                self.error_handler.handle_error(
                    RuntimeError(error_msg),
                    category=ErrorCategory.THREADING,
                    user_message=error_msg,
                    show_dialog=True
                )
                raise RuntimeError(error_msg)
            
            # Validate inputs
            try:
                self._validate_transcription_request(request)
            except ValueError as e:
                self.error_handler.handle_error(
                    e,
                    category=ErrorCategory.VALIDATION,
                    context={"request": request.to_dict()},
                    show_dialog=True
                )
                raise
            
            # Correct output file extension if needed
            corrected_path = self.file_manager.ensure_extension(
                request.output_path, request.output_format
            )
            request.output_path = corrected_path
            
            # Set running state
            self._is_running = True
            self._current_request = request
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            self.performance_monitor.set_processing_stage("transcription_starting")
            
            # Start transcription in background thread
            self._current_thread = threading.Thread(
                target=self._transcription_thread_target,
                args=(request,),
                daemon=True
            )
            self._current_thread.start()
            
            self._logger.info(f"Started transcription for: {request.video_path}")
    
    def cancel_transcription(self) -> None:
        """Cancel the current transcription operation."""
        with self._thread_lock:
            if not self._is_running:
                self._logger.warning("No transcription operation to cancel")
                return
            
            self._logger.info("Cancelling transcription operation")
            
            # Cancel the transcription service
            self.transcription_service.cancel_transcription()
            
            # Wait for thread to finish (with timeout)
            if self._current_thread and self._current_thread.is_alive():
                self._current_thread.join(timeout=5.0)
                
                if self._current_thread.is_alive():
                    self._logger.warning("Thread did not terminate within timeout")
            
            # Reset state
            self._reset_state()
    
    def is_transcription_running(self) -> bool:
        """
        Check if a transcription operation is currently running.
        
        Returns:
            True if transcription is in progress, False otherwise
        """
        with self._thread_lock:
            return self._is_running and (
                self._current_thread is not None and 
                self._current_thread.is_alive()
            )
    
    def get_current_request(self) -> Optional[TranscriptionRequest]:
        """
        Get the current transcription request if one is running.
        
        Returns:
            Current TranscriptionRequest or None if not running
        """
        with self._thread_lock:
            return self._current_request if self._is_running else None
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for the current transcription to complete.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if transcription completed within timeout, False otherwise
        """
        with self._thread_lock:
            thread = self._current_thread
        
        if thread is None:
            return True  # No operation running
        
        thread.join(timeout=timeout)
        return not thread.is_alive()
    
    def set_progress_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """
        Set the progress callback function.
        
        Args:
            callback: Function to call with progress updates
        """
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[TranscriptionResult], None]) -> None:
        """
        Set the completion callback function.
        
        Args:
            callback: Function to call when transcription completes
        """
        self.completion_callback = callback
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        Get detailed status information about the controller.
        
        Returns:
            Dictionary containing status information
        """
        with self._thread_lock:
            status = {
                "is_running": self._is_running,
                "thread_alive": (
                    self._current_thread is not None and 
                    self._current_thread.is_alive()
                ) if self._current_thread else False,
                "current_request": None
            }
            
            if self._current_request:
                status["current_request"] = {
                    "video_path": self._current_request.video_path,
                    "output_path": self._current_request.output_path,
                    "output_format": self._current_request.output_format,
                    "verbose": self._current_request.verbose,
                    "timestamp": self._current_request.timestamp.isoformat()
                }
            
            return status
    
    def _validate_transcription_request(self, request: TranscriptionRequest) -> None:
        """
        Validate a transcription request.
        
        Args:
            request: TranscriptionRequest to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Use comprehensive validation
        is_valid, errors = validate_transcription_request(
            request.video_path,
            request.output_path,
            request.output_format,
            request.verbose
        )
        
        if not is_valid:
            error_message = "Validation failed:\n" + "\n".join(errors)
            self._logger.error(f"Request validation failed: {errors}")
            raise ValueError(error_message)
        
        self._logger.info("Input validation passed")
    
    def _transcription_thread_target(self, request: TranscriptionRequest) -> None:
        """
        Target function for the transcription thread with performance optimization.
        
        Args:
            request: TranscriptionRequest to process
        """
        try:
            self._logger.info("Starting transcription thread")
            self.performance_monitor.set_processing_stage("transcription_active")
            
            # Create progress callback wrapper with performance monitoring
            def progress_wrapper(update: ProgressUpdate) -> None:
                # Update performance monitor stage based on progress
                if update.percentage < 30:
                    self.performance_monitor.set_processing_stage("video_loading")
                elif update.percentage < 70:
                    self.performance_monitor.set_processing_stage("audio_processing")
                elif update.percentage < 95:
                    self.performance_monitor.set_processing_stage("speech_recognition")
                else:
                    self.performance_monitor.set_processing_stage("finalizing")
                
                if self.progress_callback:
                    try:
                        self.progress_callback(update)
                        self.performance_monitor.record_gui_update()
                    except Exception as e:
                        self._logger.error(f"Error in progress callback: {e}")
                
                # Log verbose messages if enabled
                if request.verbose:
                    self._logger.info(f"Progress: {update.percentage:.1f}% - {update.message}")
                
                # Perform periodic optimizations during processing
                if update.percentage in [25, 50, 75]:
                    self._perform_periodic_optimization()
            
            # Perform transcription
            result = self.transcription_service.transcribe_video(
                request.video_path, 
                progress_wrapper
            )
            
            # Save transcript if transcription was successful
            if result.success:
                save_success = self.file_manager.save_transcript(
                    result.transcript,
                    request.output_path,
                    request.output_format
                )
                
                if save_success:
                    result.output_file_path = request.output_path
                    self._logger.info(f"Transcript saved to: {request.output_path}")
                else:
                    # Update result to reflect save failure
                    error_msg = f"Transcription completed but failed to save to: {request.output_path}"
                    self.error_handler.handle_file_error(
                        "save transcript",
                        request.output_path,
                        Exception("Save operation failed"),
                        show_dialog=True
                    )
                    result = TranscriptionResult(
                        success=False,
                        transcript=result.transcript,
                        error_message=error_msg,
                        processing_time=result.processing_time,
                        output_file_path=None
                    )
            
            # Call completion callback
            if self.completion_callback:
                try:
                    self.completion_callback(result)
                except Exception as e:
                    self._logger.error(f"Error in completion callback: {e}")
            
            self._logger.info(f"Transcription thread completed. Success: {result.success}")
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                category=ErrorCategory.THREADING,
                user_message=f"Transcription operation failed: {str(e)}",
                show_dialog=True
            )
            
            # Create error result
            error_result = TranscriptionResult(
                success=False,
                transcript="",
                error_message=str(e),
                processing_time=0.0,
                output_file_path=None
            )
            
            # Call completion callback with error
            if self.completion_callback:
                try:
                    self.completion_callback(error_result)
                except Exception as callback_error:
                    self._logger.error(f"Error in completion callback: {callback_error}")
        
        finally:
            # Perform final optimization
            self._perform_final_optimization()
            
            # Clean up temporary files
            try:
                self.file_manager.cleanup_temp_files()
            except Exception as e:
                self._logger.warning(f"Error during cleanup: {e}")
            
            # Update performance monitor
            self.performance_monitor.set_processing_stage("idle")
            
            # Reset state
            with self._thread_lock:
                self._reset_state()
    
    def _reset_state(self) -> None:
        """Reset the controller state after operation completion."""
        self._is_running = False
        self._current_request = None
        self._current_thread = None
        self._logger.info("Controller state reset")
    
    def _perform_periodic_optimization(self) -> None:
        """Perform periodic optimizations during transcription."""
        try:
            # Check for resource warnings
            warnings = self.performance_monitor.check_resource_warnings()
            if warnings:
                self._logger.info(f"Performance warnings: {warnings}")
            
            # Perform optimizations if needed
            optimizations = self.performance_monitor.optimize_performance()
            if optimizations:
                self._logger.info(f"Applied optimizations: {optimizations}")
            
            # Optimize file management
            file_optimizations = self.performance_optimizer.optimize_file_management(self.file_manager)
            if file_optimizations:
                self._logger.info(f"File optimizations: {file_optimizations}")
                
        except Exception as e:
            self._logger.warning(f"Error during periodic optimization: {e}")
    
    def _perform_final_optimization(self) -> None:
        """Perform final cleanup and optimization after transcription."""
        try:
            # Final memory optimization
            memory_optimizations = self.performance_optimizer.optimize_memory_usage()
            if memory_optimizations:
                self._logger.info(f"Final memory optimizations: {memory_optimizations}")
            
            # Get final performance summary
            summary = self.performance_monitor.get_performance_summary()
            if summary:
                self._logger.info(f"Performance summary: {summary}")
                
        except Exception as e:
            self._logger.warning(f"Error during final optimization: {e}")