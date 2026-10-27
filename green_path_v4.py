"""Run this launcher; keep the other modules and asset ZIP beside it."""
import sqlite3
import tkinter as tk
from tkinter import messagebox
from app import App
from database import Game

def main():
    root = tk.Tk()
    root.withdraw()
    game = None
    try:
        game = Game()
        App(root, game)
        root.deiconify()
        root.mainloop()
    except (ValueError, OSError, sqlite3.Error) as error:
        messagebox.showerror("The trail could not open", str(error), parent=root)
    finally:
        if game:
            game.close()
        try:
            root.destroy()
        except tk.TclError:
            pass

if __name__ == "__main__":
    main()
