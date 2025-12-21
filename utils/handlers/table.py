import logging
import re
import textwrap
from typing import List

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"
    "\u3030"
    "]+",
    flags=re.UNICODE,
)


def clean_cell_content(cell: str) -> str:
    """Strip formatting and emojis from a Markdown table cell."""
    cell = re.sub(r"\*\*(.*?)\*\*", r"\1", cell)
    cell = re.sub(r"<br\s*/?>", "\n", cell, flags=re.IGNORECASE)
    cell = re.sub(r"<[^>]+>", "", cell)
    cell = EMOJI_PATTERN.sub("", cell)
    cell = re.sub(r"\s+", " ", cell)
    return cell.strip()


def markdown_to_ascii_table(markdown_table: str, max_line_length: int = 100) -> str:
    """Convert a Markdown table into an ASCII table."""
    try:
        lines = [line.strip() for line in markdown_table.strip().split("\n") if line.strip()]
        if len(lines) < 2:
            return markdown_table

        rows: List[List[str]] = []
        separator_index = -1

        for i, line in enumerate(lines):
            if line.startswith("|") and line.endswith("|"):
                if re.match(r"^\|[\s\-\:\|]*\|$", line):
                    separator_index = i
                    continue
                cells = [clean_cell_content(cell.strip()) for cell in line[1:-1].split("|")]
                rows.append(cells)

        if not rows or separator_index == -1:
            return markdown_table

        max_cols = max(len(row) for row in rows) if rows else 0
        natural_col_widths = [0] * max_cols

        for row in rows:
            for idx, cell in enumerate(row):
                if idx >= max_cols:
                    continue
                cell_lines = cell.split("\n")
                max_line_width = max(len(line) for line in cell_lines) if cell_lines else 0
                natural_col_widths[idx] = max(natural_col_widths[idx], max_line_width)

        total_natural_width = sum(natural_col_widths) + (3 * max_cols) + 1

        if total_natural_width > max_line_length:
            available_width = max_line_length - (3 * max_cols) - 1
            total_content_width = sum(natural_col_widths)
            if total_content_width > 0:
                ratio = available_width / total_content_width
                col_widths = [max(1, int(width * ratio)) for width in natural_col_widths]
            else:
                col_widths = [1] * max_cols
        else:
            col_widths = natural_col_widths

        def build_separator(char: str = '-') -> str:
            return "+" + "+".join(char * (width + 2) for width in col_widths) + "+"

        ascii_lines = [build_separator('=')]

        if rows:
            header_cells = rows[0] + [""] * (max_cols - len(rows[0]))
            wrapped_headers: List[List[str]] = []
            for idx, cell in enumerate(header_cells):
                width = col_widths[idx] if idx < len(col_widths) else 1
                wrapped_headers.append(textwrap.wrap(cell.upper(), width=width) or [cell.upper()])
            max_wrap = max(len(w) for w in wrapped_headers)
            for i in range(max_wrap):
                row_cells = [wrapped_headers[idx][i] if i < len(wrapped_headers[idx]) else "" for idx in range(len(col_widths))]
                row_text = "|" + "|".join(f" {cell:<{col_widths[idx]}} " for idx, cell in enumerate(row_cells)) + "|"
                ascii_lines.append(row_text)
            ascii_lines.append(build_separator('='))

        for row in rows[1:]:
            wrapped_cells: List[List[str]] = []
            for idx in range(len(col_widths)):
                cell = row[idx] if idx < len(row) else ""
                width = col_widths[idx]
                wrapped_cells.append(textwrap.wrap(cell, width=width) or [cell])
            max_wrap = max(len(w) for w in wrapped_cells)
            for i in range(max_wrap):
                row_cells = [wrapped_cells[idx][i] if i < len(wrapped_cells[idx]) else "" for idx in range(len(col_widths))]
                row_text = "|" + "|".join(f" {cell:<{col_widths[idx]}} " for idx, cell in enumerate(row_cells)) + "|"
                ascii_lines.append(row_text)
            ascii_lines.append(build_separator())

        return "\n".join(ascii_lines)
    except Exception as exc:
        logger.error(f"Table conversion failed {exc}")
        return markdown_table


def detect_and_convert_tables(text: str, max_line_length: int = 100) -> str:
    """Convert Markdown tables inside the text to ASCII snapshots."""
    try:
        lines = text.split("\n")
        output_lines: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("|") and line.strip().endswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                if len(table_lines) >= 2:
                    ascii_table = markdown_to_ascii_table("\n".join(table_lines), max_line_length)
                    output_lines.append(f"```\n{ascii_table}\n```")
                    continue
                output_lines.extend(table_lines)
                continue
            output_lines.append(line)
            i += 1

        return "\n".join(output_lines)
    except Exception as exc:
        logger.error(f"Table detection failed {exc}")
        return text
