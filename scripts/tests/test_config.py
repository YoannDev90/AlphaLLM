"""Test cases for configuration handlers."""

import io
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import load_config, read_system_prompt, read_mood_prompt


class TestConfigHandlers:
    """Test cases for configuration handlers."""

    def test_load_config_default(self):
        """Test loading default configuration."""
        cfg, logging_cfg = load_config()

        # Should return config and logging config objects
        assert cfg is not None
        assert logging_cfg is not None

        # Check Config object has expected attributes
        assert hasattr(cfg, 'BOT_TOKEN')
        assert hasattr(cfg, 'WEBHOOK_URL')
        assert hasattr(cfg, 'BASE_DIR')
        assert hasattr(cfg, 'SYSTEM_PROMPT_PATH')

        # Check LoggingConfig object has expected properties
        assert hasattr(logging_cfg, 'level')
        assert hasattr(logging_cfg, 'enable_file_logging')
        assert hasattr(logging_cfg, 'log_file')

    def test_load_config_with_path(self):
        """Test loading configuration from a specific path."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
[test]
name = "test"
""")
            temp_path = f.name

        try:
            cfg, logging_cfg = load_config(temp_path)

            # Should load without errors
            assert cfg is not None
            assert logging_cfg is not None
            assert cfg.CONFIG_PATH == temp_path
        finally:
            os.unlink(temp_path)

    @patch.dict(os.environ, {'BOT_TOKEN': 'test_token', 'WEBHOOK_URL': 'test_webhook'})
    def test_load_config_with_env_vars(self):
        """Test configuration loading with environment variables."""
        cfg, logging_cfg = load_config()

        # Environment variables should be used
        assert cfg.BOT_TOKEN == 'test_token'
        assert cfg.WEBHOOK_POSTURL == 'test_webhook'

    def test_read_system_prompt_file_exists(self):
        """Test reading system prompt when file exists."""
        # Create a temporary system prompt file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is the system prompt.\nWith multiple lines.")
            temp_path = f.name

        # Mock the config path to point to our temp file
        with patch('core.config.cfg') as mock_cfg:
            mock_cfg.SYSTEM_PROMPT_PATH = temp_path

            result = read_system_prompt()

            assert result == "This is the system prompt.\nWith multiple lines."

        os.unlink(temp_path)

    def test_read_system_prompt_file_not_exists(self):
        """Test reading system prompt when file does not exist."""
        with patch('core.config.cfg') as mock_cfg:
            mock_cfg.SYSTEM_PROMPT_PATH = "/nonexistent/path.txt"

            result = read_system_prompt()

            assert result is None

    @patch('core.config.BASE_DIR', '/tmp')
    def test_read_mood_prompt_exists(self):
        """Test reading mood prompt when mood file exists."""
        # Create a temporary mood directory and file with correct structure
        moods_dir = '/tmp/data/moods'
        os.makedirs(moods_dir, exist_ok=True)
        mood_file = os.path.join(moods_dir, "happy.txt")

        with open(mood_file, 'w') as f:
            f.write("Happy mood prompt.")

        try:
            result = read_mood_prompt("happy")
            assert result == "Happy mood prompt."
        finally:
            import shutil
            shutil.rmtree('/tmp/data')

    @patch('core.config.BASE_DIR', '/tmp')
    def test_read_mood_prompt_fallback(self):
        """Test reading mood prompt with fallback to neutral."""
        # Create only neutral.txt file with correct structure
        moods_dir = '/tmp/data/moods'
        os.makedirs(moods_dir, exist_ok=True)
        neutral_file = os.path.join(moods_dir, "neutral.txt")

        with open(neutral_file, 'w') as f:
            f.write("Neutral mood prompt.")

        try:
            result = read_mood_prompt("nonexistent_mood")
            assert result == "Neutral mood prompt."
        finally:
            import shutil
            shutil.rmtree('/tmp/data')

    @patch('core.config.BASE_DIR', '/tmp')
    def test_read_mood_prompt_none(self):
        """Test reading mood prompt when no mood specified and no files exist."""
        # Ensure data/moods directory doesn't exist
        if os.path.exists('/tmp/data'):
            import shutil
            shutil.rmtree('/tmp/data')

        result = read_mood_prompt(None)
        assert result is None