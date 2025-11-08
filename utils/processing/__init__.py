"""Message and data processing module."""

# Delay imports to avoid circular dependencies
# Import functions directly when needed rather than at module load time

def __getattr__(name):
    """Lazy import to handle circular dependencies."""
    if name == 'generate_response':
        from utils.processing.ai_handler.core import generate_response
        return generate_response
    elif name == 'process_ai_response':
        from utils.processing.ai_handler.discord_handler import process_ai_response
        return process_ai_response
    elif name == 'message_process':
        from utils.processing.message import message_process
        return message_process
    elif name == 'smart_long_messages_with_view':
        from utils.processing.message import smart_long_messages_with_view
        return smart_long_messages_with_view
    elif name == 'crawl':
        from utils.processing.web import crawl
        return crawl
    elif name == 'md_conversion':
        from utils.processing.markdown import md_conversion
        return md_conversion
    elif name == 'detect_and_convert_tables':
        from utils.processing.table import detect_and_convert_tables
        return detect_and_convert_tables
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'generate_response',
    'process_ai_response',
    'message_process',
    'smart_long_messages_with_view',
    'crawl',
    'md_conversion',
    'detect_and_convert_tables',
]
