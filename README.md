# PDF Merger & Splitter App

A simple tool to merge multiple PDF files into one, or split a single PDF into smaller files. Available as both a **command-line interface (CLI)** and a **graphical user interface (GUI)**.

---

## Features

- Merge two or more PDF files into a single output file
- **Split a single PDF into multiple smaller files** — uniform chunks or fully custom page counts per file
- **Web UI** — browser-based interface, no desktop required
- CLI mode for scripting and automation
- GUI mode for a point-and-click experience (built with tkinter)
- Reorder files before merging (GUI / Web UI)
- Build a standalone Windows executable with a single command

---

## Requirements

- Python 3.10 or higher
- [pypdf](https://pypdf.readthedocs.io/)
- [Flask](https://flask.palletsprojects.com/) *(required for the web UI only)*
- [Gunicorn](https://gunicorn.org/) *(required for the web UI only)*

Install the dependencies with:

```bash
pip install -r requirements.txt
```

---

## Usage

### Web UI

```bash
python web_app.py
```

Then open <http://localhost:5000> in your browser.

### Docker

Build and run the web UI in a container:

```bash
docker build -t pdf-merger-app .
docker run -p 5000:5000 pdf-merger-app
```

Then open <http://localhost:5000> in your browser.  The web UI has two tabs:

**Merge PDFs tab:**
1. Drag & drop (or click to browse) the PDF files you want to merge.
2. Drag items in the list or use the ▲ / ▼ buttons to reorder them.
3. Click **Merge & Download** — the merged file downloads automatically.

*Empty state — ready to accept files:*

![Merge PDFs tab — empty](https://github.com/user-attachments/assets/d9cf3696-ed04-42df-8e7c-9253ed93409f)

*Files loaded and ready to merge:*

![Merge PDFs tab — files queued](https://github.com/user-attachments/assets/e4618496-7a9e-4c02-b788-f6330cd44afa)

**Split PDF tab:**
1. Drag & drop (or click to browse) the PDF you want to split.
2. Choose a split mode:
   - **Uniform** — enter a single number (*pages per output file*).
   - **Custom** — enter a comma-separated list of page counts, e.g. `2,1,2`.
3. Click **Split & Download** — a single PDF or a ZIP archive downloads automatically.

*Empty state — ready to accept a file:*

![Split PDF tab — empty](https://github.com/user-attachments/assets/2c5553df-9d96-47fc-af1a-7b115de80603)

*File loaded with Uniform split mode selected:*

![Split PDF tab — uniform mode](https://github.com/user-attachments/assets/5f9b2cf2-5c2c-4630-9e5b-6cfcc4c8bc09)

---

### GUI (recommended for most users)

```bash
python merge_pdfs_gui.py
```

The GUI has two tabs:

**Merge PDFs tab:**
1. Click **Add Files** to select the PDF files you want to merge.
2. Use **Move Up** / **Move Down** to set the desired page order.
3. Click **Merge PDFs** and choose where to save the output file.

**Split PDF tab:**
1. Click **Browse…** next to *Input PDF File* to select the PDF you want to split.
2. Choose a split mode:
   - **Uniform** — enter a single number in *Pages per output file* (e.g. `3`). Every output file gets that many pages (the last one gets the remainder).
   - **Custom** — enter a comma-separated list of page counts (e.g. `2,1,2`) to produce output files of exactly those sizes.
3. Click **Browse…** next to *Output Directory* to choose where to save the split files.
4. Click **Split PDF**. Output files are named `<original>_part_1.pdf`, `<original>_part_2.pdf`, etc.

### CLI — Merge

```bash
python merge_pdfs.py file1.pdf file2.pdf file3.pdf
```

By default the merged file is saved as `merged.pdf` in the current directory. Use `-o` / `--output` to specify a different path:

```bash
python merge_pdfs.py file1.pdf file2.pdf -o combined.pdf
```

#### CLI merge options

| Option | Description |
|---|---|
| `inputs` | One or more PDF files to merge (in the order listed) |
| `-o`, `--output` | Output filename (default: `merged.pdf`) |

### CLI — Split

**Uniform split** — same number of pages per file:

```bash
python split_pdf.py input.pdf -n 5
```

This splits `input.pdf` into chunks of 5 pages each.

**Custom split** — specify individual page counts with `--split`:

```bash
# 5-page PDF → file with 2 pages, file with 1 page, file with 2 pages
python split_pdf.py input.pdf --split 2,1,2

# 5-page PDF → 1 + 2 + 1 + 1 pages
python split_pdf.py input.pdf --split 1,2,1,1
```

```bash
# optional: custom output dir and prefix
python split_pdf.py input.pdf -n 10 -o ./output_dir -p chapter
python split_pdf.py input.pdf --split 3,2,5 -o ./output_dir
```

#### CLI split options

| Option | Description |
|---|---|
| `input` | PDF file to split |
| `-n`, `--pages-per-file` | Split into equal chunks of N pages each *(use this **or** `--split`)* |
| `-s`, `--split` | Comma-separated page counts per output file, e.g. `2,1,2` *(use this **or** `-n`)* |
| `-o`, `--output-dir` | Output directory (default: current directory) |
| `-p`, `--prefix` | Output filename prefix (default: input filename without extension) |

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
├── merge_pdfs.py        # CLI entry point for merging
├── merge_pdfs_gui.py    # GUI entry point (merge + split tabs)
├── split_pdf.py         # CLI entry point for splitting
├── web_app.py           # Web UI entry point (Flask)
├── templates/
│   └── index.html       # Web UI HTML template
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container image for the web UI
└── build.bat            # PyInstaller build script (Windows)
```

---

## License

This project is open source. See the repository for details.
