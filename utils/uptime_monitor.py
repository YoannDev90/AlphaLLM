import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from config import LOGGER_NAME
from utils.ressources import get_default_monitor

logger = logging.getLogger(LOGGER_NAME)


class UptimeMonitor:
    """Monitor for service uptime and availability."""

    def __init__(self, log_file: str = "data/uptime_log.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_log()

    def _load_log(self):
        """Load uptime log from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    self.uptime_periods: List[dict] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading uptime log: {e}")
                self.uptime_periods = []
        else:
            self.uptime_periods = []

    def _save_log(self):
        """Save uptime log to file."""
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.uptime_periods, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving uptime log: {e}")

    def start(self):
        """Record service start."""
        now = datetime.now()
        # If last period has no end, it means crash, analyze resource snapshots to set end
        if self.uptime_periods and self.uptime_periods[-1].get("end") is None:
            monitor = get_default_monitor()
            snapshots = monitor.get_all_snapshots()
            if snapshots:
                # Find the last snapshot with cpu_percent > 0
                last_up = None
                for s in reversed(snapshots):
                    if s.cpu_percent and s.cpu_percent > 0:
                        last_up = s.timestamp
                        break
                if last_up:
                    # Set end to last_up, assuming down after that
                    self.uptime_periods[-1]["end"] = last_up.isoformat()
                else:
                    # All 0, set end to the earliest snapshot time
                    self.uptime_periods[-1]["end"] = snapshots[0].timestamp.isoformat()
            else:
                # No snapshots, set end to now
                self.uptime_periods[-1]["end"] = now.isoformat()
        # Add new period
        self.uptime_periods.append({"start": now.isoformat(), "end": None})
        self._save_log()
        logger.info("Uptime monitor started")

    def stop(self):
        """Record service stop."""
        now = datetime.now().isoformat()
        if self.uptime_periods and self.uptime_periods[-1].get("end") is None:
            self.uptime_periods[-1]["end"] = now
            self._save_log()
        logger.info("Uptime monitor stopped")

    def get_current_uptime(self) -> float:
        """Get current uptime in seconds."""
        if not self.uptime_periods or self.uptime_periods[-1].get("end") is not None:
            return 0.0
        start = datetime.fromisoformat(self.uptime_periods[-1]["start"])
        return (datetime.now() - start).total_seconds()

    def get_availability(self, days: int) -> float:
        """Get availability percentage over the last X days."""
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        total_period = days * 24 * 3600  # total seconds
        uptime_seconds = 0.0

        for period in self.uptime_periods:
            start = datetime.fromisoformat(period["start"])
            end_str = period.get("end")
            end = datetime.fromisoformat(end_str) if end_str else now

            # Clip to cutoff
            effective_start = max(start, cutoff)
            effective_end = end

            if effective_end > cutoff:
                uptime_seconds += (effective_end - effective_start).total_seconds()

        if total_period == 0:
            return 100.0
        return min(100.0, (uptime_seconds / total_period) * 100.0)


# Global instance
_uptime_monitor: Optional[UptimeMonitor] = None


def get_uptime_monitor() -> UptimeMonitor:
    """Get the global uptime monitor instance."""
    global _uptime_monitor
    if _uptime_monitor is None:
        _uptime_monitor = UptimeMonitor()
    return _uptime_monitor