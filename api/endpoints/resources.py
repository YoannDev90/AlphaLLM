import logging
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter

from config import LOGGER_NAME
from utils.ressources import get_default_monitor

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)

router = APIRouter()
logger = logging.getLogger(LOGGER_NAME)

def get_daily_data():
    """Aggregate resource data from CSV for the last 24 hours, one point per minute, with deltas for incremental metrics."""
    csv_file = "monitoring.csv"
    if not os.path.exists(csv_file):
        return []
    
    data = []
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = datetime.fromisoformat(row['timestamp'])
                if ts < cutoff:
                    continue
                data.append({
                    'timestamp': ts,
                    'cpu_percent': float(row['cpu_percent']) if row['cpu_percent'] else 0.0,
                    'max_memory_mb': float(row['max_memory_mb']) if row['max_memory_mb'] else 0.0,
                })
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return []
    
    # Aggregate by minute
    minute_data = defaultdict(list)
    for d in data:
        minute = d['timestamp'].replace(second=0, microsecond=0)
        minute_data[minute].append(d)
    
    aggregated = []
    for minute, samples in sorted(minute_data.items()):
        if samples:
            avg_cpu = sum(s['cpu_percent'] for s in samples) / len(samples)
            avg_mem = sum(s['max_memory_mb'] for s in samples) / len(samples)
            aggregated.append({
                'timestamp': minute.isoformat(),
                'cpu_percent': round(avg_cpu, 2),
                'max_memory_mb': round(avg_mem, 2),
            })
    return aggregated

def get_realtime_data():
    """Get last 60 seconds of resource data."""
    monitor = get_default_monitor()
    snapshots = monitor.get_all_snapshots()
    recent = snapshots[-60:] if len(snapshots) >= 60 else snapshots
    
    return [{
        'timestamp': s.timestamp.isoformat(),
        'cpu_percent': round(s.cpu_percent, 2) if s.cpu_percent else 0.0,
        'max_memory_mb': round(s.max_memory, 2) if s.max_memory else 0.0,
    } for s in recent]

@router.get("/resources", tags=["general"])
async def resources_check():
    """API resources check endpoint with graph data"""
    try:
        realtime = get_realtime_data()
        daily = get_daily_data()
        return {
            "realtime": realtime,
            "daily": daily
        }
    except Exception as e:
        logger.error(f"Error during resources check: {str(e)}")
        return {"status": "error", "message": "An internal server error occurred."}