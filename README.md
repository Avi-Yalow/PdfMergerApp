# PDF Merger App

A simple tool to merge multiple PDF files into one. Available as both a **command-line interface (CLI)** and a **graphical user interface (GUI)**.

---

## Features

- Merge two or more PDF files into a single output file
- CLI mode for scripting and automation
- GUI mode for a point-and-click experience (built with tkinter)
- Reorder files before merging (GUI)
- Build a standalone Windows executable with a single command

---

## Requirements

- Python 3.10 or higher
- [pypdf](https://pypdf.readthedocs.io/)

Install the dependency with:

```bash
pip install -r requirements.txt
```

---

## Usage

### GUI (recommended for most users)

```bash
python merge_pdfs_gui.py
```

1. Click **Add Files** to select the PDF files you want to merge.
2. Use **Move Up** / **Move Down** to set the desired page order.
3. Click **Merge PDFs** and choose where to save the output file.

### CLI

```bash
python merge_pdfs.py file1.pdf file2.pdf file3.pdf
```

By default the merged file is saved as `merged.pdf` in the current directory. Use `-o` / `--output` to specify a different path:

```bash
python merge_pdfs.py file1.pdf file2.pdf -o combined.pdf
```

#### CLI options

| Option | Description |
|---|---|
| `inputs` | One or more PDF files to merge (in the order listed) |
| `-o`, `--output` | Output filename (default: `merged.pdf`) |

---

## Building a Standalone Executable (Windows)

Make sure [PyInstaller](https://pyinstaller.org/) is installed:

```bash
pip install pyinstaller
```

Then run the provided build script:

```bat
build.bat
```

This produces a single-file Windows executable (`PDF Merger.exe`) in the `dist/` folder. No Python installation is required on the target machine.

---

## Project Structure

```
PdfMergerApp/
├── merge_pdfs.py        # CLI entry point
├── merge_pdfs_gui.py    # GUI entry point
├── requirements.txt     # Python dependencies
└── build.bat            # PyInstaller build script (Windows)
```

---

## License

This project is open source. See the repository for details.
