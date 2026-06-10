"""Test cases for code block handling."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.handlers.codeblock import send_code_block_with_return, send_code_block


class TestCodeBlockHandlers:
    """Test cases for code block handling."""

    @pytest.mark.asyncio
    async def test_send_code_block_with_return_short_code(self):
        """Test sending a short code block."""
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        code_block = "```python\nprint('Hello, World!')\n```"
        result = await send_code_block_with_return(mock_channel, code_block)

        # Verify channel.send was called
        assert mock_channel.send.called
        # Verify the message contains the code
        call_args = mock_channel.send.call_args[0][0]
        assert "```python" in call_args
        assert "print('Hello, World!')" in call_args

    @pytest.mark.asyncio
    async def test_send_code_block_with_return_long_code_splits(self):
        """Test sending a long code block that requires splitting."""
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        # Create a code block that exceeds Discord's limit (2000 chars)
        long_code = "```python\n" + "x" * 3000 + "\n```"
        result = await send_code_block_with_return(mock_channel, long_code)

        # Verify channel.send was called multiple times for splitting
        assert mock_channel.send.call_count > 1

    @pytest.mark.asyncio
    async def test_send_code_block_with_return_latex_language(self):
        """Test LaTeX language handling (should use MessageSender)."""
        mock_channel = AsyncMock()
        mock_bot = MagicMock()
        mock_channel.id = 12345

        # Mock MessageSender.send_latex_image to avoid external dependencies
        with patch('utils.handlers.messages.MessageSender') as mock_sender_class:
            mock_sender_instance = AsyncMock()
            mock_sender_class.return_value = mock_sender_instance
            mock_sender_instance.send_latex_image = AsyncMock()

            code_block = "```latex\nx = {-b \\pm \\sqrt{b^2 - 4ac} \\over 2a}\n```"
            result = await send_code_block_with_return(mock_channel, code_block, bot=mock_bot)

            # Verify MessageSender was instantiated and used
            mock_sender_class.assert_called_once()
            mock_sender_instance.send_latex_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_code_block_short(self):
        """Test send_code_block (without return)."""
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()

        code_block = "```python\nprint('test')\n```"
        await send_code_block(mock_channel, code_block)

        # Verify channel.send was called
        assert mock_channel.send.called