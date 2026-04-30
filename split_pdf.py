"""PDF Split Tool - Split a PDF file into multiple smaller PDF files."""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Required package 'pypdf' not found. Install it with: pip install pypdf")
    sys.exit(1)


def _write_chunk(
    reader: "PdfReader",
    page_indices: list[int],
    output_file: Path,
) -> None:
    """Write a subset of pages from *reader* to *output_file*."""
    writer = PdfWriter()
    for idx in page_indices:
        writer.add_page(reader.pages[idx])
    with open(output_file, "wb") as f:
        writer.write(f)


def split_pdf(
    input_file: str,
    pages_per_file: int,
    output_dir: str = ".",
    output_prefix: str | None = None,
) -> list[str]:
    """Split a PDF into equal-sized chunks of *pages_per_file* pages each.

    The last chunk will contain the remaining pages if the total is not evenly
    divisible.

    Args:
        input_file: Path to the input PDF file.
        pages_per_file: Number of pages in each output file.
        output_dir: Directory where the output files will be saved.
        output_prefix: Prefix for output filenames (defaults to input stem).

    Returns:
        List of output file paths that were created.
    """
    path = Path(input_file)
    if not path.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    if path.suffix.lower() != ".pdf":
        print(f"Warning: {input_file} may not be a PDF file")

    if pages_per_file < 1:
        print("Error: pages-per-file must be at least 1")
        sys.exit(1)

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if output_prefix is None:
        output_prefix = path.stem

    reader = PdfReader(str(path))
    total_pages = len(reader.pages)

    if total_pages == 0:
        print("Error: The input PDF has no pages.")
        sys.exit(1)

    # Build uniform chunk sizes
    chunks: list[list[int]] = []
    for start in range(0, total_pages, pages_per_file):
        end = min(start + pages_per_file, total_pages)
        chunks.append(list(range(start, end)))

    return _write_chunks(reader, chunks, output_dir_path, output_prefix, path.name)


def split_pdf_custom(
    input_file: str,
    page_counts: list[int],
    output_dir: str = ".",
    output_prefix: str | None = None,
) -> list[str]:
    """Split a PDF into chunks with a custom page count per output file.

    Args:
        input_file: Path to the input PDF file.
        page_counts: List of page counts for each output file.  The values
            must be positive integers and their sum must not exceed the total
            number of pages in the PDF.  Any pages beyond the sum will be
            appended to the last chunk.
        output_dir: Directory where the output files will be saved.
        output_prefix: Prefix for output filenames (defaults to input stem).

    Returns:
        List of output file paths that were created.

    Example::

        # 5-page PDF → 2 + 1 + 2
        split_pdf_custom("doc.pdf", [2, 1, 2])

        # 5-page PDF → 1 + 2 + 1 + 1
        split_pdf_custom("doc.pdf", [1, 2, 1, 1])
    """
    path = Path(input_file)
    if not path.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    if path.suffix.lower() != ".pdf":
        print(f"Warning: {input_file} may not be a PDF file")

    if not page_counts:
        print("Error: page_counts must not be empty.")
        sys.exit(1)
    if any(c < 1 for c in page_counts):
        print("Error: every page count must be at least 1.")
        sys.exit(1)

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if output_prefix is None:
        output_prefix = path.stem

    reader = PdfReader(str(path))
    total_pages = len(reader.pages)

    if total_pages == 0:
        print("Error: The input PDF has no pages.")
        sys.exit(1)

    if sum(page_counts) > total_pages:
        print(
            f"Error: requested {sum(page_counts)} pages but the PDF only has {total_pages}."
        )
        sys.exit(1)

    # Build custom chunks; remaining pages (if any) go into the last chunk
    chunks: list[list[int]] = []
    cursor = 0
    for i, count in enumerate(page_counts):
        if cursor >= total_pages:
            break
        if i == len(page_counts) - 1:
            # Last requested chunk gets all remaining pages
            end = total_pages
        else:
            end = min(cursor + count, total_pages)
        chunks.append(list(range(cursor, end)))
        cursor = end

    return _write_chunks(reader, chunks, output_dir_path, output_prefix, path.name)


def _write_chunks(
    reader: "PdfReader",
    chunks: list[list[int]],
    output_dir_path: Path,
    output_prefix: str,
    source_name: str,
) -> list[str]:
    """Write *chunks* (each a list of 0-based page indices) to individual PDFs."""
    output_files: list[str] = []
    for part, page_indices in enumerate(chunks, start=1):
        output_file = output_dir_path / f"{output_prefix}_part_{part}.pdf"
        _write_chunk(reader, page_indices, output_file)
        start_label = page_indices[0] + 1
        end_label = page_indices[-1] + 1
        print(f"Created: {output_file} (pages {start_label}–{end_label})")
        output_files.append(str(output_file))

    print(f"Split '{source_name}' into {len(output_files)} file(s).")
    return output_files


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF file into multiple smaller PDF files."
    )
    parser.add_argument("input", help="PDF file to split")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "-n",
        "--pages-per-file",
        type=int,
        metavar="N",
        help="Split into equal chunks of N pages each",
    )
    mode_group.add_argument(
        "-s",
        "--split",
        metavar="N1,N2,...",
        help=(
            "Comma-separated page counts for each output file "
            "(e.g. '2,1,2' splits into files of 2, 1, and 2 pages)"
        ),
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        help="Output filename prefix (default: input filename without extension)",
    )
    args = parser.parse_args()

    if args.pages_per_file is not None:
        split_pdf(args.input, args.pages_per_file, args.output_dir, args.prefix)
    else:
        try:
            page_counts = [int(x.strip()) for x in args.split.split(",") if x.strip()]
        except ValueError:
            parser.error("--split must be a comma-separated list of integers, e.g. '2,1,2'")
        split_pdf_custom(args.input, page_counts, args.output_dir, args.prefix)


if __name__ == "__main__":
    main()
