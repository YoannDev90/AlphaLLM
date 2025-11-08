"""
Resource Export Module - Exports monitoring data to CSV periodically
"""

import asyncio
import logging
import csv
from datetime import datetime, timedelta
from pathlib import Path
from utils.config.app_config import logger_name
from utils.monitoring.resource import get_default_monitor

logger = logging.getLogger(logger_name)


class ResourceExporter:
    """Handles periodic export of resource data to CSV"""
    
    def __init__(self, csv_filename: str = "Resources.csv", 
                 collection_interval: float = 1.0,
                 export_interval: float = 30.0,
                 max_age_hours: int = 4):
        """
        Initialize resource exporter
        
        Args:
            csv_filename: Output CSV filename (relative to current directory)
            collection_interval: Collect data every N seconds (default: 1)
            export_interval: Export to CSV every N seconds (default: 30)
            max_age_hours: Keep only last N hours of data (default: 4)
        """
        self.csv_filename = csv_filename
        self.collection_interval = collection_interval
        self.export_interval = export_interval
        self.max_age_hours = max_age_hours
        self.is_running = False
        self.monitor = get_default_monitor(interval=collection_interval)
        self._export_counter = 0
        self._last_exported_index = 0  # Track which snapshots have been exported
        
        logger.debug(
            f"ResourceExporter initialized (CSV: {csv_filename}, "
            f"collect: {collection_interval}s, export: {export_interval}s, "
            f"max_age: {max_age_hours}h)"
        )
    
    async def start(self):
        """Start periodic export task"""
        self.is_running = True
        logger.debug("ResourceExporter started")
        
        # Start the resource monitor if not already running
        if not self.monitor.is_monitoring:
            self.monitor.start()
            logger.debug("Resource monitoring started")
        
        try:
            while self.is_running:
                self._export_counter += 1
                
                # Export every N collection intervals
                export_threshold = int(self.export_interval / self.collection_interval)
                
                if self._export_counter >= export_threshold:
                    self._export_to_csv()  # Call synchronously
                    self._export_counter = 0
                
                await asyncio.sleep(self.collection_interval)
        
        except asyncio.CancelledError:
            logger.debug("ResourceExporter cancelled")
            self.is_running = False
        except Exception as e:
            logger.error(f"Error in ResourceExporter: {e}")
            self.is_running = False
    
    def _export_to_csv(self):
        """Export current monitoring data to CSV file"""
        try:
            snapshots = self.monitor.get_all_snapshots()
            
            if not snapshots:
                logger.debug("No snapshots to export")
                return
            
            # Get only new snapshots since last export
            new_snapshots = snapshots[self._last_exported_index:]
            
            if not new_snapshots:
                logger.debug("No new snapshots to export")
                return
            
            # Clean old entries first
            self._cleanup_old_entries()
            
            # Create CSV file path
            csv_path = Path(self.csv_filename)
            
            # Check if file exists to determine if we need headers
            file_exists = csv_path.exists() and csv_path.stat().st_size > 0
            
            # Define CSV fieldnames
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
            
            # Append mode: write only new snapshots
            with open(csv_path, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header only if file is new or empty
                if not file_exists:
                    writer.writeheader()
                    logger.debug(f"Created new CSV file: {csv_path}")
                
                # Write only new snapshots
                for snapshot in new_snapshots:
                    writer.writerow(snapshot.to_dict())
            
            # Update index to track that we've exported these snapshots
            self._last_exported_index = len(snapshots)
            
            logger.debug(
                f"Exported {len(new_snapshots)} new samples to {csv_path} "
                f"(total lines: {self._count_csv_lines()})"
            )
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def _count_csv_lines(self) -> int:
        """Count lines in CSV file"""
        try:
            csv_path = Path(self.csv_filename)
            if csv_path.exists():
                with open(csv_path, 'r') as f:
                    return sum(1 for _ in f)
            return 0
        except Exception as e:
            logger.error(f"Error counting CSV lines: {e}")
            return 0
    
    def _cleanup_old_entries(self) -> None:
        """Remove entries older than max_age_hours from CSV file"""
        try:
            csv_path = Path(self.csv_filename)
            
            # If file doesn't exist, nothing to clean
            if not csv_path.exists():
                return
            
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
            
            # Read all entries
            rows_to_keep = []
            header = None
            removed_count = 0
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames
                
                for row in reader:
                    try:
                        # Parse timestamp
                        timestamp_str = row.get('timestamp', '')
                        if not timestamp_str:
                            continue
                        
                        # Handle ISO format timestamp
                        timestamp = datetime.fromisoformat(timestamp_str)
                        
                        # Keep entries newer than cutoff
                        if timestamp >= cutoff_time:
                            rows_to_keep.append(row)
                        else:
                            removed_count += 1
                    except ValueError:
                        # If timestamp can't be parsed, keep the row
                        rows_to_keep.append(row)
            
            # Write back only kept entries
            if removed_count > 0 or len(rows_to_keep) > 0:
                with open(csv_path, 'w', newline='') as f:
                    if header:
                        writer = csv.DictWriter(f, fieldnames=header)
                        writer.writeheader()
                        writer.writerows(rows_to_keep)
                
                if removed_count > 0:
                    logger.debug(
                        f"Cleaned {removed_count} old entries (older than {self.max_age_hours}h) "
                        f"from {csv_path}. Kept {len(rows_to_keep)} entries."
                    )
        
        except Exception as e:
            logger.error(f"Error cleaning old entries: {e}")
    
    def stop(self):
        """Stop the export task"""
        self.is_running = False
        
        # Stop resource monitor
        if self.monitor.is_monitoring:
            self.monitor.stop()
        
        logger.debug("ResourceExporter stopped")
    
    async def manual_export(self):
        """Manually trigger an export"""
        logger.debug("Manual export triggered")
        self._export_to_csv()


# Global instance
_exporter: ResourceExporter = None


def get_exporter(csv_filename: str = "Resources.csv",
                 collection_interval: float = 1.0,
                 export_interval: float = 30.0,
                 max_age_hours: int = 4) -> ResourceExporter:
    """Get or create the global exporter instance"""
    global _exporter
    
    if _exporter is None:
        _exporter = ResourceExporter(
            csv_filename=csv_filename,
            collection_interval=collection_interval,
            export_interval=export_interval,
            max_age_hours=max_age_hours
        )
    
    return _exporter


async def start_exporter(csv_filename: str = "Resources.csv",
                         collection_interval: float = 1.0,
                         export_interval: float = 30.0,
                         max_age_hours: int = 4) -> ResourceExporter:
    """Start the global resource exporter"""
    exporter = get_exporter(csv_filename, collection_interval, export_interval, max_age_hours)
    
    # create task to run exporter
    asyncio.create_task(exporter.start())
    
    return exporter


def stop_exporter() -> None:
    """Stop the global resource exporter"""
    global _exporter
    
    if _exporter is not None:
        _exporter.stop()
