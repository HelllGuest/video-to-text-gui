"""
Performance monitoring utilities for the Video-to-Text application.

This module provides performance monitoring, memory tracking, and resource
optimization utilities to ensure smooth operation during video processing.
"""

import time
import threading
import psutil
import gc
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    timestamp: datetime
    memory_usage_mb: float
    cpu_percent: float
    thread_count: int
    temp_files_count: int
    gui_update_rate: float
    processing_stage: str


class PerformanceMonitor:
    """
    Monitor system performance and resource usage during video processing.
    
    This class tracks memory usage, CPU utilization, thread count, and other
    performance metrics to help optimize the application's resource usage.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self._metrics_history: List[PerformanceMetrics] = []
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_lock = threading.Lock()
        self._callbacks: List[Callable[[PerformanceMetrics], None]] = []
        
        # Configuration
        self._sample_interval = 1.0  # Sample every second
        self._max_history_size = 300  # Keep 5 minutes of history
        self._memory_warning_threshold_mb = 1000
        self._cpu_warning_threshold = 80.0
        
        # Current state tracking
        self._current_stage = "idle"
        self._gui_update_count = 0
        self._last_gui_update_time = time.time()
        self._temp_files_count = 0
    
    def start_monitoring(self) -> None:
        """Start performance monitoring in a background thread."""
        with self._monitor_lock:
            if self._monitoring_active:
                return
            
            self._monitoring_active = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        with self._monitor_lock:
            self._monitoring_active = False
            
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2.0)
    
    def set_processing_stage(self, stage: str) -> None:
        """
        Set the current processing stage for monitoring.
        
        Args:
            stage: Current processing stage name
        """
        self._current_stage = stage
    
    def record_gui_update(self) -> None:
        """Record a GUI update for rate calculation."""
        self._gui_update_count += 1
    
    def set_temp_files_count(self, count: int) -> None:
        """
        Set the current temporary files count.
        
        Args:
            count: Number of temporary files
        """
        self._temp_files_count = count
    
    def add_callback(self, callback: Callable[[PerformanceMetrics], None]) -> None:
        """
        Add a callback to be called when new metrics are collected.
        
        Args:
            callback: Function to call with new metrics
        """
        self._callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """
        Get the most recent performance metrics.
        
        Returns:
            Latest PerformanceMetrics or None if no data available
        """
        with self._monitor_lock:
            return self._metrics_history[-1] if self._metrics_history else None
    
    def get_metrics_history(self, minutes: int = 5) -> List[PerformanceMetrics]:
        """
        Get performance metrics history for the specified time period.
        
        Args:
            minutes: Number of minutes of history to return
            
        Returns:
            List of PerformanceMetrics from the specified time period
        """
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        
        with self._monitor_lock:
            return [
                metric for metric in self._metrics_history
                if metric.timestamp.timestamp() > cutoff_time
            ]
    
    def get_performance_summary(self) -> Dict[str, float]:
        """
        Get a summary of performance metrics.
        
        Returns:
            Dictionary containing performance summary statistics
        """
        recent_metrics = self.get_metrics_history(minutes=2)
        
        if not recent_metrics:
            return {}
        
        memory_values = [m.memory_usage_mb for m in recent_metrics]
        cpu_values = [m.cpu_percent for m in recent_metrics]
        
        return {
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'current_temp_files': self._temp_files_count,
            'sample_count': len(recent_metrics)
        }
    
    def check_resource_warnings(self) -> List[str]:
        """
        Check for resource usage warnings.
        
        Returns:
            List of warning messages
        """
        warnings = []
        current_metrics = self.get_current_metrics()
        
        if current_metrics:
            if current_metrics.memory_usage_mb > self._memory_warning_threshold_mb:
                warnings.append(
                    f"High memory usage: {current_metrics.memory_usage_mb:.1f} MB"
                )
            
            if current_metrics.cpu_percent > self._cpu_warning_threshold:
                warnings.append(
                    f"High CPU usage: {current_metrics.cpu_percent:.1f}%"
                )
            
            if current_metrics.temp_files_count > 20:
                warnings.append(
                    f"Many temporary files: {current_metrics.temp_files_count}"
                )
        
        return warnings
    
    def optimize_performance(self) -> Dict[str, str]:
        """
        Perform performance optimizations based on current metrics.
        
        Returns:
            Dictionary describing optimizations performed
        """
        optimizations = {}
        current_metrics = self.get_current_metrics()
        
        if current_metrics:
            # Memory optimization
            if current_metrics.memory_usage_mb > self._memory_warning_threshold_mb:
                collected = gc.collect()
                optimizations['memory'] = f"Garbage collection freed {collected} objects"
            
            # Adjust monitoring frequency based on CPU usage
            if current_metrics.cpu_percent > 50:
                self._sample_interval = min(self._sample_interval * 1.2, 3.0)
                optimizations['monitoring'] = "Reduced monitoring frequency to save CPU"
            elif current_metrics.cpu_percent < 20:
                self._sample_interval = max(self._sample_interval * 0.9, 0.5)
                optimizations['monitoring'] = "Increased monitoring frequency"
        
        return optimizations
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        while self._monitoring_active:
            try:
                metrics = self._collect_metrics()
                
                with self._monitor_lock:
                    self._metrics_history.append(metrics)
                    
                    # Limit history size
                    if len(self._metrics_history) > self._max_history_size:
                        self._metrics_history = self._metrics_history[-self._max_history_size:]
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(metrics)
                    except Exception:
                        pass  # Ignore callback errors
                
                time.sleep(self._sample_interval)
                
            except Exception:
                # Continue monitoring even if individual samples fail
                time.sleep(self._sample_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """
        Collect current performance metrics.
        
        Returns:
            PerformanceMetrics with current system state
        """
        try:
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            
            # Thread count
            thread_count = process.num_threads()
            
            # GUI update rate calculation
            current_time = time.time()
            time_diff = current_time - self._last_gui_update_time
            gui_update_rate = self._gui_update_count / max(time_diff, 1.0)
            
            # Reset GUI update tracking
            self._gui_update_count = 0
            self._last_gui_update_time = current_time
            
        except Exception:
            # Fallback values if monitoring fails
            memory_mb = 0.0
            cpu_percent = 0.0
            thread_count = 0
            gui_update_rate = 0.0
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent,
            thread_count=thread_count,
            temp_files_count=self._temp_files_count,
            gui_update_rate=gui_update_rate,
            processing_stage=self._current_stage
        )


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.
    
    Returns:
        Global PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def start_performance_monitoring() -> None:
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring()


def stop_performance_monitoring() -> None:
    """Stop global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()


