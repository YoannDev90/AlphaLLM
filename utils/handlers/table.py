import io
import logging
import re
import textwrap
from typing import Any, List

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def _get_font(size: int, bold: bool = False, italic: bool = False):
    """Load Noto Sans font (regular, bold, italic, or bold-italic)."""
    try:
        if bold and italic:
            path = "assets/fonts/NotoSans-BoldItalic.ttf"
        elif bold:
            path = "assets/fonts/NotoSans-Bold.ttf"
        elif italic:
            path = "assets/fonts/NotoSans-Italic.ttf"
        else:
            path = "assets/fonts/NotoSans-Regular.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# Constants for rendering
EMOJI_BUFFER = 12
SEGMENT_GAP = "  "
COLUMN_MAX_WIDTH = 1200


def _calc_col_widths(headers: List[str], rows: List[List[str]], font: ImageFont.FreeTypeFont, padding: int) -> List[int]:
    """Calculate column widths based on content and font."""
    img = Image.new("RGB", (1, 1))
    widths = []

    with Pilmoji(img) as pilmoji:
        for i, header in enumerate(headers):
            # Use Pilmoji to measure width to stay consistent with rendering
            max_w = pilmoji.draw.textlength(str(header), font=font) + padding * 2

            # Check all cells in this column
            for row in rows:
                if i < len(row):
                    cell_text = str(row[i])
                    # Handle multi-line text by splitting and finding longest line
                    for line in cell_text.split("\n"):
                        raw_w = pilmoji.draw.textlength(line, font=font)
                        # Add buffer for emojis
                        if any(ord(c) > 0xFFFF for c in line):
                            raw_w += EMOJI_BUFFER
                        
                        cell_w = raw_w + padding * 2
                        max_w = max(max_w, cell_w)

            widths.append(int(min(max_w, COLUMN_MAX_WIDTH)))

    return widths


def _parse_text_formatting(text: str):
    """Parse text with **bold**, *italic*, and __underline__ formatting."""
    # Pattern to catch bold-italic (***), bold (**), italic (*), and underline (__)
    pattern = r"(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|__.*?__)"
    parts = re.split(pattern, text)
    segments = []
    
    for part in parts:
        if not part:
            continue
        
        style = {"bold": False, "italic": False, "underline": False}
        content = part
        
        if part.startswith("***") and part.endswith("***"):
            style["bold"] = style["italic"] = True
            content = part[3:-3]
        elif part.startswith("**") and part.endswith("**"):
            style["bold"] = True
            content = part[2:-2]
        elif part.startswith("*") and part.endswith("*"):
            style["italic"] = True
            content = part[1:-1]
        elif part.startswith("__") and part.endswith("__"):
            style["underline"] = True
            content = part[2:-2]
            
        segments.append((style, content))
    return segments


def _wrap_text_with_formatting(text: str, max_width: int, fonts: dict) -> list:
    """Wrap text with formatting based on pixel width."""
    if not text:
        return [[({"bold": False, "italic": False, "underline": False}, "")]]

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    segments = _parse_text_formatting(text)
    lines = []
    current_line = []
    current_width = 0

    for style, segment_text in segments:
        f = fonts.get(f"{'bold' if style['bold'] else 'reg'}_{'italic' if style['italic'] else 'reg'}", fonts["cell"])
        words = segment_text.split()
        for word in words:
            word_width = draw.textlength(word, font=f)
            space_width = draw.textlength(" ", font=f)
            space_needed = space_width if current_line else 0

            if current_width + word_width + space_needed <= max_width:
                current_line.append((style, word))
                current_width += word_width + space_needed
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [(style, word)]
                current_width = word_width + space_needed

    if current_line:
        lines.append(current_line)
    return lines


