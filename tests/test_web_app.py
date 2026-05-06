"""Tests for the Flask web application routes."""

import io
import zipfile

import pytest
from pypdf import PdfReader, PdfWriter

from web_app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _make_pdf(num_pages: int = 1) -> io.BytesIO:
    """Create a minimal valid PDF with the given number of pages."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf


class TestIndex:
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200


class TestMergeRoute:
    def test_merge_success(self, client):
        pdf1 = _make_pdf(1)
        pdf2 = _make_pdf(2)
        data = {
            "pdfs": [
                (pdf1, "a.pdf"),
                (pdf2, "b.pdf"),
            ]
        }
        resp = client.post("/merge", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"
        reader = PdfReader(io.BytesIO(resp.data))
        assert len(reader.pages) == 3

    def test_merge_fewer_than_two_files(self, client):
        pdf = _make_pdf(1)
        data = {"pdfs": [(pdf, "a.pdf")]}
        resp = client.post("/merge", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert "at least 2" in resp.get_json()["error"]

    def test_merge_non_pdf_rejected(self, client):
        pdf = _make_pdf(1)
        txt = io.BytesIO(b"not a pdf")
        data = {
            "pdfs": [
                (pdf, "a.pdf"),
                (txt, "b.txt"),
            ]
        }
        resp = client.post("/merge", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert "not a PDF" in resp.get_json()["error"]


class TestSplitRoute:
    def test_split_uniform(self, client):
        pdf = _make_pdf(4)
        data = {
            "pdf": (pdf, "doc.pdf"),
            "mode": "uniform",
            "pages_per_file": "2",
        }
        resp = client.post("/split", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.content_type == "application/zip"
        zf = zipfile.ZipFile(io.BytesIO(resp.data))
        assert len(zf.namelist()) == 2

    def test_split_uniform_single_part_returns_pdf(self, client):
        pdf = _make_pdf(2)
        data = {
            "pdf": (pdf, "doc.pdf"),
            "mode": "uniform",
            "pages_per_file": "10",
        }
        resp = client.post("/split", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"

    def test_split_custom(self, client):
        pdf = _make_pdf(5)
        data = {
            "pdf": (pdf, "doc.pdf"),
            "mode": "custom",
            "page_counts": "2,3",
        }
        resp = client.post("/split", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert resp.content_type == "application/zip"
        zf = zipfile.ZipFile(io.BytesIO(resp.data))
        assert len(zf.namelist()) == 2

    def test_split_no_file(self, client):
        resp = client.post("/split", data={"mode": "uniform"}, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_split_non_pdf_rejected(self, client):
        data = {
            "pdf": (io.BytesIO(b"hello"), "doc.txt"),
            "mode": "uniform",
            "pages_per_file": "1",
        }
        resp = client.post("/split", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert "not a PDF" in resp.get_json()["error"]

    def test_split_invalid_pages_per_file(self, client):
        pdf = _make_pdf(4)
        data = {
            "pdf": (pdf, "doc.pdf"),
            "mode": "uniform",
            "pages_per_file": "0",
        }
        resp = client.post("/split", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_split_invalid_custom_counts(self, client):
        pdf = _make_pdf(4)
        data = {
            "pdf": (pdf, "doc.pdf"),
            "mode": "custom",
            "page_counts": "a,b,c",
        }
        resp = client.post("/split", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_split_unknown_mode(self, client):
        pdf = _make_pdf(4)
        data = {
            "pdf": (pdf, "doc.pdf"),
            "mode": "unknown",
        }
        resp = client.post("/split", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400
