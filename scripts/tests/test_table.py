"""Test cases for table handling."""

import io
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.handlers.table import detect_and_convert_tables


class TestTableHandlers:
    """Test cases for table handling."""

    def test_detect_and_convert_tables_basic(self):
        """Test basic table detection and conversion."""
        text = """Here's a table:

```markdown
| Name  | Age | City      |
|-------|-----|-----------|
| Alice | 30  | New York  |
| Bob   | 25  | San Francisco |
```

More text here."""

        new_text, table_images, table_data = detect_and_convert_tables(text)

        # Should have converted table to image
        assert len(table_images) == 1
        assert len(table_data) == 1

        # Should replace table with placeholder
        assert "__TABLE_IMG_0__" in new_text
        assert "```markdown" not in new_text

        # Check table data structure
        assert table_data[0]["headers"] == ["Name", "Age", "City"]
        assert table_data[0]["rows"] == [["Alice", "30", "New York"], ["Bob", "25", "San Francisco"]]

    def test_detect_and_convert_tables_no_table(self):
        """Test text without tables."""
        text = "This is just plain text without any tables."
        new_text, table_images, table_data = detect_and_convert_tables(text)

        # Should not detect any tables
        assert len(table_images) == 0
        assert len(table_data) == 0
        assert new_text == text

    def test_detect_and_convert_tables_multiline(self):
        """Test table with multiline content."""
        text = """```markdown
| Header1 | Header2 |
|---------|---------|
| Cell1   | Cell2   |
| Cell3   |
```"""

        new_text, table_images, table_data = detect_and_convert_tables(text)

        # Should handle multiline cells
        assert len(table_images) == 1
        assert len(table_data) == 1

    def test_extract_links_and_sanitize(self):
        """Test link extraction and sanitization."""
        from utils.handlers.table import _extract_links_and_sanitize

        text = "Check out [Google](https://google.com) and https://github.com"
        current_links = []
        sanitized, updated_links = _extract_links_and_sanitize(text, current_links)

        # Should replace links with numbered references
        assert "[1] (google.com)" in sanitized
        assert "[2] (github.com)" in sanitized
        assert len(updated_links) == 2
        assert "https://google.com" in updated_links
        assert "https://github.com" in updated_links

    def test_detect_and_convert_tables_with_links(self):
        """Test table conversion with links."""
        text = """```markdown
| Name  | URL            |
|-------|----------------|
| Test  | https://test.com |
```"""

        new_text, table_images, table_data = detect_and_convert_tables(text)

        assert len(table_images) == 1
        assert len(table_data) == 1
        assert "https://test.com" in table_data[0]["links"]