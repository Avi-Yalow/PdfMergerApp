"""Core PDF business logic shared by all application interfaces."""

import io

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    raise SystemExit("Required package 'pypdf' not found. Install it with: pip install pypdf")


def merge_pdf_streams(streams: list[io.BytesIO]) -> io.BytesIO:
    """Merge multiple PDF byte-streams into one and return the result.

    Args:
        streams: List of PDF file contents as BytesIO streams.

    Returns:
        A BytesIO stream containing the merged PDF.
    """
    writer = PdfWriter()
    for stream in streams:
        reader = PdfReader(stream)
        for page in reader.pages:
            writer.add_page(page)
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def split_pdf_stream_uniform(
    stream: io.BytesIO, pages_per_file: int
) -> list[tuple[str, io.BytesIO]]:
    """Split a PDF stream into equal chunks of *pages_per_file* pages each.

    The last chunk will contain the remaining pages if the total is not evenly
    divisible.

    Args:
        stream: PDF file contents as a BytesIO stream.
        pages_per_file: Number of pages in each output chunk.

    Returns:
        List of (filename, BytesIO) tuples for each output chunk.
    """
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


def split_pdf_stream_custom(
    stream: io.BytesIO, page_counts: list[int]
) -> list[tuple[str, io.BytesIO]]:
    """Split a PDF stream using *page_counts* as sizes for each output chunk.

    The last chunk absorbs any remaining pages beyond the specified counts.

    Args:
        stream: PDF file contents as a BytesIO stream.
        page_counts: List of page counts for each output chunk.

    Returns:
        List of (filename, BytesIO) tuples for each output chunk.
    """
    reader = PdfReader(stream)
    total = len(reader.pages)
    results: list[tuple[str, io.BytesIO]] = []
    cursor = 0
    num_parts = len(page_counts)
    for part, count in enumerate(page_counts, start=1):
        # Last part gets all remaining pages; other parts get exactly count pages.
        end = total if part == num_parts else min(cursor + count, total)
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
