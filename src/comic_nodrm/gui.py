from pathlib import Path
from kobo import Kobo
from kindle import Kindle
from text_util import rename_invalid_filename_characters, full2half
from epub import epub2cbz
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import setting
import tempfile


class Gui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comic NoDRM")
        self.kobo = Kobo()
        self.kindle = Kindle()
        self.create_widgets()
        self.insert_books()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("title", "type"), show="headings", selectmode="extended")
        self.tree.column("title", width=500, minwidth=500, stretch=tk.NO)
        self.tree.column("type", width=50, minwidth=50, stretch=tk.NO)
        self.tree.heading("title", text="Title")
        self.tree.heading("type", text="Type")
        self.tree.pack(expand=True, fill=tk.BOTH)

        self.path_frame = ttk.Frame(self)
        self.path_frame.pack(padx=5, pady=5, fill=tk.X)

        self.path_entry = ttk.Entry(self.path_frame)
        self.path_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.path_entry.insert(0, str(setting.load_setting().default_folder) or "")

        self.set_path_button = ttk.Button(self.path_frame, text="select", command=self.filedialog)
        self.set_path_button.pack(side=tk.LEFT, padx=5)

        self.execute_button = ttk.Button(self, text="execute", command=self.execute)
        self.execute_button.pack(pady=5)

    def insert_books(self):
        for i, book in enumerate(self.kobo.books):
            self.tree.insert("", "end", iid=f"kobo-{i}", text=book.title, values=(book.title, "kobo"))

        for i, book in enumerate(self.kindle.books):
            self.tree.insert(
                "",
                "end",
                iid=f"kindle-{i}",
                text=book.stem,
                values=(Kindle.get_title(book), "kindle"),
            )

    def filedialog(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def execute(self):
        self.show_progress_popup()
        total_books = len(self.tree.selection())
        save_dir = Path(self.path_entry.get())

        for i, iid in enumerate(self.tree.selection()):
            book_type, index = iid.split("-")
            index = int(index)
            with tempfile.TemporaryDirectory(dir=".") as tmpdir:
                if book_type == "kobo":
                    book = self.kobo.books[index]
                    self.kobo.decrypt(book, Path(tmpdir) / "temp.epub")
                    title = rename_invalid_filename_characters(full2half(book.title))
                    epub2cbz(Path(tmpdir) / "temp.epub", save_dir / f"{title}.cbz")

                else:
                    book = self.kindle.books[index]
                    self.kindle.decrypt_epub(book, Path(tmpdir), "temp")
                    title = rename_invalid_filename_characters(Kindle.get_title(book))
                    epub2cbz(Path(tmpdir) / "temp.epub", save_dir / f"{title}.cbz")

            progress = (i / total_books) * 100
            self.progress_bar["value"] = progress
            self.progress_popup.update()

        self.progress_popup.destroy()

    def show_progress_popup(self):
        self.progress_popup = tk.Toplevel(self)
        self.progress_popup.title("Progress")
        self.progress_bar = ttk.Progressbar(self.progress_popup, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=10, padx=10)
        self.progress_bar["maximum"] = 100


if __name__ == "__main__":
    app = Gui()
    app.mainloop()
