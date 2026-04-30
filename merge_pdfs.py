"""PDF Merge Tool - Merge multiple PDF files into one."""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfMerger
except ImportError:
    print("Required package 'pypdf' not found. Install it with: pip install pypdf")
    sys.exit(1)


def merge_pdfs(input_files: list[str], output_file: str) -> None:
    merger = PdfMerger()
    try:
        for pdf_path in input_files:
            path = Path(pdf_path)
            if not path.exists():
                print(f"Error: File not found: {pdf_path}")
                sys.exit(1)
            if not path.suffix.lower() == ".pdf":
                print(f"Warning: {pdf_path} may not be a PDF file")
            merger.append(str(path))

        merger.write(output_file)
        print(f"Merged {len(input_files)} files into: {output_file}")
    finally:
        merger.close()


def main():
    parser = argparse.ArgumentParser(description="Merge multiple PDF files into one.")
    parser.add_argument("inputs", nargs="+", help="PDF files to merge (in order)")
    parser.add_argument("-o", "--output", default="merged.pdf", help="Output filename (default: merged.pdf)")
    args = parser.parse_args()

    merge_pdfs(args.inputs, args.output)


if __name__ == "__main__":
    main()