class PerformanceOptimizer:
    """
    Utility class for applying performance optimizations.
    
    This class provides methods to optimize various aspects of the application
    based on current performance metrics and system state.
    """
    
    @staticmethod
    def optimize_memory_usage() -> Dict[str, str]:
        """
        Optimize memory usage by performing garbage collection and cleanup.
        
        Returns:
            Dictionary describing optimizations performed
        """
        optimizations = {}
        
        # Force garbage collection
        collected = gc.collect()
        optimizations['garbage_collection'] = f"Freed {collected} objects"
        
        # Get memory info before and after
        try:
            process = psutil.Process()
            memory_after = process.memory_info().rss / (1024 * 1024)
            optimizations['memory_after_mb'] = f"{memory_after:.1f}"
        except Exception:
            pass
        
        return optimizations
    
    @staticmethod
    def optimize_gui_responsiveness(progress_panel) -> Dict[str, str]:
        """
        Optimize GUI responsiveness by adjusting update frequencies.
        
        Args:
            progress_panel: ProgressPanel instance to optimize
            
        Returns:
            Dictionary describing optimizations performed
        """
        optimizations = {}
        
        try:
            # Get performance stats from progress panel
            stats = progress_panel.get_performance_stats()
            
            # Optimize if too many pending updates
            if stats['pending_updates'] > 10:
                progress_panel.optimize_performance()
                optimizations['gui_updates'] = "Optimized pending GUI updates"
            
            # Adjust update throttling based on performance
            if stats['dropped_updates'] > 50:
                optimizations['throttling'] = "Increased update throttling to improve performance"
            
        except Exception as e:
            optimizations['error'] = f"GUI optimization failed: {str(e)}"
        
        return optimizations
    
    @staticmethod
    def optimize_file_management(file_manager) -> Dict[str, str]:
        """
        Optimize file management by cleaning up temporary files.
        
        Args:
            file_manager: FileManager instance to optimize
            
        Returns:
            Dictionary describing optimizations performed
        """
        optimizations = {}
        
        try:
            # Get current temp file stats
            stats_before = file_manager.get_temp_file_stats()
            
            # Perform optimization
            file_manager.optimize_temp_file_management()
            file_manager.cleanup_temp_files()
            
            # Get stats after optimization
            stats_after = file_manager.get_temp_file_stats()
            
            files_cleaned = stats_before['tracked_files'] - stats_after['tracked_files']
            size_freed = stats_before['total_size_mb'] - stats_after['total_size_mb']
            
            optimizations['temp_files'] = f"Cleaned {files_cleaned} files, freed {size_freed:.1f} MB"
            
        except Exception as e:
            optimizations['error'] = f"File management optimization failed: {str(e)}"
        
        return optimizations