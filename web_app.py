"""PDF Merger & Splitter — Flask web application."""

import io
import re
import zipfile
from pathlib import Path

from flask import Flask, make_response, render_template, request, send_file, jsonify

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    raise SystemExit("Required package 'pypdf' not found. Install it with: pip install pypdf")

app = Flask(__name__)
# Maximum upload size: 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _merge_pdfs(file_streams: list[io.BytesIO]) -> io.BytesIO:
    """Merge multiple PDF byte-streams into one and return the result."""
    writer = PdfWriter()
    for stream in file_streams:
        reader = PdfReader(stream)
        for page in reader.pages:
            writer.add_page(page)
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def _split_uniform(stream: io.BytesIO, pages_per_file: int) -> list[tuple[str, io.BytesIO]]:
    """Split *stream* into equal chunks of *pages_per_file* pages each."""
    reader = PdfReader(stream)
    total = len(reader.pages)
    results: list[tuple[str, io.BytesIO]] = []
    part = 1
    for start in range(0, total, pages_per_file):
        end = min(start + pages_per_file, total)
        writer = PdfWriter()
        for idx in range(start, end):
            writer.add_page(reader.pages[idx])
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        results.append((f"split_part_{part}.pdf", buf))
        part += 1
    return results


def _split_custom(stream: io.BytesIO, page_counts: list[int]) -> list[tuple[str, io.BytesIO]]:
    """Split *stream* using *page_counts* as sizes for each output file."""
    reader = PdfReader(stream)
    total = len(reader.pages)
    results: list[tuple[str, io.BytesIO]] = []
    cursor = 0
    for part, count in enumerate(page_counts, start=1):
        if part == len(page_counts):
            end = total
        else:
            end = min(cursor + count, total)
        writer = PdfWriter()
        for idx in range(cursor, end):
            writer.add_page(reader.pages[idx])
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        results.append((f"split_part_{part}.pdf", buf))
        cursor = end
        if cursor >= total:
            break
    return results


def _build_zip(parts: list[tuple[str, io.BytesIO]]) -> io.BytesIO:
    """Pack multiple (name, stream) pairs into a zip archive."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, buf in parts:
            zf.writestr(name, buf.read())
    zip_buf.seek(0)
    return zip_buf


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/merge", methods=["POST"])
def merge():
    files = request.files.getlist("pdfs")
    if len(files) < 2:
        return jsonify(error="Please upload at least 2 PDF files."), 400

    streams: list[io.BytesIO] = []
    for f in files:
        if not f.filename:
            return jsonify(error="One or more files have no name."), 400
        if not f.filename.lower().endswith(".pdf"):
            return jsonify(error=f"'{f.filename}' is not a PDF file."), 400
        streams.append(io.BytesIO(f.read()))

    try:
        merged = _merge_pdfs(streams)
    except Exception:
        app.logger.exception("Merge failed")
        return jsonify(error="Merge failed. Please ensure all uploaded files are valid PDFs."), 500

    return send_file(
        merged,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="merged.pdf",
    )


@app.route("/split", methods=["POST"])
def split():
    file = request.files.get("pdf")
    if not file or not file.filename:
        return jsonify(error="Please upload a PDF file."), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify(error="The uploaded file is not a PDF."), 400

    stem = Path(file.filename).stem
    # Sanitize stem: allow alphanumerics, hyphens, underscores and single dots;
    # strip leading/trailing dots and spaces to prevent path traversal.
    stem = re.sub(r'[^\w\- ]', '', stem)
    stem = re.sub(r'\s+', '_', stem).strip('_') or "split"
    mode = request.form.get("mode", "uniform")
    stream = io.BytesIO(file.read())

    try:
        if mode == "uniform":
            pages_per_file = int(request.form.get("pages_per_file", 1))
            if pages_per_file < 1:
                return jsonify(error="Pages per file must be at least 1."), 400
            parts = _split_uniform(stream, pages_per_file)
        elif mode == "custom":
            raw = request.form.get("page_counts", "")
            try:
                page_counts = [int(x.strip()) for x in raw.split(",") if x.strip()]
            except ValueError:
                return jsonify(error="Page counts must be comma-separated integers, e.g. '2,1,2'."), 400
            if not page_counts or any(c < 1 for c in page_counts):
                return jsonify(error="Each page count must be a positive integer."), 400
            parts = _split_custom(stream, page_counts)
        else:
            return jsonify(error="Unknown split mode."), 400
    except Exception:
        app.logger.exception("Split failed")
        return jsonify(error="Split failed. Please ensure the uploaded file is a valid PDF."), 500

    # Rename parts to use the original stem
    named_parts = [(f"{stem}_part_{i}.pdf", buf) for i, (_, buf) in enumerate(parts, start=1)]

    if len(named_parts) == 1:
        resp = make_response(named_parts[0][1].getvalue())
        resp.headers["Content-Type"] = "application/pdf"
        resp.headers["Content-Disposition"] = f'attachment; filename="{stem}_part_1.pdf"'
        return resp

    zip_buf = _build_zip(named_parts)
    return send_file(
        zip_buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{stem}_split.zip",
    )


if __name__ == "__main__":
    # NOTE: The built-in Flask development server is for local use only.
    # For production deployments use a WSGI server such as Gunicorn:
    #   gunicorn web_app:app
    app.run(debug=False, host="127.0.0.1", port=5000)
