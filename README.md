# PDF Merger & Splitter App

A simple tool to merge multiple PDF files into one, or split a single PDF into smaller files. Available as both a **command-line interface (CLI)** and a **graphical user interface (GUI)**.

---

## Features

- Merge two or more PDF files into a single output file
- **Split a single PDF into multiple smaller files** — uniform chunks or fully custom page counts per file
- CLI mode for scripting and automation
- GUI mode for a point-and-click experience (built with tkinter)
- Reorder files before merging (GUI)
- Build a standalone Windows executable with a single command
- Build an Android APK with a single command (via [Buildozer](https://buildozer.readthedocs.io/))

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

## Building an Android APK

The Android build uses [Kivy](https://kivy.org/) for the UI and [Buildozer](https://buildozer.readthedocs.io/) as the packaging tool.  The entry point is `main.py` (a Kivy re-implementation of the same Merge + Split UI).

### Prerequisites

1. **Linux or macOS build machine** (Ubuntu 22.04 LTS is recommended; Windows users can use WSL 2).

2. Install system dependencies:

   ```bash
   sudo apt-get update && sudo apt-get install -y \
       git zip unzip openjdk-17-jdk python3-pip \
       autoconf libtool pkg-config zlib1g-dev \
       libncurses5-dev libncursesw5-dev libtinfo5 \
       cmake libffi-dev libssl-dev
   ```

3. Install Buildozer and Kivy:

   ```bash
   pip install buildozer kivy
   ```

### Build

```bash
bash build_android.sh          # debug APK (default)
bash build_android.sh release  # release APK (requires keystore setup)
```

The first run downloads the Android SDK/NDK and compiles the Python runtime — this can take 20–30 minutes.  Subsequent builds are much faster.

The resulting APK is placed in the `bin/` directory.

### Android app features

The Kivy UI (`main.py`) provides the same two-tab interface as the desktop GUI:

**Merge PDFs tab** — tap *Add Files* to pick one or more PDFs, then tap *Merge PDFs* to combine them.

**Split PDF tab** — select an input PDF and enter either a single page count (uniform split, e.g. `3`) or a comma-separated list of counts (custom split, e.g. `2,1,2`), then tap *Split PDF*.

Output files are written to the directory you select (defaults to device storage root).

---

## Project Structure

```
PdfMergerApp/
├── main.py              # Kivy entry point for Android (merge + split tabs)
├── merge_pdfs.py        # CLI entry point for merging
├── merge_pdfs_gui.py    # GUI entry point (merge + split tabs, tkinter/desktop)
├── split_pdf.py         # CLI entry point for splitting
├── requirements.txt     # Python dependencies (desktop)
├── buildozer.spec       # Buildozer configuration for Android APK
├── build.bat            # PyInstaller build script (Windows)
└── build_android.sh     # Buildozer build script (Android)
```

---

## License

This project is open source. See the repository for details.
