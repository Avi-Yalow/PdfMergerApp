"""PDF Merger & Splitter — Flask web application."""

import io
import re
import zipfile
from pathlib import Path

from flask import Flask, make_response, render_template, request, send_file, jsonify

try:
    from pdf_operations import merge_pdf_streams, split_pdf_stream_uniform, split_pdf_stream_custom
except ImportError:
    raise SystemExit("Required package 'pypdf' not found. Install it with: pip install pypdf")

app = Flask(__name__)
# Maximum upload size: 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
        merged = merge_pdf_streams(streams)
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
    # Replace whitespace runs with underscores and strip leading/trailing underscores
    stem = re.sub(r'\s+', '_', stem).strip('_') or "split"
    mode = request.form.get("mode", "uniform")
    stream = io.BytesIO(file.read())

    try:
        if mode == "uniform":
            pages_per_file = int(request.form.get("pages_per_file", 1))
            if pages_per_file < 1:
                return jsonify(error="Pages per file must be at least 1."), 400
            parts = split_pdf_stream_uniform(stream, pages_per_file)
        elif mode == "custom":
            raw = request.form.get("page_counts", "")
            try:
                page_counts = [int(x.strip()) for x in raw.split(",") if x.strip()]
            except ValueError:
                return jsonify(error="Page counts must be comma-separated integers, e.g. '2,1,2'."), 400
            if not page_counts or any(c < 1 for c in page_counts):
                return jsonify(error="Each page count must be a positive integer."), 400
            parts = split_pdf_stream_custom(stream, page_counts)
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
