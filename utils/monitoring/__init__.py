"""Monitoring and resource tracking module."""

# Lazy imports to avoid circular dependencies

def __getattr__(name):
    """Lazy import to handle dependencies."""
    if name == 'ResourceMonitor':
        from utils.monitoring.resource import ResourceMonitor
        return ResourceMonitor
    elif name == 'ResourceMonitoringTask':
        from utils.monitoring.task import ResourceMonitoringTask
        return ResourceMonitoringTask
    elif name == 'get_status':
        from utils.monitoring.status import get_status
        return get_status
    elif name == 'ResourceExporter':
        from utils.monitoring.exporter import ResourceExporter
        return ResourceExporter
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'ResourceMonitor',
    'ResourceMonitoringTask', 
    'get_status',
    'ResourceExporter',
]
