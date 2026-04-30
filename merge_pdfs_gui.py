"""PDF Merger & Splitter Tool - GUI version using tkinter."""

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependency",
        "The 'pypdf' package is not installed.\n\n"
        "Please run:\n  pip install pypdf\n\n"
        "Then restart this application."
    )
    sys.exit(1)

from split_pdf import split_pdf


class PdfMergerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Merger & Splitter")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)

        self._build_ui()

    def _build_ui(self):
        # Notebook with two tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        merge_tab = ttk.Frame(notebook, padding=10)
        split_tab = ttk.Frame(notebook, padding=10)

        notebook.add(merge_tab, text="Merge PDFs")
        notebook.add(split_tab, text="Split PDF")

        self._build_merge_tab(merge_tab)
        self._build_split_tab(split_tab)

    # ------------------------------------------------------------------
    # Merge tab
    # ------------------------------------------------------------------

    def _build_merge_tab(self, parent: ttk.Frame):
        ttk.Label(parent, text="PDF Merger", font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

        # File list frame
        list_frame = ttk.LabelFrame(parent, text="PDF Files (merged in order shown)", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        list_inner = ttk.Frame(list_frame)
        list_inner.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_inner)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(list_inner, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        self.file_paths: list[str] = []

        # File management buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="Add Files", command=self._add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Remove", command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Move Up", command=self._move_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Move Down", command=self._move_down).pack(side=tk.LEFT)

        ttk.Button(parent, text="Merge PDFs", command=self._merge).pack(fill=tk.X)

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )
        for f in files:
            self.file_paths.append(f)
            self.file_listbox.insert(tk.END, Path(f).name)

    def _remove_selected(self):
        sel = self.file_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.file_listbox.delete(idx)
        self.file_paths.pop(idx)

    def _clear_all(self):
        self.file_listbox.delete(0, tk.END)
        self.file_paths.clear()

    def _move_up(self):
        sel = self.file_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self._swap(idx, idx - 1)
        self.file_listbox.selection_set(idx - 1)

    def _move_down(self):
        sel = self.file_listbox.curselection()
        if not sel or sel[0] >= len(self.file_paths) - 1:
            return
        idx = sel[0]
        self._swap(idx, idx + 1)
        self.file_listbox.selection_set(idx + 1)

    def _swap(self, i: int, j: int):
        self.file_paths[i], self.file_paths[j] = self.file_paths[j], self.file_paths[i]
        name_i = self.file_listbox.get(i)
        name_j = self.file_listbox.get(j)
        self.file_listbox.delete(i)
        self.file_listbox.insert(i, name_j)
        self.file_listbox.delete(j)
        self.file_listbox.insert(j, name_i)

    def _merge(self):
        if len(self.file_paths) < 2:
            messagebox.showwarning("PDF Merger", "Please add at least 2 PDF files to merge.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="merged.pdf",
        )
        if not output_path:
            return

        writer = PdfWriter()
        try:
            for pdf_path in self.file_paths:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            messagebox.showinfo("PDF Merger", f"Successfully merged {len(self.file_paths)} files!\n\nSaved to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("PDF Merger", f"Error merging files:\n{e}")

    # ------------------------------------------------------------------
    # Split tab
    # ------------------------------------------------------------------

    def _build_split_tab(self, parent: ttk.Frame):
        ttk.Label(parent, text="PDF Splitter", font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

        # Input file selection
        input_frame = ttk.LabelFrame(parent, text="Input PDF File", padding=8)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        input_inner = ttk.Frame(input_frame)
        input_inner.pack(fill=tk.X)

        self.split_input_var = tk.StringVar()
        ttk.Entry(input_inner, textvariable=self.split_input_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(input_inner, text="Browse…", command=self._split_browse_input).pack(side=tk.LEFT)

        # Pages per file
        pages_frame = ttk.LabelFrame(parent, text="Split Options", padding=8)
        pages_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(pages_frame, text="Pages per output file:").pack(side=tk.LEFT, padx=(0, 8))
        self.pages_per_file_var = tk.IntVar(value=1)
        spinbox = ttk.Spinbox(
            pages_frame,
            from_=1,
            to=9999,
            textvariable=self.pages_per_file_var,
            width=8,
        )
        spinbox.pack(side=tk.LEFT)

        # Output directory selection
        out_frame = ttk.LabelFrame(parent, text="Output Directory", padding=8)
        out_frame.pack(fill=tk.X, pady=(0, 10))

        out_inner = ttk.Frame(out_frame)
        out_inner.pack(fill=tk.X)

        self.split_output_dir_var = tk.StringVar()
        ttk.Entry(out_inner, textvariable=self.split_output_dir_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(out_inner, text="Browse…", command=self._split_browse_output_dir).pack(side=tk.LEFT)

        # Split button
        ttk.Button(parent, text="Split PDF", command=self._split).pack(fill=tk.X)

    def _split_browse_input(self):
        path = filedialog.askopenfilename(
            title="Select PDF file to split",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )
        if path:
            self.split_input_var.set(path)

    def _split_browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select output directory")
        if directory:
            self.split_output_dir_var.set(directory)

    def _split(self):
        input_path = self.split_input_var.get().strip()
        if not input_path:
            messagebox.showwarning("PDF Splitter", "Please select a PDF file to split.")
            return

        output_dir = self.split_output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("PDF Splitter", "Please select an output directory.")
            return

        try:
            pages_per_file = int(self.pages_per_file_var.get())
        except (ValueError, tk.TclError):
            messagebox.showwarning("PDF Splitter", "Please enter a valid number of pages per file.")
            return

        if pages_per_file < 1:
            messagebox.showwarning("PDF Splitter", "Pages per file must be at least 1.")
            return

        try:
            created_files = split_pdf(input_path, pages_per_file, output_dir)
            files_list = "\n".join(Path(f).name for f in created_files)
            messagebox.showinfo(
                "PDF Splitter",
                f"Successfully split '{Path(input_path).name}' into {len(created_files)} file(s)!\n\n"
                f"Saved to:\n{output_dir}\n\n"
                f"Files created:\n{files_list}",
            )
        except SystemExit:
            pass  # split_pdf already printed an error message
        except Exception as e:
            messagebox.showerror("PDF Splitter", f"Error splitting file:\n{e}")


def main():
    root = tk.Tk()
    PdfMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
