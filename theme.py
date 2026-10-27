"""Bauhaus-inspired flat colour, clear type and keyboard-accessible controls."""
BG = YELLOW = "#FFFF99"
PANEL = SAGE = "#B8D97D"
CHARCOAL = EDGE = TEXT = "#245C4B"
MUTED = "#45604B"
MAGENTA = "#FF00BF"
CYAN = "#5CE6E6"
INK = "#0B2018"
ERROR = "#8A005F"
FONT = TITLE = "Helvetica"
MONO = "Courier New"

def action_button(parent, text, command, style="TButton", **packing):
    from tkinter import ttk
    button = ttk.Button(parent, text=text, command=command, style=style)
    button.pack(**packing)
    return button
