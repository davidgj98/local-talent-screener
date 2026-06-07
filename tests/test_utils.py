from __future__ import annotations

import pytest

from utils import extract_text_from_pdf


class TestExtractTextFromPdf:
    def test_none_raises(self):
        with pytest.raises(ValueError):
            extract_text_from_pdf(None)

    def test_empty_bytes_raises(self):
        with pytest.raises(ValueError, match="empty"):
            extract_text_from_pdf(b"")

    def test_invalid_bytes_returns_string(self):
        text = extract_text_from_pdf(b"not a pdf at all")
        assert isinstance(text, str)

    def test_valid_minimal_pdf(self, minimal_pdf):
        text = extract_text_from_pdf(minimal_pdf)
        assert isinstance(text, str)
