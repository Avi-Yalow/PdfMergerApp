"""PDF Merger & Splitter – Kivy entry point for Android (and desktop)."""

import sys
from pathlib import Path

try:
    from kivy.app import App
    from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.textinput import TextInput
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.filechooser import FileChooserListView
    from kivy.uix.popup import Popup
    from kivy.metrics import dp
except ImportError:
    print("Kivy is required. Install it with: pip install kivy")
    sys.exit(1)

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("pypdf is required. Install it with: pip install pypdf")
    sys.exit(1)

from split_pdf import split_pdf, split_pdf_custom

# Detect Android and set the default file-browser root accordingly.
try:
    from android import mActivity  # noqa: F401 – only importable on-device
    _IS_ANDROID = True
    _DEFAULT_PATH = "/sdcard"
except ImportError:
    _IS_ANDROID = False
    _DEFAULT_PATH = str(Path.home())


# ---------------------------------------------------------------------------
# Reusable popup widgets
# ---------------------------------------------------------------------------

class _FileChooserPopup(Popup):
    """File-chooser popup that calls *callback* with the selected paths."""

    def __init__(self, callback, multiselect=False, path=_DEFAULT_PATH, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.title = "Select File"
        self.size_hint = (0.95, 0.9)

        layout = BoxLayout(orientation="vertical", spacing=dp(6))

        self.chooser = FileChooserListView(
            path=path,
            filters=["*.pdf", "*.PDF"],
            multiselect=multiselect,
        )
        layout.add_widget(self.chooser)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        btn_select = Button(text="Select")
        btn_select.bind(on_press=self._on_select)
        btn_cancel = Button(text="Cancel")
        btn_cancel.bind(on_press=self.dismiss)
        btn_row.add_widget(btn_select)
        btn_row.add_widget(btn_cancel)
        layout.add_widget(btn_row)

        self.content = layout

    def _on_select(self, *_args):
        if self.chooser.selection:
            self.callback(self.chooser.selection)
            self.dismiss()


class _DirChooserPopup(Popup):
    """Directory-chooser popup that calls *callback* with the chosen path."""

    def __init__(self, callback, path=_DEFAULT_PATH, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.title = "Select Output Directory"
        self.size_hint = (0.95, 0.9)

        layout = BoxLayout(orientation="vertical", spacing=dp(6))

        self.chooser = FileChooserListView(
            path=path,
            dirselect=True,
        )
        layout.add_widget(self.chooser)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        btn_select = Button(text="Select")
        btn_select.bind(on_press=self._on_select)
        btn_cancel = Button(text="Cancel")
        btn_cancel.bind(on_press=self.dismiss)
        btn_row.add_widget(btn_select)
        btn_row.add_widget(btn_cancel)
        layout.add_widget(btn_row)

        self.content = layout

    def _on_select(self, *_args):
        chosen = self.chooser.path
        if self.chooser.selection:
            chosen = self.chooser.selection[0]
        self.callback(chosen)
        self.dismiss()


class _MessagePopup(Popup):
    """Simple informational/alert popup."""

    def __init__(self, title, message, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.85, 0.45)

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        lbl = Label(text=message, halign="center", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        layout.add_widget(lbl)

        btn = Button(text="OK", size_hint_y=None, height=dp(50))
        btn.bind(on_press=self.dismiss)
        layout.add_widget(btn)

        self.content = layout


# ---------------------------------------------------------------------------
# Merge tab
# ---------------------------------------------------------------------------

class _MergeTab(BoxLayout):
    """Content for the "Merge PDFs" tab."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(10), **kwargs)

        self.file_paths: list[str] = []

        self.add_widget(Label(
            text="PDF Merger",
            size_hint_y=None,
            height=dp(44),
            font_size=dp(20),
            bold=True,
            halign="center",
        ))

        # Scrollable file list -----------------------------------------------
        scroll = ScrollView(size_hint_y=1)
        self._file_list_lbl = Label(
            text="No files added yet.",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._file_list_lbl.bind(texture_size=self._file_list_lbl.setter("size"))
        scroll.add_widget(self._file_list_lbl)
        self.add_widget(scroll)

        # File management buttons --------------------------------------------
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        for label, handler in [
            ("Add Files", self._add_files),
            ("Remove Last", self._remove_last),
            ("Clear All", self._clear_all),
        ]:
            btn = Button(text=label)
            btn.bind(on_press=handler)
            btn_row.add_widget(btn)
        self.add_widget(btn_row)

        # Output path row ----------------------------------------------------
        out_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        out_row.add_widget(Label(text="Save to:", size_hint_x=None, width=dp(70)))
        self._output_input = TextInput(
            text=str(Path(_DEFAULT_PATH) / "merged.pdf"),
            multiline=False,
            hint_text="Output file path",
        )
        out_row.add_widget(self._output_input)
        btn_browse = Button(text="Browse", size_hint_x=None, width=dp(80))
        btn_browse.bind(on_press=self._browse_output_dir)
        out_row.add_widget(btn_browse)
        self.add_widget(out_row)

        # Merge button -------------------------------------------------------
        btn_merge = Button(text="Merge PDFs", size_hint_y=None, height=dp(55))
        btn_merge.bind(on_press=self._merge)
        self.add_widget(btn_merge)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_list(self):
        if not self.file_paths:
            self._file_list_lbl.text = "No files added yet."
        else:
            lines = [f"{i + 1}. {Path(p).name}" for i, p in enumerate(self.file_paths)]
            self._file_list_lbl.text = "\n".join(lines)

    def _add_files(self, *_args):
        _FileChooserPopup(
            callback=self._on_files_selected,
            multiselect=True,
            path=_DEFAULT_PATH,
        ).open()

    def _on_files_selected(self, selection):
        self.file_paths.extend(selection)
        self._refresh_list()

    def _remove_last(self, *_args):
        if self.file_paths:
            self.file_paths.pop()
            self._refresh_list()

    def _clear_all(self, *_args):
        self.file_paths.clear()
        self._refresh_list()

    def _browse_output_dir(self, *_args):
        _DirChooserPopup(
            callback=self._on_output_dir_selected,
            path=_DEFAULT_PATH,
        ).open()

    def _on_output_dir_selected(self, directory):
        current_name = Path(self._output_input.text).name or "merged.pdf"
        self._output_input.text = str(Path(directory) / current_name)

    def _merge(self, *_args):
        if len(self.file_paths) < 2:
            _MessagePopup("PDF Merger", "Please add at least 2 PDF files to merge.").open()
            return

        output_path = self._output_input.text.strip()
        if not output_path:
            output_path = str(Path(_DEFAULT_PATH) / "merged.pdf")

        writer = PdfWriter()
        try:
            for pdf_path in self.file_paths:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
            with open(output_path, "wb") as fh:
                writer.write(fh)
            _MessagePopup(
                "PDF Merger",
                f"Merged {len(self.file_paths)} file(s)!\n\nSaved to:\n{output_path}",
            ).open()
        except Exception as exc:
            _MessagePopup("PDF Merger", f"Error merging files:\n{exc}").open()


# ---------------------------------------------------------------------------
# Split tab
# ---------------------------------------------------------------------------

class _SplitTab(BoxLayout):
    """Content for the "Split PDF" tab.

    The *Pages* field accepts either a single integer (uniform split, e.g. ``5``)
    or a comma-separated list of integers (custom split, e.g. ``2,1,2``).
    """

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(10), **kwargs)

        self.add_widget(Label(
            text="PDF Splitter",
            size_hint_y=None,
            height=dp(44),
            font_size=dp(20),
            bold=True,
            halign="center",
        ))

        # Input file ---------------------------------------------------------
        in_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        in_row.add_widget(Label(text="Input:", size_hint_x=None, width=dp(60)))
        self._input_field = TextInput(
            multiline=False,
            hint_text="Select PDF file…",
            readonly=True,
        )
        in_row.add_widget(self._input_field)
        btn_in = Button(text="Browse", size_hint_x=None, width=dp(80))
        btn_in.bind(on_press=self._browse_input)
        in_row.add_widget(btn_in)
        self.add_widget(in_row)

        # Pages field --------------------------------------------------------
        pages_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        pages_row.add_widget(Label(text="Pages:", size_hint_x=None, width=dp(60)))
        self._pages_input = TextInput(
            text="1",
            multiline=False,
            hint_text="e.g. 5  or  2,1,2",
        )
        pages_row.add_widget(self._pages_input)
        self.add_widget(pages_row)

        hint = Label(
            text="Enter a single number for a uniform split\nor comma-separated counts for a custom split.",
            size_hint_y=None,
            height=dp(44),
            halign="center",
            font_size=dp(12),
        )
        hint.bind(size=hint.setter("text_size"))
        self.add_widget(hint)

        # Output directory ---------------------------------------------------
        out_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        out_row.add_widget(Label(text="Output:", size_hint_x=None, width=dp(60)))
        self._output_dir_field = TextInput(
            text=_DEFAULT_PATH,
            multiline=False,
            hint_text="Output directory",
            readonly=True,
        )
        out_row.add_widget(self._output_dir_field)
        btn_out = Button(text="Browse", size_hint_x=None, width=dp(80))
        btn_out.bind(on_press=self._browse_output_dir)
        out_row.add_widget(btn_out)
        self.add_widget(out_row)

        # Split button -------------------------------------------------------
        btn_split = Button(text="Split PDF", size_hint_y=None, height=dp(55))
        btn_split.bind(on_press=self._split)
        self.add_widget(btn_split)

        # Filler space -------------------------------------------------------
        self.add_widget(Label())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _browse_input(self, *_args):
        _FileChooserPopup(
            callback=self._on_input_selected,
            path=_DEFAULT_PATH,
        ).open()

    def _on_input_selected(self, selection):
        if selection:
            self._input_field.text = selection[0]

    def _browse_output_dir(self, *_args):
        _DirChooserPopup(
            callback=self._on_output_dir_selected,
            path=_DEFAULT_PATH,
        ).open()

    def _on_output_dir_selected(self, directory):
        self._output_dir_field.text = directory

    def _split(self, *_args):
        input_path = self._input_field.text.strip()
        if not input_path:
            _MessagePopup("PDF Splitter", "Please select a PDF file to split.").open()
            return

        output_dir = self._output_dir_field.text.strip()
        if not output_dir:
            _MessagePopup("PDF Splitter", "Please select an output directory.").open()
            return

        raw = self._pages_input.text.strip()
        try:
            if "," in raw:
                # Custom split – comma-separated page counts
                page_counts = [int(x.strip()) for x in raw.split(",") if x.strip()]
                created_files = split_pdf_custom(input_path, page_counts, output_dir)
            else:
                # Uniform split – single integer
                pages_per_file = int(raw) if raw else 1
                created_files = split_pdf(input_path, pages_per_file, output_dir)
        except SystemExit as exc:
            reason = str(exc) if str(exc) not in ("None", "1", "") else "Check your input file and settings."
            _MessagePopup("PDF Splitter", f"Split failed: {reason}").open()
            return
        except Exception as exc:
            _MessagePopup("PDF Splitter", f"Error splitting file:\n{exc}").open()
            return

        _MessagePopup(
            "PDF Splitter",
            f"Split into {len(created_files)} file(s)!\n\nSaved to:\n{output_dir}",
        ).open()


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

class PdfMergerApp(App):
    """Main Kivy application."""

    def build(self):
        panel = TabbedPanel(do_default_tab=False)

        merge_item = TabbedPanelItem(text="Merge PDFs")
        merge_item.content = _MergeTab()
        panel.add_widget(merge_item)

        split_item = TabbedPanelItem(text="Split PDF")
        split_item.content = _SplitTab()
        panel.add_widget(split_item)

        return panel


if __name__ == "__main__":
    PdfMergerApp().run()
