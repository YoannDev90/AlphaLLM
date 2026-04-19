import io
import logging
import re
import textwrap
from typing import Any, List, Tuple
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

from config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

URL_REGEX = r'\[([^\]]+)\]\((https?://[^\s\)]+)\)|(https?://[^\s\)]+)'

def _extract_links_and_sanitize(text: str, current_links: List[str]) -> Tuple[str, List[str]]:
    """
    Substitutes URLs into placeholders like [n] (domain) and returns the links.
    Markdown links: [text](url) -> sanitized_text and url
    Plain URLs: url -> sanitized_url and url
    current_links: Shared list across the whole table to ensure incremental [n] indices.
    """
    def replacer(match):
        label, url_md, url_plain = match.groups()
        url = url_md or url_plain
        
        # Determine index based on global table links
        if url in current_links:
            idx = current_links.index(url) + 1
        else:
            current_links.append(url)
            idx = len(current_links)
        
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
            
        placeholder = f"[{idx}] ({domain})"
        return placeholder

    sanitized_text = re.sub(URL_REGEX, replacer, text)
    return sanitized_text, current_links

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


def _render_table_image(headers: List[str], rows: List[List[str]], alignments: List[str]) -> Tuple[io.BytesIO, List[str]]:
    """Render table as a high-resolution image and return buffer + extracted links."""
    # Sanitize content and collect links
    all_links = []
    
    sanitized_headers = []
    for h in headers:
        text, all_links = _extract_links_and_sanitize(h, all_links)
        sanitized_headers.append(text)
        
    sanitized_rows = []
    for row in rows:
        sanitized_row = []
        for cell in row:
            text, all_links = _extract_links_and_sanitize(str(cell), all_links)
            sanitized_row.append(text)
        sanitized_rows.append(sanitized_row)

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
    logger.debug(f"Rendering table with {len(sanitized_headers)} columns and {len(sanitized_rows)} rows")
    col_widths = _calc_col_widths(sanitized_headers, sanitized_rows, fonts["reg_reg"], padding)
    logger.debug(f"Calculated column widths: {col_widths}")

    processed_data = []
    for row in sanitized_rows:
        processed_row = []
        row_h = min_cell_height
        for i, cell in enumerate(row):
            wrapped = _wrap_text_with_formatting(str(cell).strip(), col_widths[i] - padding * 2, fonts)
            processed_row.append(wrapped)
            row_h = max(row_h, len(wrapped) * fonts["line_height"] + padding)
        processed_data.append((processed_row, row_h))

    total_width = sum(col_widths) + len(col_widths) + 1
    total_height = header_height + sum(h for _, h in processed_data) + len(processed_data) + 1
    logger.debug(f"Total image size: {total_width}x{total_height}")

    img = Image.new("RGB", (total_width, total_height), colors["bg"])
    
    with Pilmoji(img) as pilmoji:
        def draw_cell_text(x_start, y_start, width, height, wrapped_lines, align, is_header=False):
            total_text_h = len(wrapped_lines) * fonts["line_height"]
            start_y = y_start + (height - total_text_h) // 2
            
            for line_idx, line in enumerate(wrapped_lines):
                line_y = start_y + (line_idx * fonts["line_height"])
                
                # Render full line as a single string to let Pilmoji handle layout and emojis perfectly
                line_text = " ".join(w for s, w in line)
                if not line_text.strip():
                    continue
                
                # Use font based on the first style of the line or header status
                # Safe check if line is empty (shouldn't happen with the strip check above but anyway)
                if not line:
                    continue
                    
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
        for header, width, align in zip(sanitized_headers, col_widths, alignments):
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
    logger.debug(f"Table image rendered successfully, size: {buffer.getbuffer().nbytes} bytes")
    # Return unique links, preserving order if possible
    unique_links = []
    seen = set()
    for link in all_links:
        if link not in seen:
            unique_links.append(link)
            seen.add(link)
            
    return buffer, unique_links



