"""Resource monitor that replaced the legacy helpers."""

import csv
import logging
import os
import resource
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

@dataclass
class ResourceSnapshot:
    """Represents a single resource snapshot."""

    timestamp: datetime
    process_id: int
    cpu_time: float
    cpu_user_time: Optional[float] = None
    cpu_sys_time: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    page_faults_minor: Optional[int] = None
    page_faults_major: Optional[int] = None
    io_reads: Optional[int] = None
    io_writes: Optional[int] = None
    context_switches_vol: Optional[int] = None
    context_switches_invol: Optional[int] = None
    swaps: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "process_id": self.process_id,
            "cpu_time_sec": f"{self.cpu_time:.5f}",
            "cpu_user_time_sec": f"{self.cpu_user_time:.5f}" if self.cpu_user_time is not None else None,
            "cpu_sys_time_sec": f"{self.cpu_sys_time:.5f}" if self.cpu_sys_time is not None else None,
            "cpu_percent": f"{self.cpu_percent:.5f}" if self.cpu_percent is not None else None,
            "memory_percent": f"{self.memory_percent:.5f}" if self.memory_percent is not None else None,
            "page_faults_minor": self.page_faults_minor,
            "page_faults_major": self.page_faults_major,
            "io_reads": self.io_reads,
            "io_writes": self.io_writes,
            "context_switches_vol": self.context_switches_vol,
            "context_switches_invol": self.context_switches_invol,
            "swaps": self.swaps,
        }


