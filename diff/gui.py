"""Graphical user interface module."""

import tkinter as tk
from tkinter import filedialog

from . import l5x
from . import report
from . import version


def run():
    """Top-level function to start the GUI."""
    root = App()
    root.mainloop()


class App(tk.Tk):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.title(f"Tag Compare v{version.VERSION}")
        self.file_pickers = [L5XEntry(self, i) for i in range(1, 3)]

        btn = tk.Button(self, text="Compare", command=self._compare)
        btn.pack(pady=10)

    def _compare(self):
        """Handler for clicking the compare button."""
        files = [l5x.filename for l5x in self.file_pickers]
        if not None in files:
            hashes = {f: l5x.compute_md5(f) for f in files}
            tags = {f: l5x.parse(f) for f in files}
            diff = l5x.compare(*[t.values for t in tags.values()])

            # Excluded tags are those without decorated data but have differing
            # raw values.
            excl = l5x.compare(*[t.no_data for t in tags.values()])

            report.generate(files, hashes, tags, diff, excl)


class L5XEntry(tk.Frame):
    """Set of widgets for selecting a single L5X file."""

    def __init__(self, parent, num):
        super().__init__(parent)
        self.num = num
        self.pack(padx=10, pady=10)

        lbl = tk.Label(self, text=f"L5X {num}")
        lbl.pack(side=tk.LEFT)

        self.var = tk.StringVar()
        entry = tk.Entry(self, textvariable=self.var, width=50)
        entry.pack(side=tk.LEFT)

        btn = tk.Button(self, text="...", command=self._on_click)
        btn.pack(side=tk.LEFT)

    @property
    def filename(self):
        """Returns the currently selected file name."""
        raw = self.var.get().strip()
        if raw:
            return raw
        return None

    def _on_click(self):
        """Handler for clicking the select button."""
        filename = filedialog.askopenfilename(
            title=f"Select L5X {self.num}",
            filetypes=[("L5X", "*.L5X")],
        )
        self.var.set(filename)
