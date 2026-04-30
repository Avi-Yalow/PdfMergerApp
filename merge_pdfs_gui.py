"""PDF Merge Tool - GUI version using tkinter."""

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


class PdfMergerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Merger")
        self.root.geometry("600x450")
        self.root.minsize(500, 350)

        self._build_ui()

    def _build_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="PDF Merger", font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

        # File list frame
        list_frame = ttk.LabelFrame(main_frame, text="PDF Files (merged in order shown)", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Listbox with scrollbar
        list_inner = ttk.Frame(list_frame)
        list_inner.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_inner)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(list_inner, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        self.file_paths: list[str] = []

        # Buttons for file management
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="Add Files", command=self._add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Remove", command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Move Up", command=self._move_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Move Down", command=self._move_down).pack(side=tk.LEFT)

        # Merge button
        ttk.Button(main_frame, text="Merge PDFs", command=self._merge, style="Accent.TButton").pack(fill=tk.X)

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


def main():
    root = tk.Tk()
    PdfMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
