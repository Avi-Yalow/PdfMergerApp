"""Tests for pdf_operations module."""

import io

import pytest
from pypdf import PdfReader, PdfWriter

from pdf_operations import (
    merge_pdf_streams,
    split_pdf_stream_custom,
    split_pdf_stream_uniform,
)


def _make_pdf(num_pages: int = 1) -> io.BytesIO:
    """Create a minimal valid PDF with the given number of pages."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf


class TestMergePdfStreams:
    def test_merge_two_single_page_pdfs(self):
        pdf1 = _make_pdf(1)
        pdf2 = _make_pdf(1)
        result = merge_pdf_streams([pdf1, pdf2])
        reader = PdfReader(result)
        assert len(reader.pages) == 2

    def test_merge_preserves_page_order(self):
        pdf1 = _make_pdf(3)
        pdf2 = _make_pdf(2)
        result = merge_pdf_streams([pdf1, pdf2])
        reader = PdfReader(result)
        assert len(reader.pages) == 5

    def test_merge_single_file(self):
        pdf = _make_pdf(4)
        result = merge_pdf_streams([pdf])
        reader = PdfReader(result)
        assert len(reader.pages) == 4

    def test_merge_many_files(self):
        streams = [_make_pdf(1) for _ in range(10)]
        result = merge_pdf_streams(streams)
        reader = PdfReader(result)
        assert len(reader.pages) == 10

    def test_merge_empty_list(self):
        result = merge_pdf_streams([])
        reader = PdfReader(result)
        assert len(reader.pages) == 0


class TestSplitPdfStreamUniform:
    def test_split_into_single_pages(self):
        pdf = _make_pdf(4)
        parts = split_pdf_stream_uniform(pdf, 1)
        assert len(parts) == 4
        for name, buf in parts:
            reader = PdfReader(buf)
            assert len(reader.pages) == 1

    def test_split_into_two_page_chunks(self):
        pdf = _make_pdf(6)
        parts = split_pdf_stream_uniform(pdf, 2)
        assert len(parts) == 3
        for _, buf in parts:
            reader = PdfReader(buf)
            assert len(reader.pages) == 2

    def test_split_uneven_last_chunk(self):
        pdf = _make_pdf(5)
        parts = split_pdf_stream_uniform(pdf, 2)
        assert len(parts) == 3
        assert len(PdfReader(parts[0][1]).pages) == 2
        assert len(PdfReader(parts[1][1]).pages) == 2
        assert len(PdfReader(parts[2][1]).pages) == 1

    def test_split_pages_per_file_exceeds_total(self):
        pdf = _make_pdf(3)
        parts = split_pdf_stream_uniform(pdf, 10)
        assert len(parts) == 1
        assert len(PdfReader(parts[0][1]).pages) == 3

    def test_split_filenames(self):
        pdf = _make_pdf(3)
        parts = split_pdf_stream_uniform(pdf, 1)
        names = [name for name, _ in parts]
        assert names == ["split_part_1.pdf", "split_part_2.pdf", "split_part_3.pdf"]


class TestSplitPdfStreamCustom:
    def test_custom_split_exact_counts(self):
        pdf = _make_pdf(5)
        parts = split_pdf_stream_custom(pdf, [2, 3])
        assert len(parts) == 2
        assert len(PdfReader(parts[0][1]).pages) == 2
        assert len(PdfReader(parts[1][1]).pages) == 3

    def test_custom_split_remainder_goes_to_last(self):
        pdf = _make_pdf(10)
        parts = split_pdf_stream_custom(pdf, [2, 3])
        assert len(parts) == 2
        assert len(PdfReader(parts[0][1]).pages) == 2
        # Last chunk absorbs remaining pages
        assert len(PdfReader(parts[1][1]).pages) == 8

    def test_custom_split_single_count(self):
        pdf = _make_pdf(5)
        parts = split_pdf_stream_custom(pdf, [5])
        assert len(parts) == 1
        assert len(PdfReader(parts[0][1]).pages) == 5

    def test_custom_split_filenames(self):
        pdf = _make_pdf(4)
        parts = split_pdf_stream_custom(pdf, [1, 1, 2])
        names = [name for name, _ in parts]
        assert names == ["split_part_1.pdf", "split_part_2.pdf", "split_part_3.pdf"]
