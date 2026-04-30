"""PDF Split Tool - Split a PDF file into multiple smaller PDF files."""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Required package 'pypdf' not found. Install it with: pip install pypdf")
    sys.exit(1)


def split_pdf(
    input_file: str,
    pages_per_file: int,
    output_dir: str = ".",
    output_prefix: str | None = None,
) -> list[str]:
    """Split a PDF file into multiple smaller PDF files.

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

    output_files: list[str] = []
    part = 1
    for start in range(0, total_pages, pages_per_file):
        writer = PdfWriter()
        end = min(start + pages_per_file, total_pages)
        for page_num in range(start, end):
            writer.add_page(reader.pages[page_num])

        output_file = output_dir_path / f"{output_prefix}_part_{part}.pdf"
        with open(output_file, "wb") as f:
            writer.write(f)
        print(f"Created: {output_file} (pages {start + 1}–{end})")
        output_files.append(str(output_file))
        part += 1

    print(f"Split '{path.name}' into {len(output_files)} file(s).")
    return output_files


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF file into multiple smaller PDF files."
    )
    parser.add_argument("input", help="PDF file to split")
    parser.add_argument(
        "-n",
        "--pages-per-file",
        type=int,
        required=True,
        help="Number of pages per output file",
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

    split_pdf(args.input, args.pages_per_file, args.output_dir, args.prefix)


if __name__ == "__main__":
    main()
