"""Unit Tests for wikidpad2markdown using pytest
"""

from pathlib import Path
import pytest

from wikidpad2markdown import Wikidpad2Markdown

def test_formatter_from_sample_pages():
    """Does a markdown transform test of _sample_pages/main.wiki against _sample_pages/main.md
    """
    wiki_path = Path( "./_sample_pages/main.wiki")
    md_path   = Path( "./_sample_pages/main.md")

    markdown_expected = md_path.read_text()
    markdown = Wikidpad2Markdown( wiki_path.read_text(), remove_remaining_wikidpad=False)

    if False:
        md_test_file = Path( "./tests/main.test.md")
        md_test_file.write_text( markdown)

    assert markdown.strip() == markdown_expected.strip()