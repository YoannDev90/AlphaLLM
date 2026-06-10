"""Test cases for MessageSender class."""

import asyncio
import io
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.handlers.messages import MessageSender


class TestMessageSender:
    """Test cases for MessageSender class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_channel = MagicMock()
        self.mock_channel.id = 12345
        self.mock_bot = MagicMock()
        self.mock_bot.get_channel = MagicMock(return_value=self.mock_channel)

    @pytest.mark.asyncio
    async def test_send_text_chunks_simple(self):
        """Test sending simple text chunks."""
        sender = MessageSender(self.mock_channel, self.mock_bot, max_length=100)

        with patch.object(
            sender, "_get_target_channel", return_value=self.mock_channel
        ):
            mock_send = AsyncMock()
            self.mock_channel.send = mock_send

            text = "This is a simple test message."
            result = await sender.send_text_chunks(text)

            # Verify message was sent
            assert mock_send.called
            call_arg = mock_send.call_args[0][0]
            assert "This is a simple test message." in call_arg

    @pytest.mark.asyncio
    async def test_send_text_chunks_long_text(self):
        """Test sending long text that requires splitting."""
        sender = MessageSender(self.mock_channel, self.mock_bot, max_length=50)

        with patch.object(
            sender, "_get_target_channel", return_value=self.mock_channel
        ):
            mock_send = AsyncMock()
            self.mock_channel.send = mock_send

            # Create text that will require multiple splits
            text = "A" * 100
            result = await sender.send_text_chunks(text)

            # Should have been called multiple times
            assert mock_send.call_count > 1

    @pytest.mark.asyncio
    async def test_send_text_chunks_empty_text(self):
        """Test sending empty text."""
        sender = MessageSender(self.mock_channel, self.mock_bot)

        with patch.object(
            sender, "_get_target_channel", return_value=self.mock_channel
        ):
            mock_send = AsyncMock()
            self.mock_channel.send = mock_send

            text = ""
            result = await sender.send_text_chunks(text)

            # Should not send any messages
            assert not mock_send.called
            assert result is None

    @pytest.mark.asyncio
    async def test_send_latex_image_success(self):
        """Test successful LaTeX image conversion."""
        sender = MessageSender(self.mock_channel, self.mock_bot)

        with patch.object(
            sender, "_get_target_channel", return_value=self.mock_channel
        ):
            with patch("utils.handlers.latex.convert_latex_to_png") as mock_convert:
                mock_convert.return_value = (io.BytesIO(b"fake_png"), True)

                mock_send = AsyncMock()
                self.mock_channel.send = mock_send

                latex_match = "```latex\nx = {-b \\pm \\sqrt{b^2 - 4ac} \\over 2a}\n```"
                result = await sender.send_latex_image(latex_match)

                # Verify conversion was attempted and message sent
                mock_convert.assert_called_once()
                assert mock_send.called

    @pytest.mark.asyncio
    async def test_send_latex_image_failure(self):
        """Test LaTeX image conversion failure."""
        sender = MessageSender(self.mock_channel, self.mock_bot)

        with patch.object(
            sender, "_get_target_channel", return_value=self.mock_channel
        ):
            with patch("utils.handlers.latex.convert_latex_to_png") as mock_convert:
                mock_convert.return_value = ("Failed to render LaTeX", False)

                mock_send = AsyncMock()
                self.mock_channel.send = mock_send

                latex_match = "```latex\ninvalid latex\n```"
                result = await sender.send_latex_image(latex_match)

                # Should send fallback message
                assert mock_send.called

    def test_clean_latex_simple(self):
        """Test LaTeX cleaning with simple case."""
        sender = MessageSender(self.mock_channel, self.mock_bot)

        # The function should handle both code fences and $ delimiters
        # Test with code fence and $ delimiters
        latex = "```latex\n$x + y = z\n```"
        cleaned = sender._clean_latex(latex)
        assert cleaned == "$x + y = z"  # Code fence removed, but $ delimiters kept

    def test_clean_latex_inline(self):
        """Test LaTeX cleaning with inline math."""
        sender = MessageSender(self.mock_channel, self.mock_bot)

        # The function should remove $ delimiters
        latex = "$x + y = z$"
        cleaned = sender._clean_latex(latex)
        assert cleaned == "x + y = z"  # $ delimiters removed

    def test_clean_latex_display(self):
        """Test LaTeX cleaning with display math."""
        sender = MessageSender(self.mock_channel, self.mock_bot)

        # The function should remove \\[ ... \\] delimiters and strip whitespace
        latex = "\\[ x + y = z \\]"
        cleaned = sender._clean_latex(latex)
        assert cleaned == "x + y = z"  # \\[ ... \\] removed and whitespace stripped
