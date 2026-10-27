"""Fixed-size photo previews loaded off the Tk thread; no resize work during play."""
from functools import lru_cache
import time
import tkinter as tk
from PIL import Image, ImageOps, ImageTk
from resources import BASE
from theme import BG, EDGE, MUTED

@lru_cache(maxsize=8)
def load_photo(name):
    path = (BASE / name).resolve()
    if not path.is_relative_to((BASE / "photos").resolve()):
        raise ValueError("Photo must be inside the photos folder.")
    if path.stat().st_size > 12 * 1024 * 1024:
        raise ValueError("Photo is too large.")
    with Image.open(path) as image:
        if image.width * image.height > 20_000_000:
            raise ValueError("Photo is too large.")
        image = ImageOps.exif_transpose(image)
        image.thumbnail((380, 190), Image.Resampling.LANCZOS)
        return image.convert("RGB")

class PhotoView(tk.Label):
    def __init__(self, parent, executor, name):
        super().__init__(parent, text="Opening the view...", bg=BG, fg=MUTED,
                         highlightthickness=1, highlightbackground=EDGE)
        self.future = executor.submit(load_photo, name) if name else None
        self.timer = self.after(25, self.poll)
        self.bind("<Destroy>", lambda event: self.after_cancel(self.timer))

    def poll(self):
        if not self.future:
            self.configure(text="Photo unavailable")
        elif not self.future.done():
            self.configure(text="Opening the view" + "." * (int(time.monotonic() * 4) % 3 + 1))
            self.timer = self.after(25, self.poll)
        else:
            try:
                self.image = ImageTk.PhotoImage(self.future.result(), master=self)
                self.configure(image=self.image, text="")
            except (ValueError, OSError):
                self.configure(text="Photo unavailable")
