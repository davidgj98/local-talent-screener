from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Union

from markitdown import MarkItDown


def extract_text_from_pdf(pdf_path: Union[str, Path, bytes, None]) -> str:
    if pdf_path is None:
        raise ValueError("PDF is not available. Please re-upload the file.")
    try:
        md = MarkItDown()

        if isinstance(pdf_path, bytes):
            if not pdf_path:
                raise ValueError("PDF file is empty")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_path)
                tmp_path = tmp.name
            try:
                result = md.convert(tmp_path)
                return result.text_content.strip()
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        else:
            result = md.convert(str(pdf_path))
            return result.text_content.strip()
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {e}") from e
