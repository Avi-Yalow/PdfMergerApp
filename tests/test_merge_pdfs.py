"""Tests for the merge_pdfs CLI module."""

import io
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from merge_pdfs import merge_pdfs


def _make_pdf_file(tmp_path: Path, name: str, num_pages: int = 1) -> Path:
    """Write a minimal PDF to tmp_path and return its path."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    filepath = tmp_path / name
    with open(filepath, "wb") as f:
        writer.write(f)
    return filepath


class TestMergePdfs:
    def test_merge_creates_output(self, tmp_path):
        f1 = _make_pdf_file(tmp_path, "a.pdf", 2)
        f2 = _make_pdf_file(tmp_path, "b.pdf", 3)
        output = tmp_path / "out.pdf"
        merge_pdfs([str(f1), str(f2)], str(output))
        assert output.exists()
        reader = PdfReader(str(output))
        assert len(reader.pages) == 5

    def test_merge_file_not_found(self, tmp_path):
        with pytest.raises(SystemExit):
            merge_pdfs([str(tmp_path / "nonexistent.pdf")], str(tmp_path / "out.pdf"))