class ResourceMonitor:
    """Low level monitor that collects metrics on a background thread."""

    def __init__(self, interval: float = 1.0, max_samples: int = 10000, csv_file: Optional[str] = None) -> None:
        self.interval = interval
        self.max_samples = max_samples
        self.process_id = os.getpid()
        self.is_monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.samples: List[ResourceSnapshot] = []
        self._previous_snapshot: Optional[ResourceSnapshot] = None
        self.csv_file = csv_file
        self._csv_initialized = False
        self._previous_network_sent = 0
        self._previous_network_recv = 0
        if csv_file:
            self._init_csv()

    def _init_csv(self) -> None:
        """Initialize CSV file for streaming writes."""
        if not self.csv_file:
            return
        path = Path(self.csv_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = path.exists() and path.stat().st_size > 0
        if not file_exists:
            with open(path, "w", newline="") as csvfile:
                fieldnames = [
                    "timestamp",
                    "process_id",
                    "cpu_time_sec",
                    "cpu_user_time_sec",
                    "cpu_sys_time_sec",
                    "cpu_percent",
                    "memory_percent",
                    "page_faults_minor",
                    "page_faults_major",
                    "io_reads",
                    "io_writes",
                    "context_switches_vol",
                    "context_switches_invol",
                    "swaps",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
        self._csv_initialized = True

    def _write_snapshot_to_csv(self, snapshot: ResourceSnapshot) -> None:
        """Write a snapshot to the CSV file."""
        if not self._csv_initialized or not snapshot:
            return
        try:
            with open(self.csv_file, "a", newline="") as csvfile:
                fieldnames = [
                    "timestamp",
                    "process_id",
                    "cpu_time_sec",
                    "cpu_user_time_sec",
                    "cpu_sys_time_sec",
                    "cpu_percent",
                    "memory_percent",
                    "page_faults_minor",
                    "page_faults_major",
                    "io_reads",
                    "io_writes",
                    "context_switches_vol",
                    "context_switches_invol",
                    "swaps",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(snapshot.to_dict())
        except Exception as e:
            logger.error(f"Failed to write snapshot to CSV: {e}")

    def _collect_snapshot(self) -> Optional[ResourceSnapshot]:
        try:
            current_time = time.time()
            cpu_time = time.process_time()
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            cpu_user = rusage.ru_utime
            cpu_system = rusage.ru_stime
            total_cpu = cpu_user + cpu_system

            cpu_percent: Optional[float] = None
            if self._previous_snapshot:
                delta_time = current_time - self._previous_snapshot.timestamp.timestamp()
                previous_cpu = (
                    (self._previous_snapshot.cpu_user_time or 0) +
                    (self._previous_snapshot.cpu_sys_time or 0)
                )
                delta_cpu = total_cpu - previous_cpu
                if delta_time > 0:
                    cpu_percent = delta_cpu / delta_time * 100.0
                    max_cpu = (os.cpu_count() or 1) * 100.0
                    cpu_percent = min(cpu_percent, max_cpu)

            max_memory_kb = rusage.ru_maxrss
            if os.uname().sysname == "Darwin":
                max_memory_mb = max_memory_kb / (1024 * 1024)
            else:
                max_memory_mb = max_memory_kb / 1024

            memory_percent = (max_memory_mb / 4096) * 100

            snapshot = ResourceSnapshot(
                timestamp=datetime.now(),
                process_id=self.process_id,
                cpu_time=cpu_time,
                cpu_user_time=cpu_user,
                cpu_sys_time=cpu_system,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                page_faults_minor=rusage.ru_minflt,
                page_faults_major=rusage.ru_majflt,
                io_reads=rusage.ru_inblock,
                io_writes=rusage.ru_oublock,
                context_switches_vol=rusage.ru_nvcsw,
                context_switches_invol=rusage.ru_nivcsw,
                swaps=rusage.ru_nswap,
            )
            self._previous_snapshot = snapshot
            return snapshot
        except Exception as exc:  # pragma: no cover - monitoring is best effort
            logger.error(f"Failed to collect resource snapshot: {exc}")
            return None

    def _monitor_loop(self) -> None:
        logger.debug("Resource monitoring thread started")
        while self.is_monitoring:
            snapshot = self._collect_snapshot()
            if snapshot:
                with self._lock:
                    self.samples.append(snapshot)
                    if len(self.samples) > self.max_samples:
                        self.samples.pop(0)
                self._write_snapshot_to_csv(snapshot)
            time.sleep(self.interval)
        logger.debug("Resource monitoring thread stopped")

    def start(self) -> None:
        if self.is_monitoring:
            logger.debug("Resource monitoring already running")
            return
        self.is_monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ResourceMonitor")
        self._thread.start()
        logger.debug("Resource monitoring started")

    def stop(self) -> None:
        if not self.is_monitoring:
            logger.debug("Resource monitoring already stopped")
            return
        self.is_monitoring = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.debug("Resource monitoring stopped")

    def get_latest_snapshot(self) -> Optional[ResourceSnapshot]:
        with self._lock:
            return self.samples[-1] if self.samples else None

    def get_all_snapshots(self) -> List[ResourceSnapshot]:
        with self._lock:
            return list(self.samples)

    def get_statistics(self) -> Dict[str, float]:
        with self._lock:
            if not self.samples:
                return {}
            cpu_times = [snapshot.cpu_time for snapshot in self.samples]
            stats: Dict[str, float] = {
                "samples_count": len(self.samples),
                "cpu_time_min": min(cpu_times),
                "cpu_time_max": max(cpu_times),
                "cpu_time_avg": sum(cpu_times) / len(cpu_times),
            }
            cpu_percents = [snapshot.cpu_percent for snapshot in self.samples if snapshot.cpu_percent is not None]
            if cpu_percents:
                stats.update({
                    "cpu_percent_min": min(cpu_percents),
                    "cpu_percent_max": max(cpu_percents),
                    "cpu_percent_avg": sum(cpu_percents) / len(cpu_percents),
                })
            memory_values = [snapshot.memory_percent for snapshot in self.samples if snapshot.memory_percent is not None]
            if memory_values:
                stats.update({
                    "memory_min": min(memory_values),
                    "memory_max": max(memory_values),
                    "memory_avg": sum(memory_values) / len(memory_values),
                })
            return stats

    def get_current_usage(self) -> Dict[str, Any]:
        snapshot = self._collect_snapshot()
        if not snapshot:
            return {}
        return snapshot.to_dict()

    def export_to_csv(self, filename: str) -> None:
        with self._lock:
            if not self.samples:
                logger.debug("No resource samples to export")
                return
            try:
                path = Path(filename)
                path.parent.mkdir(parents=True, exist_ok=True)
                file_exists = path.exists() and path.stat().st_size > 0
                fieldnames = [
                    "timestamp",
                    "process_id",
                    "cpu_time_sec",
                    "cpu_user_time_sec",
                    "cpu_sys_time_sec",
                    "cpu_percent",
                    "memory_percent",
                    "page_faults_minor",
                    "page_faults_major",
                    "io_reads",
                    "io_writes",
                    "context_switches_vol",
                    "context_switches_invol",
                    "swaps",
                ]
                with open(path, "a", newline="") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                    for snapshot in self.samples:
                        writer.writerow(snapshot.to_dict())
                logger.info(f"Exported {len(self.samples)} resource snapshots to {path}")
            except Exception as exc:
                logger.error(f"Failed to export resource snapshots: {exc}")

    def print_summary(self) -> None:
        """Print a summary of resource usage statistics."""
        stats = self.get_statistics()
        if not stats:
            logger.info("No resource statistics available")
            return
        
        logger.info("Resource Usage Summary:")
        logger.info(f"  Samples collected: {stats.get('samples_count', 0)}")
        if 'cpu_time_avg' in stats:
            logger.info(f"  CPU Time - Avg: {stats['cpu_time_avg']:.2f}s, Max: {stats['cpu_time_max']:.2f}s")
        if 'cpu_percent_avg' in stats:
            logger.info(f"  CPU Usage - Avg: {stats['cpu_percent_avg']:.2f}%, Max: {stats['cpu_percent_max']:.2f}%")
        if 'memory_avg' in stats:
            logger.info(f"  Memory - Min: {stats['memory_min']:.1f}MB, Avg: {stats['memory_avg']:.1f}MB, Max: {stats['memory_max']:.1f}MB")

    def get_last_timestamp(self) -> Optional[datetime]:
        """Get the last timestamp from the CSV file."""
        if not self.csv_file or not Path(self.csv_file).exists():
            logger.debug(f"CSV file {self.csv_file} does not exist")
            return None
        try:
            with open(self.csv_file, "r", newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                last_row = None
                for row in reader:
                    last_row = row
                if last_row and "timestamp" in last_row:
                    ts = datetime.fromisoformat(last_row["timestamp"])
                    logger.debug(f"Last timestamp from CSV: {ts}")
                    return ts
                else:
                    logger.debug("No valid last row found in CSV")
        except Exception as e:
            logger.error(f"Failed to read last timestamp from CSV: {e}")
        return None

    def fill_gaps(self, current_time: datetime) -> None:
        """Fill gaps in CSV with zero values for missing seconds in recent history."""
        if not self._csv_initialized:
            logger.debug("CSV not initialized, skipping fill_gaps")
            return
        timestamps = []
        if Path(self.csv_file).exists():
            try:
                with open(self.csv_file, "r", newline="") as csvfile:
                    reader = csv.DictReader(csvfile)
                    rows = list(reader)[-500:]
                    for row in rows:
                        if "timestamp" in row:
                            try:
                                ts = datetime.fromisoformat(row["timestamp"])
                                timestamps.append(ts)
                            except ValueError:
                                pass
            except Exception as e:
                logger.error(f"Failed to read timestamps from CSV: {e}")
                return
        
        if not timestamps:
            logger.debug("No timestamps in CSV, skipping fill_gaps")
            return
        
        timestamps.sort()
        
        filled_count = 0
        fieldnames = [
            "timestamp",
            "process_id",
            "cpu_time_sec",
            "cpu_user_time_sec",
            "cpu_sys_time_sec",
            "cpu_percent",
            "memory_percent",
            "page_faults_minor",
            "page_faults_major",
            "io_reads",
            "io_writes",
            "context_switches_vol",
            "context_switches_invol",
            "swaps",
        ]
        try:
            with open(self.csv_file, "a", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for i in range(len(timestamps) - 1):
                    current_ts = timestamps[i]
                    next_expected = current_ts + timedelta(seconds=1)
                    while next_expected < timestamps[i+1]:
                        zero_snapshot = ResourceSnapshot(
                            timestamp=next_expected,
                            process_id=self.process_id,
                            cpu_time=0.0,
                            cpu_user_time=0.0,
                            cpu_sys_time=0.0,
                            cpu_percent=0.0,
                            memory_percent=0.0,
                            page_faults_minor=0,
                            page_faults_major=0,
                            io_reads=0,
                            io_writes=0,
                            context_switches_vol=0,
                            context_switches_invol=0,
                            swaps=0,
                        )
                        writer.writerow(zero_snapshot.to_dict())
                        next_expected += timedelta(seconds=1)
                        filled_count += 1
                
                last_ts = timestamps[-1]
                next_ts = last_ts + timedelta(seconds=1)
                while next_ts <= current_time:
                    zero_snapshot = ResourceSnapshot(
                        timestamp=next_ts,
                        process_id=self.process_id,
                        cpu_time=0.0,
                        cpu_user_time=0.0,
                        cpu_sys_time=0.0,
                        cpu_percent=0.0,
                        memory_percent=0.0,
                        page_faults_minor=0,
                        page_faults_major=0,
                        io_reads=0,
                        io_writes=0,
                        context_switches_vol=0,
                        context_switches_invol=0,
                        swaps=0,
                    )
                    writer.writerow(zero_snapshot.to_dict())
                    next_ts += timedelta(seconds=1)
                    filled_count += 1
        except Exception as e:
            logger.error(f"Failed to write gap fills to CSV: {e}")
        
        logger.debug(f"Filled {filled_count} gap entries")

_monitor_instance: Optional[ResourceMonitor] = None

def get_default_monitor(interval: float = 1.0, csv_file: Optional[str] = None) -> ResourceMonitor:
    """Return the shared resource monitor."""

    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ResourceMonitor(interval=interval, csv_file=csv_file)
    return _monitor_instance


def start_monitoring(interval: float = 1.0, csv_file: Optional[str] = None) -> ResourceMonitor:
    """Start the shared monitor if not already running."""

    monitor = get_default_monitor(interval=interval, csv_file=csv_file)
    monitor.start()
    return monitor


def stop_monitoring() -> None:
    """Gracefully stop the shared monitor."""

    if _monitor_instance is not None:
        _monitor_instance.stop()
