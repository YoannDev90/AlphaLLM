"""Helpers for sending long or formatted Discord messages."""

import logging
import re
from typing import Any, List, Optional, Tuple

import discord

from core.config import cfg
from utils.logger import get_logger

logger = get_logger()

from utils.handlers.codeblock import send_code_block, send_code_block_with_return
from utils.handlers.latex import LATEX_TO_EMOJI, detect_latex
from utils.handlers.table import TABLE_IMAGE_PLACEHOLDER, detect_and_convert_tables


class MessageSender:
    """Send text, LaTeX and table-rich responses to Discord channels.

    Attributes
    ----------
    channel : discord.abc.Messageable
        Target channel-like object used for sending messages.
    bot : Optional[discord.Client]
        Optional bot instance used to resolve the live channel object.
    max_length : int
        Maximum number of characters per message chunk.
    """

    def __init__(
        self,
        channel: discord.abc.Messageable,
        bot: Optional[discord.Client] = None,
        max_length: int = 2000,
    ):
        """Initialize a message sender.

        Parameters
        ----------
        channel : discord.abc.Messageable
            Channel-like object to send messages to.
        bot : Optional[discord.Client]
            Optional bot instance used to resolve the current channel. Default is None.
        max_length : int
            Maximum message chunk size (default: 2000).
        """
        self.channel = channel
        self.bot = bot
        self.max_length = max_length

    def _get_target_channel(self) -> discord.abc.Messageable:
        """Return the most up-to-date channel object available.

        Returns
        -------
        discord.abc.Messageable
            Resolved channel object.
        """
        if self.bot and hasattr(self.channel, "id"):
            return self.bot.get_channel(self.channel.id) or self.channel
        return self.channel

    async def send_text_chunks(self, text: str) -> Optional[discord.Message]:
        """Send plain text as one or more Discord messages.

        Parameters
        ----------
        text : str
            Text to send.

        Returns
        -------
        Optional[discord.Message]
            Last message sent, or None if text was empty.
        """
        if not text.strip():
            return None
        target = self._get_target_channel()
        lines = text.splitlines(keepends=True)
        current_message = ""
        last_message = None
        for line in lines:
            if len(line) > self.max_length:
                if current_message:
                    last_message = await target.send(current_message.rstrip())
                    current_message = ""
                for i in range(0, len(line), self.max_length):
                    chunk = line[i : i + self.max_length]
                    last_message = await target.send(chunk.rstrip())
            elif len(current_message) + len(line) > self.max_length:
                if current_message:
                    last_message = await target.send(current_message.rstrip())
                current_message = line
            else:
                current_message += line
        if current_message.strip():
            last_message = await target.send(current_message.rstrip())
        return last_message

    async def send_latex_image(self, latex_match: str) -> Optional[discord.Message]:
        """Render and send a LaTeX expression as an image when possible.

        Parameters
        ----------
        latex_match : str
            Raw LaTeX text or match content.

        Returns
        -------
        Optional[discord.Message]
            Message created by Discord, or None on failure.
        """
        from utils.handlers.latex import convert_latex_to_png

        latex = self._clean_latex(latex_match)
        result, success = convert_latex_to_png(latex)
        target = self._get_target_channel()
        if success:
            if isinstance(result, str):
                return await target.send(result)
            file = discord.File(result, filename="formula.png")
            return await target.send(file=file)
        latex_display = latex[:100] + "..." if len(latex) > 100 else latex
        return await target.send(f"Failed to render LaTeX: {latex_display}")

    def _clean_latex(self, latex: str) -> str:
        """Strip wrappers such as code fences and `$...$` from LaTeX text.

        Parameters
        ----------
        latex : str
            Raw LaTeX string.

        Returns
        -------
        str
            Cleaned LaTeX content.
        """
        latex = latex.strip()
        if latex.startswith("```") and latex.endswith("```"):
            lines = latex.split("\n")
            if len(lines) >= 3 and lines[-1] == "```":
                latex = "\n".join(lines[1:-1])
        if latex.startswith("$") and latex.endswith("$"):
            latex = latex[1:-1]
        if latex.startswith(r"\[") and latex.endswith(r"\]"):
            latex = latex[2:-2]
        return latex

    async def send_text_with_latex(self, text: str) -> Optional[discord.Message]:
        """Send text while converting LaTeX fragments to emoji or images.

        Parameters
        ----------
        text : str
            Text containing optional LaTeX fragments.

        Returns
        -------
        Optional[discord.Message]
            Last Discord message sent, or None.
        """
        matches = detect_latex(text)
        if not matches:
            return await self.send_text_chunks(text)
        current_text = ""
        last_end = 0
        last_message = None
        for match in matches:
            start = text.find(match, last_end)
            if start == -1:
                continue
            current_text += text[last_end:start]
            latex = self._clean_latex(match)
            if latex in LATEX_TO_EMOJI:
                current_text += LATEX_TO_EMOJI[latex]
            else:
                if current_text:
                    last_message = await self.send_text_chunks(current_text)
                    current_text = ""
                last_message = await self.send_latex_image(match)
            last_end = start + len(match)
        current_text += text[last_end:]
        if current_text:
            last_message = await self.send_text_chunks(current_text)
        return last_message

    async def process_and_send(
        self, response: str
    ) -> Tuple[Optional[discord.Message], List[dict]]:
        """Process a response and send text, tables and code blocks.

        Parameters
        ----------
        response : str
            Full model response to send.

        Returns
        -------
        Tuple[Optional[discord.Message], List[dict]]
            Last message sent and table metadata extracted from the response.
        """
        response, table_images, table_data = detect_and_convert_tables(response)
        placeholder_escaped = re.escape(TABLE_IMAGE_PLACEHOLDER)
        pattern = re.compile(f"({placeholder_escaped}_\\d+__)|(```[\\s\\S]*?```)")
        parts = [p for p in pattern.split(response) if p is not None]
        target = self._get_target_channel()
        last_message = None
        for part in parts:
            if not part:
                continue
            if part.startswith(TABLE_IMAGE_PLACEHOLDER) and part.endswith("__"):
                try:
                    idx_str = part[len(TABLE_IMAGE_PLACEHOLDER) + 1 : -2]
                    idx = int(idx_str)
                    if idx < len(table_images):
                        img_buffer = table_images[idx]
                        img_buffer.seek(0)
                        file = discord.File(fp=img_buffer, filename=f"table_{idx}.png")
                        last_message = await target.send(file=file)
                    else:
                        last_message = await self.send_text_with_latex(part)
                except Exception as e:
                    logger.error(f"Failed to send table message: {e}")
                    last_message = await self.send_text_with_latex(part)
            elif part.startswith("```") and part.endswith("```"):
                if TABLE_IMAGE_PLACEHOLDER not in part:
                    last_message = await send_code_block_with_return(
                        target, part, self.max_length, bot=self.bot
                    )
            else:
                last_message = await self.send_text_with_latex(part)
        return last_message, table_data
