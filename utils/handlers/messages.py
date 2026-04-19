import logging
import re
from typing import Optional, List, Any

import discord
from config import LOGGER_NAME
from utils.handlers.codeblock import (send_code_block,
                                      send_code_block_with_return)
from utils.handlers.latex import (LATEX_TO_EMOJI, detect_latex)
from utils.handlers.table import (TABLE_IMAGE_PLACEHOLDER,
                                    detect_and_convert_tables)

logger = logging.getLogger(LOGGER_NAME)

class MessageSender:
    """
    Handles sending and splitting of complex Discord messages including:
    - Long text splitting
    - Code blocks preservation
    - LaTeX to image/emoji conversion
    - Table conversion to images
    """

    def __init__(self, channel: discord.abc.Messageable, bot: Optional[discord.Client] = None, max_length: int = 2000):
        self.channel = channel
        self.bot = bot
        self.max_length = max_length

    def _get_target_channel(self) -> discord.abc.Messageable:
        """Returns the actual discord channel object."""
        if self.bot and hasattr(self.channel, 'id'):
            return self.bot.get_channel(self.channel.id) or self.channel
        return self.channel

    async def send_text_chunks(self, text: str) -> Optional[discord.Message]:
        """Sends plain text in chunks, returning the last message sent."""
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
                    chunk = line[i:i + self.max_length]
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
        """Renders LaTeX and sends it as an image."""
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
        """Processes text for LaTeX and sends parts accordingly."""
        matches = detect_latex(text)
        if not matches:
            return await self.send_text_chunks(text)

        current_text = ""
        last_end = 0
        last_message = None
        
        for match in matches:
            start = text.find(match, last_end)
            if start == -1: continue
            
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

    async def process_and_send(self, response: str) -> Optional[discord.Message]:
        """Main entry point for sending complex responses."""
        response, table_images = detect_and_convert_tables(response)
        pattern = re.compile(f"({TABLE_IMAGE_PLACEHOLDER}_\\d+)|(```[\\s\\S]*?```)")
        parts = pattern.split(response)
        parts = [p for p in parts if p is not None and (p.strip() or p.startswith(TABLE_IMAGE_PLACEHOLDER))]
        
        target = self._get_target_channel()
        last_message = None

        for part in parts:
            if part.startswith(TABLE_IMAGE_PLACEHOLDER):
                try:
                    idx = int(part.split("_")[-1])
                    img_buffer = table_images[idx]
                    img_buffer.seek(0)
                    file = discord.File(fp=img_buffer, filename="table.png")
                    last_message = await target.send(file=file)
                except (IndexError, ValueError):
                    pass
            elif part.startswith("```") and part.endswith("```"):
                last_message = await send_code_block_with_return(target, part, self.max_length, bot=self.bot)
            else:
                last_message = await self.send_text_with_latex(part)

        return last_message

    async def send_with_view(self, response: str, original_question: str, model: Any, response_data: Any) -> Optional[discord.Message]:
        """Sends a complex response and attaches a MessageView to the last message."""
        from utils.views.message import MessageView
        
        last_message = await self.process_and_send(response)
        
        if last_message:
            view = MessageView(original_question, model, response_data, self.bot)
            try:
                await last_message.edit(view=view)
                view.message = last_message
            except Exception as e:
                logger.error(f"Failed to edit message with view: {e}")
        
        return last_message
