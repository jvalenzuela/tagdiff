"""Graphical user interface module."""

import tkinter as tk
from tkinter import filedialog

from . import project
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
        self.file_pickers = [L5KEntry(self, i) for i in range(1, 3)]

        btn = tk.Button(self, text="Compare", command=self._compare)
        btn.pack(pady=10)

    def _compare(self):
        """Handler for clicking the compare button."""
        files = [l5k.filename for l5k in self.file_pickers]
        if not None in files:
            tags = {f: project.parse(f) for f in files}
            diff = project.compare(*tags.values())

            report.generate(files, tags, diff)


class L5KEntry(tk.Frame):
    """Set of widgets for selecting a single L5K file."""

    def __init__(self, parent, num):
        super().__init__(parent)
        self.num = num
        self.pack(padx=10, pady=10)

        lbl = tk.Label(self, text=f"L5K {num}")
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
            title=f"Select L5K {self.num}",
            filetypes=[("L5K", "*.L5K")],
        )
        self.var.set(filename)
