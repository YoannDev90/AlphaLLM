"""
Resource Monitoring Module using Python Standard Library

Monitors CPU, RAM, and provides hooks for disk/network monitoring with proper limitations.
Uses only Python standard library modules (resource, time, os, threading, csv, datetime).
No external dependencies like psutil or /proc file access required for core functionality.

Limitations:
- Memory: Uses resource.getrusage() for maximum memory used by process
- CPU: Uses time.process_time() for CPU time, not wall-clock time
- Disk: Standard library has no reliable way to get disk I/O without /proc
- Network: Standard library has no reliable way to get network usage
"""

import resource
import time
import os
import threading
import csv
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    """Represents a single resource monitoring snapshot."""
    timestamp: datetime
    process_id: int
    cpu_time: float  # in seconds (total via time.process_time())
    max_memory: float  # in MB
    
    # CPU metrics
    cpu_user_time: Optional[float] = None  # User mode CPU time (seconds)
    cpu_sys_time: Optional[float] = None  # System mode CPU time (seconds)
    cpu_percent: Optional[float] = None  # CPU usage percentage (0-100*num_cpus)
    
    # Memory metrics
    avg_memory: Optional[float] = None  # Not easily obtainable from resource module
    memory_percent: Optional[float] = None  # Not easily obtainable from resource module
    page_faults_minor: Optional[int] = None  # Soft page faults
    page_faults_major: Optional[int] = None  # Hard page faults (disk access)
    
    # I/O metrics
    io_reads: Optional[int] = None  # Block reads
    io_writes: Optional[int] = None  # Block writes
    
    # Context switching metrics
    context_switches_vol: Optional[int] = None  # Voluntary context switches
    context_switches_invol: Optional[int] = None  # Involuntary context switches
    
    # Memory pressure metrics
    swaps: Optional[int] = None  # Number of times swapped
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'process_id': self.process_id,
            'cpu_time_sec': self.cpu_time,
            'cpu_user_time_sec': self.cpu_user_time,
            'cpu_sys_time_sec': self.cpu_sys_time,
            'cpu_percent': self.cpu_percent,
            'max_memory_mb': self.max_memory,
            'avg_memory_mb': self.avg_memory,
            'memory_percent': self.memory_percent,
            'page_faults_minor': self.page_faults_minor,
            'page_faults_major': self.page_faults_major,
            'io_reads': self.io_reads,
            'io_writes': self.io_writes,
            'context_switches_vol': self.context_switches_vol,
            'context_switches_invol': self.context_switches_invol,
            'swaps': self.swaps,
        }