TABLE_IMAGE_PLACEHOLDER = "TABLE_IMAGE_RENDERED_PLACEHOLDER"

def detect_and_convert_tables(text: str) -> tuple[str, list[io.BytesIO], list[dict]]:
    """Detect Markdown tables and render them as images with alignment support.
    Returns: (modified_text, list_of_images, list_of_table_data)
    """
    try:
        # Pre-process: detect and isolate markdown code blocks containing tables
        code_block_pattern = re.compile(r"```(?:markdown)?\n((?:\|.*\|(?:\n|$))+)```", re.MULTILINE)
        
        table_images = []
        table_data_list = []
        
        def replace_table_block(match):
            logger.debug("Detected markdown table inside code block")
            table_content = match.group(1).strip()
            lines = table_content.split("\n")
            headers, rows, alignments = [], [], []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line.startswith("|") or not line.endswith("|"):
                    i += 1
                    continue
                
                parts = [p.strip() for p in line[1:-1].split("|")]
                
                # Check for separator line
                if all(re.match(r"^[\s\-\:]+$", p) for p in parts) and parts:
                    for p in parts:
                        if p.startswith(":") and p.endswith(":"): alignments.append("center")
                        elif p.endswith(":"): alignments.append("right")
                        else: alignments.append("left")
                elif not headers:
                    headers = parts
                else:
                    rows.append(parts)
                i += 1
                
            if headers and rows:
                num_cols = len(headers)
                while len(alignments) < num_cols: alignments.append("left")
                alignments = alignments[:num_cols]
                
                # Normalize rows
                normalized_rows = []
                for r in rows:
                    if len(r) < num_cols:
                        r.extend([""] * (num_cols - len(r)))
                    normalized_rows.append(r[:num_cols])
                
                try:
                    img_buffer, links = _render_table_image(headers, normalized_rows, alignments)
                    table_images.append(img_buffer)
                    table_data_list.append({
                        "id": len(table_images) - 1,
                        "headers": headers,
                        "rows": normalized_rows,
                        "links": links
                    })
                    return f"\n{TABLE_IMAGE_PLACEHOLDER}_{len(table_images)-1}\n"
                except Exception as e:
                    logger.error(f"Table render failed: {e}")
                    return match.group(0)
            return match.group(0)

        text = code_block_pattern.sub(replace_table_block, text)

        # Legacy direct table detection (for tables not in code blocks)
        lines = text.split("\n")
        output_lines, i = [], 0

        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("|") and line.endswith("|"):
                logger.debug(f"Detected potential table start at line {i}")
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
                    num_cols = len(headers)
                    rows = []
                    for row_str in potential_table[1:]:
                        cells = [c.strip() for c in row_str.strip()[1:-1].split("|")]
                        # Pad or truncate row to match header column count
                        if len(cells) < num_cols:
                            cells.extend([""] * (num_cols - len(cells)))
                        elif len(cells) > num_cols:
                            cells = cells[:num_cols]
                        rows.append(cells)
                    
                    while len(alignments) < num_cols: alignments.append("left")
                    if len(alignments) > num_cols:
                        alignments = alignments[:num_cols]
                    
                    try:
                        img_buffer, links = _render_table_image(headers, rows, alignments)
                        table_images.append(img_buffer)
                        table_data_list.append({
                            "id": len(table_images) - 1,
                            "headers": headers,
                            "rows": rows,
                            "links": links
                        })
                        output_lines.append(f"\n{TABLE_IMAGE_PLACEHOLDER}_{len(table_images)-1}\n")
                    except Exception as e:
                        logger.error(f"Table render failed: {e}")
                        output_lines.extend(potential_table)
                    continue
            output_lines.append(lines[i])
            i += 1
        return "\n".join(output_lines), table_images, table_data_list
    except Exception as exc:
        logger.error(f"Table detection failed: {exc}")
        return text, [], []
    except Exception as exc:
        logger.error(f"Table detection failed: {exc}")
        return text, []

