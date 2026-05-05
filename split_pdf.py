"""PDF Split Tool - Split a PDF file into multiple smaller PDF files."""

import argparse
import io
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
    from pdf_operations import split_pdf_stream_uniform, split_pdf_stream_custom
except ImportError:
    print("Required package 'pypdf' not found. Install it with: pip install pypdf")
    sys.exit(1)


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

    stream = io.BytesIO(path.read_bytes())
    total_pages = len(PdfReader(stream).pages)
    stream.seek(0)

    if total_pages == 0:
        print("Error: The input PDF has no pages.")
        sys.exit(1)

    parts = split_pdf_stream_uniform(stream, pages_per_file)
    return _write_parts(parts, output_dir_path, output_prefix, path.name)


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

    stream = io.BytesIO(path.read_bytes())
    total_pages = len(PdfReader(stream).pages)
    stream.seek(0)

    if total_pages == 0:
        print("Error: The input PDF has no pages.")
        sys.exit(1)

    if sum(page_counts) > total_pages:
        print(
            f"Error: requested {sum(page_counts)} pages but the PDF only has {total_pages}."
        )
        sys.exit(1)

    parts = split_pdf_stream_custom(stream, page_counts)
    return _write_parts(parts, output_dir_path, output_prefix, path.name)


def _write_parts(
    parts: list[tuple[str, io.BytesIO]],
    output_dir_path: Path,
    output_prefix: str,
    source_name: str,
) -> list[str]:
    """Write *parts* (each a (name, stream) pair) to individual PDF files."""
    output_files: list[str] = []
    for part_num, (_, buf) in enumerate(parts, start=1):
        output_file = output_dir_path / f"{output_prefix}_part_{part_num}.pdf"
        data = buf.read()
        output_file.write_bytes(data)
        num_pages = len(PdfReader(io.BytesIO(data)).pages)
        print(f"Created: {output_file} ({num_pages} page(s))")
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