class ResourceMonitor:
    """
    Monitor system Resources of the current process using Python standard library.
    
    Attributes:
        interval: Monitoring interval in seconds (default: 5)
        max_samples: Maximum number of samples to keep in memory (default: 1000)
    """
    
    def __init__(self, interval: float = 5.0, max_samples: int = 1000):
        """
        Initialize ResourceMonitor.
        
        Args:
            interval: Monitoring interval in seconds
            max_samples: Maximum number of samples to keep in memory
        """
        self.interval = interval
        self.max_samples = max_samples
        self.process_id = os.getpid()
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.samples: List[ResourceSnapshot] = []
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._start_cpu_time = time.process_time()
        self._previous_snapshot: Optional[ResourceSnapshot] = None
        
        logger.debug(f"ResourceMonitor initialized (PID: {self.process_id}, interval: {interval}s)")
    
    def _collect_resources(self) -> ResourceSnapshot:
        """
        Collect current resource usage.
        
        Returns:
            ResourceSnapshot containing current resource data
        """
        try:
            current_time = time.time()
            
            # Get CPU time using time.process_time() (only CPU time, not wall-clock time)
            cpu_time = time.process_time()
            
            # Get memory usage using resource.getrusage()
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            
            # === CPU Metrics ===
            cpu_user_time = rusage.ru_utime
            cpu_sys_time = rusage.ru_stime
            total_cpu_time = cpu_user_time + cpu_sys_time
            
            # Calculate CPU percentage based on delta from previous snapshot
            cpu_percent = None
            if self._previous_snapshot is not None:
                time_delta = current_time - self._previous_snapshot.timestamp.timestamp()
                previous_total_cpu = (self._previous_snapshot.cpu_user_time or 0) + (self._previous_snapshot.cpu_sys_time or 0)
                cpu_delta = total_cpu_time - previous_total_cpu
                
                if time_delta > 0:
                    cpu_percent = (cpu_delta / time_delta) * 100
                    # Limit to 100% * number of CPUs
                    max_cpu_percent = os.cpu_count() * 100 if os.cpu_count() else 100
                    cpu_percent = min(cpu_percent, max_cpu_percent)
            
            # === Memory Metrics ===
            # Maximum resident set size in kilobytes, convert to MB
            # Note: On many systems, this is not available or not updated in real-time
            max_memory_kb = rusage.ru_maxrss
            
            # Convert to MB (ru_maxrss is in KB on Linux, but in bytes on macOS)
            # This is system-dependent
            if os.uname().sysname == 'Darwin':
                max_memory_mb = max_memory_kb / (1024 * 1024)
            else:
                max_memory_mb = max_memory_kb / 1024
            
            # Page faults
            page_faults_minor = rusage.ru_minflt
            page_faults_major = rusage.ru_majflt
            
            # === I/O Metrics ===
            io_reads = rusage.ru_inblock
            io_writes = rusage.ru_oublock
            
            # === Context Switching Metrics ===
            context_switches_vol = rusage.ru_nvcsw
            context_switches_invol = rusage.ru_nivcsw
            
            # === Memory Pressure Metrics ===
            swaps = rusage.ru_nswap
            
            snapshot = ResourceSnapshot(
                timestamp=datetime.now(),
                process_id=self.process_id,
                cpu_time=cpu_time,
                cpu_user_time=cpu_user_time,
                cpu_sys_time=cpu_sys_time,
                cpu_percent=cpu_percent,
                max_memory=max_memory_mb,
                page_faults_minor=page_faults_minor,
                page_faults_major=page_faults_major,
                io_reads=io_reads,
                io_writes=io_writes,
                context_switches_vol=context_switches_vol,
                context_switches_invol=context_switches_invol,
                swaps=swaps,
            )
            
            # Store for next CPU percentage calculation
            self._previous_snapshot = snapshot
            
            return snapshot
        
        except Exception as e:
            logger.error(f"Error collecting Resources: {e}")
            return None
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        logger.debug("Resource monitoring started")
        
        while self.is_monitoring:
            try:
                snapshot = self._collect_resources()
                
                if snapshot is not None:
                    with self._lock:
                        self.samples.append(snapshot)
                        
                        # Keep only max_samples
                        if len(self.samples) > self.max_samples:
                            self.samples.pop(0)
                
                time.sleep(self.interval)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                if not self.is_monitoring:
                    break
        
        logger.debug("Resource monitoring stopped")
    
    def start(self) -> None:
        """Start background resource monitoring."""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ResourceMonitor"
        )
        self.monitor_thread.start()
        logger.debug("Monitoring thread started")
    
    def stop(self) -> None:
        """Stop background resource monitoring."""
        if not self.is_monitoring:
            logger.warning("Monitoring is not running")
            return
        
        self.is_monitoring = False
        
        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=5.0)

        logger.debug("Monitoring thread stopped")

    def get_latest_snapshot(self) -> Optional[ResourceSnapshot]:
        """Get the latest resource snapshot."""
        with self._lock:
            return self.samples[-1] if self.samples else None
    
    def get_all_snapshots(self) -> List[ResourceSnapshot]:
        """Get all collected snapshots."""
        with self._lock:
            return self.samples.copy()
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Calculate statistics from collected samples.
        
        Returns:
            Dictionary with min, max, average for all metrics
        """
        with self._lock:
            if not self.samples:
                return {}
            
            # Filter out None values for each metric
            cpu_times = [s.cpu_time for s in self.samples]
            cpu_user_times = [s.cpu_user_time for s in self.samples if s.cpu_user_time is not None]
            cpu_sys_times = [s.cpu_sys_time for s in self.samples if s.cpu_sys_time is not None]
            cpu_percents = [s.cpu_percent for s in self.samples if s.cpu_percent is not None]
            memory_values = [s.max_memory for s in self.samples]
            page_faults_minor = [s.page_faults_minor for s in self.samples if s.page_faults_minor is not None]
            page_faults_major = [s.page_faults_major for s in self.samples if s.page_faults_major is not None]
            io_reads = [s.io_reads for s in self.samples if s.io_reads is not None]
            io_writes = [s.io_writes for s in self.samples if s.io_writes is not None]
            context_switches_vol = [s.context_switches_vol for s in self.samples if s.context_switches_vol is not None]
            context_switches_invol = [s.context_switches_invol for s in self.samples if s.context_switches_invol is not None]
            swaps = [s.swaps for s in self.samples if s.swaps is not None]
            
            stats = {
                'samples_count': len(self.samples),
            }
            
            # CPU statistics
            stats['cpu_time_min'] = min(cpu_times)
            stats['cpu_time_max'] = max(cpu_times)
            stats['cpu_time_avg'] = sum(cpu_times) / len(cpu_times)
            
            if cpu_user_times:
                stats['cpu_user_time_min'] = min(cpu_user_times)
                stats['cpu_user_time_max'] = max(cpu_user_times)
                stats['cpu_user_time_avg'] = sum(cpu_user_times) / len(cpu_user_times)
            
            if cpu_sys_times:
                stats['cpu_sys_time_min'] = min(cpu_sys_times)
                stats['cpu_sys_time_max'] = max(cpu_sys_times)
                stats['cpu_sys_time_avg'] = sum(cpu_sys_times) / len(cpu_sys_times)
            
            if cpu_percents:
                stats['cpu_percent_min'] = min(cpu_percents)
                stats['cpu_percent_max'] = max(cpu_percents)
                stats['cpu_percent_avg'] = sum(cpu_percents) / len(cpu_percents)
            
            # Memory statistics
            stats['memory_min'] = min(memory_values)
            stats['memory_max'] = max(memory_values)
            stats['memory_avg'] = sum(memory_values) / len(memory_values)
            
            # Page fault statistics
            if page_faults_minor:
                stats['page_faults_minor_total'] = sum(page_faults_minor)
            
            if page_faults_major:
                stats['page_faults_major_total'] = sum(page_faults_major)
            
            # I/O statistics
            if io_reads:
                stats['io_reads_total'] = sum(io_reads)
            
            if io_writes:
                stats['io_writes_total'] = sum(io_writes)
            
            # Context switch statistics
            if context_switches_vol:
                stats['context_switches_vol_total'] = sum(context_switches_vol)
            
            if context_switches_invol:
                stats['context_switches_invol_total'] = sum(context_switches_invol)
            
            # Swap statistics
            if swaps:
                stats['swaps_total'] = sum(swaps)
            
            return stats
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage without waiting for next monitoring cycle.
        
        Returns:
            Dictionary with current CPU and memory usage
        """
        snapshot = self._collect_resources()
        
        if snapshot is None:
            return {}
        
        return {
            'cpu_time_sec': snapshot.cpu_time,
            'max_memory_mb': snapshot.max_memory,
            'timestamp': snapshot.timestamp.isoformat(),
        }
    
    def export_to_csv(self, filename: str) -> None:
        """
        Export collected samples to CSV file.
        
        Args:
            filename: Output CSV file path
        """
        with self._lock:
            if not self.samples:
                logger.warning("No samples to export")
                return
            
            try:
                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = [
                        'timestamp',
                        'process_id',
                        'cpu_time_sec',
                        'cpu_user_time_sec',
                        'cpu_sys_time_sec',
                        'cpu_percent',
                        'max_memory_mb',
                        'avg_memory_mb',
                        'memory_percent',
                        'page_faults_minor',
                        'page_faults_major',
                        'io_reads',
                        'io_writes',
                        'context_switches_vol',
                        'context_switches_invol',
                        'swaps',
                    ]
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for snapshot in self.samples:
                        writer.writerow(snapshot.to_dict())

                logger.debug(f"Exported {len(self.samples)} samples to {filename}")

            except Exception as e:
                logger.error(f"Error exporting to CSV: {e}")
    
    def print_summary(self) -> None:
        """Print current monitoring summary to console."""
        latest = self.get_latest_snapshot()
        stats = self.get_statistics()
        
        print("\n" + "=" * 80)
        print("RESOURCE MONITORING SUMMARY")
        print("=" * 80)
        
        if latest:
            print(f"\nLatest Snapshot (as of {latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')}):")
            print(f"  PID: {latest.process_id}")
            print(f"\n  CPU Metrics:")
            print(f"    Total CPU Time: {latest.cpu_time:.2f} seconds")
            if latest.cpu_user_time is not None:
                print(f"    User Time: {latest.cpu_user_time:.4f}s")
            if latest.cpu_sys_time is not None:
                print(f"    System Time: {latest.cpu_sys_time:.4f}s")
            if latest.cpu_percent is not None:
                print(f"    CPU Usage: {latest.cpu_percent:.2f}%")
            
            print(f"\n  Memory Metrics:")
            print(f"    Max Memory: {latest.max_memory:.2f} MB")
            if latest.page_faults_minor is not None:
                print(f"    Page Faults (minor): {latest.page_faults_minor}")
            if latest.page_faults_major is not None:
                print(f"    Page Faults (major): {latest.page_faults_major}")
            if latest.swaps is not None:
                print(f"    Swaps: {latest.swaps}")
            
            print(f"\n  I/O Metrics:")
            if latest.io_reads is not None:
                print(f"    Block Reads: {latest.io_reads}")
            if latest.io_writes is not None:
                print(f"    Block Writes: {latest.io_writes}")
            
            print(f"\n  Context Switching:")
            if latest.context_switches_vol is not None:
                print(f"    Voluntary: {latest.context_switches_vol}")
            if latest.context_switches_invol is not None:
                print(f"    Involuntary: {latest.context_switches_invol}")
        
        if stats:
            print(f"\n  Statistics ({stats['samples_count']} samples):")
            
            print(f"\n    CPU Time:")
            print(f"      Min: {stats['cpu_time_min']:.2f}s, "
                  f"Max: {stats['cpu_time_max']:.2f}s, "
                  f"Avg: {stats['cpu_time_avg']:.2f}s")
            
            if 'cpu_percent_avg' in stats:
                print(f"\n    CPU Usage %:")
                print(f"      Min: {stats['cpu_percent_min']:.2f}%, "
                      f"Max: {stats['cpu_percent_max']:.2f}%, "
                      f"Avg: {stats['cpu_percent_avg']:.2f}%")
            
            print(f"\n    Memory:")
            print(f"      Min: {stats['memory_min']:.2f}MB, "
                  f"Max: {stats['memory_max']:.2f}MB, "
                  f"Avg: {stats['memory_avg']:.2f}MB")
            
            if 'page_faults_minor_total' in stats:
                print(f"\n    Page Faults (total):")
                if 'page_faults_minor_total' in stats:
                    print(f"      Minor: {stats['page_faults_minor_total']}")
                if 'page_faults_major_total' in stats:
                    print(f"      Major: {stats['page_faults_major_total']}")
            
            if 'io_reads_total' in stats or 'io_writes_total' in stats:
                print(f"\n    I/O (total):")
                if 'io_reads_total' in stats:
                    print(f"      Block Reads: {stats['io_reads_total']}")
                if 'io_writes_total' in stats:
                    print(f"      Block Writes: {stats['io_writes_total']}")
            
            if 'context_switches_vol_total' in stats or 'context_switches_invol_total' in stats:
                print(f"\n    Context Switches (total):")
                if 'context_switches_vol_total' in stats:
                    print(f"      Voluntary: {stats['context_switches_vol_total']}")
                if 'context_switches_invol_total' in stats:
                    print(f"      Involuntary: {stats['context_switches_invol_total']}")
            
            if 'swaps_total' in stats:
                print(f"\n    Swaps (total): {stats['swaps_total']}")
        
        print("\nLimitations:")
        print("  ✓ CPU Time: time.process_time() provides process CPU time")
        print("  ✓ CPU %: Calculated from CPU time delta")
        print("  ✓ RAM: resource.getrusage() provides max RSS memory")
        print("  ✓ Page Faults: Minor and major faults available")
        print("  ✓ I/O: Block read/write operations")
        print("  ✓ Context Switches: Voluntary and involuntary")
        print("  ✗ Disk I/O detailed: Not accessible via standard library without /proc")
        print("  ✗ Network: Not accessible via standard library without /proc")
        
        print("=" * 80 + "\n")


# Global monitoring instance
_default_monitor: Optional[ResourceMonitor] = None


def get_default_monitor(interval: float = 5.0) -> ResourceMonitor:
    """Get or create the default monitor instance."""
    global _default_monitor
    
    if _default_monitor is None:
        _default_monitor = ResourceMonitor(interval=interval)
    
    return _default_monitor


def start_monitoring(interval: float = 5.0) -> ResourceMonitor:
    """Start default resource monitoring."""
    monitor = get_default_monitor(interval)
    monitor.start()
    return monitor


def stop_monitoring() -> None:
    """Stop default resource monitoring."""
    global _default_monitor
    
    if _default_monitor is not None:
        _default_monitor.stop()