def _render_table_image(headers: List[str], rows: List[List[str]], alignments: List[str]) -> io.BytesIO:
    """Render table as a high-resolution image with formatting and alignment."""
    font_size = 42
    fonts = {
        "reg_reg": _get_font(font_size),
        "bold_reg": _get_font(font_size, bold=True),
        "reg_italic": _get_font(font_size, italic=True),
        "bold_italic": _get_font(font_size, bold=True, italic=True),
        "header_reg": _get_font(font_size + 6),
        "header_bold": _get_font(font_size + 6, bold=True),
        "cell": _get_font(font_size),
        "line_height": font_size + 12,
    }

    colors = {
        "bg": (7, 7, 9),         # Discord theme dark
        "header_bg": (28, 28, 32), # Slightly lighter for header
        "row_bg": (7, 7, 9),
        "row_bg_alt": (28, 28, 32),
        "border": (60, 60, 65),
        "text": (255, 255, 255),
    }

    padding, header_height, min_cell_height = 36, 120, 84
    col_widths = _calc_col_widths(headers, rows, fonts["reg_reg"], padding)

    processed_data = []
    for row in rows:
        processed_row = []
        row_h = min_cell_height
        for i, cell in enumerate(row):
            wrapped = _wrap_text_with_formatting(str(cell).strip(), col_widths[i] - padding * 2, fonts)
            processed_row.append(wrapped)
            row_h = max(row_h, len(wrapped) * fonts["line_height"] + padding)
        processed_data.append((processed_row, row_h))

    total_width = sum(col_widths) + len(col_widths) + 1
    total_height = header_height + sum(h for _, h in processed_data) + len(processed_data) + 1

    img = Image.new("RGB", (total_width, total_height), colors["bg"])
    
    with Pilmoji(img) as pilmoji:
        def draw_cell_text(x_start, y_start, width, height, wrapped_lines, align, is_header=False):
            total_text_h = len(wrapped_lines) * fonts["line_height"]
            start_y = y_start + (height - total_text_h) // 2
            
            for line_idx, line in enumerate(wrapped_lines):
                line_y = start_y + (line_idx * fonts["line_height"])
                
                # Render full line as a single string to let Pilmoji handle layout and emojis perfectly
                line_text = " ".join(w for s, w in line)
                
                # Use font based on the first style of the line or header status
                first_style, _ = line[0]
                if is_header:
                    f = fonts["header_bold" if first_style["bold"] else "header_reg"]
                else:
                    f = fonts[f"{'bold' if first_style['bold'] else 'reg'}_{'italic' if first_style['italic'] else 'reg'}"]

                line_w = pilmoji.draw.textlength(line_text, font=f)

                if align == "center":
                    curr_x = x_start + (width - line_w) // 2
                elif align == "right":
                    curr_x = x_start + width - line_w - padding
                else:
                    curr_x = x_start + padding

                pilmoji.text((curr_x, line_y), line_text, fill=colors["text"], font=f)

        draw = ImageDraw.Draw(img)
        # Draw Header
        x = 0
        for header, width, align in zip(headers, col_widths, alignments):
            draw.rectangle([x, 0, x + width, header_height], fill=colors["header_bg"], outline=colors["border"])
            header_lines = _wrap_text_with_formatting(header, width - padding * 2, fonts)
            draw_cell_text(x, 0, width, header_height, header_lines, align, is_header=True)
            x += width + 1

        # Draw Rows
        y = header_height + 1
        for row_idx, (processed_row, row_h) in enumerate(processed_data):
            x = 0
            row_bg = colors["row_bg_alt"] if row_idx % 2 else colors["row_bg"]
            for wrapped_lines, width, align in zip(processed_row, col_widths, alignments):
                draw.rectangle([x, y, x + width, y + row_h], fill=row_bg, outline=colors["border"])
                draw_cell_text(x, y, width, row_h, wrapped_lines, align)
                x += width + 1
            y += row_h + 1

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", dpi=(300, 300))
    buffer.seek(0)
    return buffer



def detect_and_convert_tables(text: str) -> str:
    """Detect Markdown tables and render them as images with alignment support."""
    try:
        lines = text.split("\n")
        output_lines, i = [], 0

        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("|") and line.endswith("|"):
                potential_table, alignments = [], []
                
                # Group table lines
                while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    l_strip = lines[i].strip()
                    if re.match(r"^\|[\s\-\:\|]*\|$", l_strip):
                        # Parse alignments: :--- center, ---: right, :---: center (markdown spec)
                        for c in [c.strip() for c in l_strip[1:-1].split("|")]:
                            if c.startswith(":") and c.endswith(":"): alignments.append("center")
                            elif c.endswith(":"): alignments.append("right")
                            else: alignments.append("left")
                    else:
                        potential_table.append(lines[i])
                    i += 1
                
                if len(potential_table) >= 2:
                    headers = [c.strip() for c in potential_table[0].strip()[1:-1].split("|")]
                    rows = [[c.strip() for c in row.strip()[1:-1].split("|")] for row in potential_table[1:]]
                    while len(alignments) < len(headers): alignments.append("left")
                    
                    try:
                        # Logic to attach the image would go here in the real bot
                        # For now we just keep the marker
                        output_lines.append("```\n[Table Rendered as Image]\n```")
                    except Exception as e:
                        logger.error(f"Table render failed: {e}")
                        output_lines.extend(potential_table)
                    continue
            output_lines.append(lines[i])
            i += 1
        return "\n".join(output_lines)
    except Exception as exc:
        logger.error(f"Table detection failed: {exc}")
        return text

