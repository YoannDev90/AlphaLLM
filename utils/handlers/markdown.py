import os
import tempfile
from typing import Optional
from markitdown import MarkItDown
import logging
from config import LOGGER_NAME

class MarkdownConverter:
    def __init__(self) -> None:
        self._converter = MarkItDown()
        self._logger = logging.getLogger(LOGGER_NAME)

    def convert_to_markdown(self, file_path: str) -> Optional[str]:
        try:
            result = self._converter.convert(file_path)
            content = result.text_content
            if not content:
                return None

            # Essai de détecter si c'est du JSON
            import json
            try:
                json.loads(content)
                # Si c'est du JSON valide, formater en Markdown
                return f"```json\n{content}\n```"
            except json.JSONDecodeError:
                pass

            return content
        except Exception as exc:
            self._logger.error("Markdown conversion failed %s", exc)
            return None

    def convert_file_like(self, file_content: bytes, suffix: str = "") -> Optional[str]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        try:
            return self.convert_to_markdown(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except Exception as exc:
                self._logger.warning("Temporary file cleanup failed %s", exc)
