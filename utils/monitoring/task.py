"""
Module for periodic resource monitoring and reporting
"""

import asyncio
import logging
from datetime import datetime
from utils.config.app_config import logger_name
from utils.monitoring.resource import get_default_monitor

logger = logging.getLogger(logger_name)


class ResourceMonitoringTask:
    """Handles periodic monitoring and resource analysis"""
    
    def __init__(self, interval: int = 300, alert_threshold_cpu_percent: float = 50.0,
                 alert_threshold_memory: float = 500.0):
        """
        Initialize resource monitoring task
        
        Args:
            interval: Monitoring interval in seconds (default: 5 minutes)
            alert_threshold_cpu_percent: Alert if CPU % exceeds this value
            alert_threshold_memory: Alert if memory exceeds this (MB)
        """
        self.interval = interval
        self.alert_threshold_cpu_percent = alert_threshold_cpu_percent
        self.alert_threshold_memory = alert_threshold_memory
        self.is_running = False
        self.monitor = get_default_monitor()
    
    async def start(self):
        """Start periodic monitoring task"""
        self.is_running = True
        logger.info(f"ResourceMonitoringTask started (interval: {self.interval}s)")
        
        try:
            while self.is_running:
                await asyncio.sleep(self.interval)
                await self._analyze_resources()
        except asyncio.CancelledError:
            logger.info("ResourceMonitoringTask cancelled")
            self.is_running = False
        except Exception as e:
            logger.error(f"Error in ResourceMonitoringTask: {e}")
            self.is_running = False
    
    async def _analyze_resources(self):
        """Analyze current Resources and log alerts if necessary"""
        try:
            snapshot = self.monitor.get_latest_snapshot()
            stats = self.monitor.get_statistics()
            
            if not snapshot or not stats:
                return
            
            # Check CPU usage percentage
            if snapshot.cpu_percent is not None and snapshot.cpu_percent > self.alert_threshold_cpu_percent:
                logger.warning(
                    f"⚠️ HIGH CPU USAGE: Current={snapshot.cpu_percent:.2f}%, "
                    f"Avg={stats.get('cpu_percent_avg', 0):.2f}%, "
                    f"Threshold={self.alert_threshold_cpu_percent:.2f}%"
                )
            
            # Check memory usage
            if snapshot.max_memory > self.alert_threshold_memory:
                logger.warning(
                    f"⚠️ HIGH MEMORY USAGE: Current={snapshot.max_memory:.1f}MB, "
                    f"Max={stats['memory_max']:.1f}MB, "
                    f"Avg={stats['memory_avg']:.1f}MB, "
                    f"Threshold={self.alert_threshold_memory:.1f}MB"
                )
            
            # Check for major page faults (memory pressure indicator)
            if snapshot.page_faults_major is not None and snapshot.page_faults_major > 100:
                logger.warning(
                    f"⚠️ HIGH PAGE FAULTS: Major={snapshot.page_faults_major}, "
                    f"Minor={snapshot.page_faults_minor} "
                    f"(Indicates memory pressure)"
                )
            
            # Log normal status periodically
            cpu_percent_str = f"{snapshot.cpu_percent:.2f}%" if snapshot.cpu_percent is not None else "N/A"
            logger.debug(
                f"📊 Resource Check - CPU: {snapshot.cpu_time:.2f}s ({cpu_percent_str}) "
                f"| Memory: {snapshot.max_memory:.1f}MB | "
                f"Samples: {stats['samples_count']}"
            )
        
        except Exception as e:
            logger.error(f"Error in resource analysis: {e}")
    
    def stop(self):
        """Stop the monitoring task"""
        self.is_running = False
        logger.info("ResourceMonitoringTask stopped")


# Global instance
_monitoring_task: ResourceMonitoringTask = None


def get_monitoring_task(interval: int = 300) -> ResourceMonitoringTask:
    """Get or create the global monitoring task"""
    global _monitoring_task
    
    if _monitoring_task is None:
        _monitoring_task = ResourceMonitoringTask(interval=interval)
    
    return _monitoring_task
