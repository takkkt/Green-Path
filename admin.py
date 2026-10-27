"""The route notebook: first-admin setup and a small, plain map editor."""
import tkinter as tk
from tkinter import ttk, messagebox
from theme import BG, TEXT, CYAN, EDGE, ERROR, FONT
from art import MAP_ART, drawing_for
from dialogue import scene_for

def setup_admin(app):
    if messagebox.askyesno("Look after the maps?", "Make this account the admin for this copy of Green Path?", parent=app.root):
        app.game.claim_admin()
        show_admin(app)

def show_admin(app):
    app.game.require_admin()
    app.clear("Look after the route.")
    app.say("Choose a stop to edit, or add somewhere new.")
    places = [dict(row) for row in app.game.locations()]
    row = tk.Frame(app.page, bg=BG)
    row.pack(fill="x", pady=(9, 15))
    listing = tk.Listbox(row, height=min(8, max(3, len(places))), bg=BG, fg=TEXT, selectbackground=CYAN, selectforeground=TEXT, font=(FONT, 13), relief="flat", bd=0, highlightbackground=EDGE, highlightcolor=EDGE, activestyle="none", exportselection=False)
    listing.pack(side="left", fill="x", expand=True)
    if len(places) > 8:
        scroll = ttk.Scrollbar(row, command=listing.yview)
        scroll.pack(side="right", fill="y")
        listing.configure(yscrollcommand=scroll.set)
    for number, place in enumerate(places, 1):
        listing.insert("end", f"{number:02}   {place['name']}")
    if not places:
        app.say("An empty route. Add the first map below.")
    def selected():
        if not listing.curselection():
            raise ValueError("Pick a map from the list first.")
        return places[listing.curselection()[0]]
    def remove():
        place = selected()
        if messagebox.askyesno("Remove this map?", f"Remove {place['name']} from future routes?\nYour saved scores and photo files will stay.", parent=app.root, default="no"):
            app.game.delete_location(place["id"])
            show_admin(app)
    app.button("Add a map", lambda: edit_map(app), True)
    edit = app.button("Edit selected map", lambda: edit_map(app, selected()))
    delete = app.button("Remove selected map", remove)
    for button in (edit, delete):
        button.state(["disabled"])
    def selection_changed(event):
        for button in (edit, delete):
            button.state(["!disabled"] if listing.curselection() else ["disabled"])
    listing.bind("<<ListboxSelect>>", selection_changed)
    app.button("Back to the game", app.home)

def edit_map(app, place=None):
    app.game.require_admin()
    place = place or {}
    app.clear("Give this place a story." if place else "Put a place on the map.")
    app.say("Changes appear on your next route. Existing photo pairs stay with their map.")
    form, fields = tk.Frame(app.page, bg=BG), {}
    form.pack(fill="x", pady=(9, 13))
    def tab_field(event):
        target = event.widget.tk_focusPrev() if event.state & 1 else event.widget.tk_focusNext()
        target.focus_set()
        return "break"
    for row, (key, label) in enumerate((("name", "Map name"), ("description", "Arrival story"), ("fact", "A fact to take away"), ("art_style", "Line drawing"), ("enemy_hp", "Base strength / 1-200"))):
        tk.Label(form, text=label, bg=BG, fg=TEXT, font=(FONT, 11), anchor="w").grid(row=row, column=0, sticky="nw", padx=(0, 23), pady=11)
        if key in ("description", "fact"):
            widget = tk.Text(form, height=3, width=60, wrap="word", bg=BG, fg=TEXT, insertbackground=TEXT, font=(FONT, 11), relief="solid", bd=1, highlightthickness=0, padx=7, pady=5)
            widget.insert("1.0", scene_for(place)["arrival"] if key == "description" and place else place.get(key, ""))
            for keypress in ("<Tab>", "<Shift-Tab>"):
                widget.bind(keypress, tab_field)
        elif key == "art_style":
            widget = ttk.Combobox(form, values=list(MAP_ART), state="readonly")
            widget.set(next(label for label, style in MAP_ART.items() if style == drawing_for(place)))
        else:
            widget = ttk.Entry(form)
            widget.insert(0, place.get(key, 50 if key == "enemy_hp" else ""))
        widget.grid(row=row, column=1, sticky="ew", pady=7)
        fields[key] = widget
    form.columnconfigure(1, weight=1)
    fields["name"].focus_set()
    feedback = app.say("New maps use line art. Existing maps keep their photographs.", 10)
    def save():
        try:
            values = {key: widget.get("1.0", "end-1c") if isinstance(widget, tk.Text) else widget.get() for key, widget in fields.items()}
            values["art_style"] = MAP_ART[values["art_style"]]
            app.game.save_location(values, place.get("id"))
            show_admin(app)
            app.say(f"Saved. {values['name'].strip()} is ready for the next route.", 10)
        except (ValueError, OSError) as error:
            feedback.configure(text=str(error), fg=ERROR)
    app.button("Save map", save, True)
    app.button("Cancel", lambda: show_admin(app))
