"""Run: python green_path_v4.py. A simple Tkinter GUI for Green Path."""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from PIL import ImageTk

from green_path_core import Game, ATTACKS, BASE, START_HP
from mission import Mission
from photos import read_photo, import_photo, photo_path, PHOTO_KEYS

BG = "#10171c"
PANEL = "#19242b"
EDGE = "#2b3b43"
TEXT = "#eef4f2"
MUTED = "#a4b7bb"
GREEN = "#94dfb2"


class GreenPathApp:
    def __init__(self, root, game):
        self.root = root
        self.game = game
        self.mission = None
        self.round_review = None
        self.buttons = {}
        self.images = []
        root.title("Green Path V4")
        root.geometry("1080x760")
        root.minsize(960, 700)
        root.configure(background=BG)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(16, 10),
                        background=PANEL, foreground=TEXT, borderwidth=0)
        style.map("TButton", background=[("active", "#30464d"), ("pressed", "#3a565b")])
        style.configure("Accent.TButton", background=GREEN, foreground="#10251b")
        style.map("Accent.TButton", background=[("active", "#b5efcb"), ("pressed", "#7bc899")])
        style.configure("TEntry", fieldbackground=PANEL, foreground=TEXT, insertcolor=TEXT,
                        bordercolor=EDGE, lightcolor=EDGE, darkcolor=EDGE, padding=7)
        style.map("TEntry", bordercolor=[("focus", GREEN)], lightcolor=[("focus", GREEN)])
        style.configure("Horizontal.TProgressbar", background=GREEN, troughcolor=EDGE,
                        borderwidth=0, lightcolor=GREEN, darkcolor=GREEN)
        style.configure("Vertical.TScrollbar", background=EDGE, troughcolor=PANEL, borderwidth=0)
        header = tk.Frame(root, bg=BG, padx=32, pady=12)
        header.pack(fill="x")
        self.label(header, "GREEN / PATH", font=("Segoe UI", 15, "bold"), color=GREEN).pack(side="left")
        self.label(header, "V4  /  EXPLORE  /  RESTORE  /  LEARN", font=("Segoe UI", 9), color=MUTED).pack(side="right")
        tk.Frame(root, bg=EDGE, height=1).pack(fill="x")
        footer = tk.Frame(root, bg=BG, padx=32, pady=8)
        footer.pack(side="bottom", fill="x")
        self.label(footer, "An environmental adventure · Fictional missions, real places", color=MUTED,
                   font=("Segoe UI", 9)).pack(side="left")
        ttk.Button(footer, text="Photo credits", command=self.show_credits).pack(side="right")
        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.page = ttk.Frame(self.canvas, padding=(32, 16))
        page_id = self.canvas.create_window((0, 0), window=self.page, anchor="nw")
        self.page.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(page_id, width=event.width))
        root.bind("<MouseWheel>", self.scroll_page)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.show_login()

    def clear(self, title, subtitle=""):
        for child in self.page.winfo_children():
            child.destroy()
        self.buttons = {}
        self.images = []
        self.canvas.yview_moveto(0)
        ttk.Label(self.page, text=title, style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        if subtitle:
            self.label(self.page, subtitle, color=MUTED, wrap=970).pack(anchor="w", pady=(0, 14))

    def scroll_page(self, event):
        if not isinstance(event.widget, (tk.Text, tk.Listbox)) and self.page.winfo_reqheight() > self.canvas.winfo_height():
            self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def button(self, parent, label, callback, accent=False, vertical=False):
        def safe_callback():
            try:
                callback()
            except (ValueError, PermissionError, sqlite3.Error, OSError) as error:
                messagebox.showerror("Could not complete action", str(error), parent=self.root)
        widget = ttk.Button(parent, text=label, command=safe_callback,
                            style="Accent.TButton" if accent else "TButton")
        widget.pack(side="top" if vertical else "left", fill="x" if vertical else "none",
                    padx=(0, 8), pady=5)
        self.buttons[label] = widget
        return widget

    def row(self, parent=None):
        frame = ttk.Frame(parent or self.page)
        frame.pack(fill="x")
        return frame

    def entry(self, parent, label, secret=False, initial=""):
        self.label(parent, label, color=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 3))
        widget = ttk.Entry(parent, show="*" if secret else "", font=("Segoe UI", 11))
        widget.pack(fill="x", pady=(0, 3))
        widget.insert(0, initial)
        return widget

    def text_box(self, text, height=8):
        box = ScrolledText(self.page, height=height, wrap="word", font=("Segoe UI", 11),
                           background=PANEL, foreground=TEXT, padx=16, pady=12,
                           relief="flat", borderwidth=0, highlightthickness=1,
                           highlightbackground=EDGE, insertbackground=TEXT)
        box.pack(fill="both", expand=True, pady=8)
        box.insert("1.0", text)
        box.configure(state="disabled")
        return box

    def label(self, parent, text, color=TEXT, font=("Segoe UI", 11), wrap=0):
        background = parent.cget("background") if isinstance(parent, tk.Frame) else BG
        return tk.Label(parent, text=text, bg=background, fg=color,
                        font=font, justify="left", anchor="w", wraplength=wrap)

    def card(self, parent):
        return tk.Frame(parent, bg=PANEL, padx=18, pady=16,
                        highlightbackground=EDGE, highlightthickness=1)

    def photo_card(self, parent, location, kind, width=430, height=235):
        frame = self.card(parent)
        caption = "BEFORE / THE CHALLENGE" if kind == "before" else "AFTER / THE GOAL"
        self.label(frame, caption, color=GREEN, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        area = tk.Frame(frame, bg=BG, width=width, height=height)
        area.pack(fill="x")
        area.pack_propagate(False)
        name = location.get(kind + "_photo")
        try:
            if not name:
                raise ValueError("No photo added")
            image = ImageTk.PhotoImage(read_photo(photo_path(name), (width, height)), master=self.root)
            self.images.append(image)
            tk.Label(area, image=image, bg=BG).pack(expand=True)
        except (ValueError, OSError, tk.TclError):
            self.label(area, "Photo unavailable\nAn administrator can add one.", color=MUTED).pack(expand=True)
        credit = (location.get(kind + "_credit") or "Administrator supplied photo") if name else "No photo selected"
        self.label(frame, credit, color=MUTED, font=("Segoe UI", 8), wrap=width).pack(anchor="w", pady=(8, 0))
        return frame

    def stats(self):
        mission = self.mission
        bar = self.row()
        for title, value in [("HEALTH", f"{mission.hp} / {START_HP}"),
                             ("POINTS", str(mission.score)),
                             ("LOCATIONS RESOLVED", f"{mission.resolved} / {len(mission.locations)}")]:
            panel = self.card(bar)
            panel.configure(pady=10)
            panel.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=(0, 14))
            self.label(panel, title, color=MUTED, font=("Segoe UI", 9)).pack(side="left", padx=(0, 14))
            self.label(panel, value, color=GREEN, font=("Segoe UI", 17, "bold")).pack(side="right")

    def show_credits(self):
        window = tk.Toplevel(self.root)
        window.title("Photo credits")
        window.geometry("760x560")
        box = ScrolledText(window, wrap="word", bg=BG, fg=TEXT, font=("Segoe UI", 10), padx=20, pady=20)
        box.pack(fill="both", expand=True)
        try:
            text = (BASE / "PHOTO_CREDITS.md").read_text(encoding="utf-8")
        except OSError:
            text = "No bundled photo credits file found."
        if self.game.user_id is not None:
            text += "\n\nCURRENT LOCATION CREDITS\n"
            for location in self.game.locations():
                text += f"\n{location['name']}\nBefore: {location['before_credit'] or 'None'}\nAfter: {location['after_credit'] or 'None'}\n{location['photo_note'] or ''}\n"
        box.insert("1.0", text)
        box.configure(state="disabled")

    def show_login(self):
        self.clear("Small actions. A cleaner world.", "Visit real places, take on environmental challenges, and make every move count.")
        columns = self.row()
        left = ttk.Frame(columns)
        left.pack(side="left", fill="both", expand=True, padx=(0, 28))
        locations = self.game.locations()
        if locations:
            self.photo_card(left, dict(locations[0]), "after", 440, 270).pack(fill="x")
        self.label(left, "YOUR MISSION STARTS HERE", color=GREEN, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(22, 8))
        self.label(left, "Explore India's landmarks.\nFace a challenge at each stop.\nDiscover what is worth protecting.", color=MUTED, wrap=440).pack(anchor="w")
        form = ttk.Frame(columns, width=410)
        form.pack(side="left", fill="both", expand=True)
        self.label(form, "Welcome back", font=("Segoe UI", 21, "bold")).pack(anchor="w", pady=(12, 8))
        self.label(form, "Sign in to begin your next mission.", color=MUTED).pack(anchor="w", pady=(0, 12))
        self.username = self.entry(form, "Username")
        self.password = self.entry(form, "Password", secret=True)
        self.button(self.row(form), "Log in", self.login, accent=True)
        self.button(self.row(form), "Create player account", lambda: self.show_registration(False))
        if not self.game.db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            self.button(self.row(form), "First-time administrator setup", lambda: self.show_registration(True))
        self.label(form, "Five failed logins cause a 60-second cooldown.", color=MUTED, font=("Segoe UI", 9), wrap=380).pack(anchor="w", pady=14)
        self.username.focus_set()

    def login(self):
        password = self.password.get()
        self.password.delete(0, "end")
        if not self.game.login(self.username.get(), password):
            raise ValueError("Login failed or temporarily locked. Check details or wait 60 seconds.")
        self.show_home()

    def show_registration(self, admin):
        self.clear("Administrator setup" if admin else "Create player account",
                   "Username: 3-24 letters, digits or underscores, starting with a letter.\n"
                   "Password: a memorable passphrase of 12-128 characters.")
        self.username = self.entry(self.page, "Username")
        self.password = self.entry(self.page, "Password", secret=True)
        self.confirm = self.entry(self.page, "Confirm password", secret=True)
        self.button(self.row(), "Create account", lambda: self.register(admin), accent=True)
        self.button(self.row(), "Back to login", self.show_login)

    def register(self, admin):
        password, confirm = self.password.get(), self.confirm.get()
        self.password.delete(0, "end")
        self.confirm.delete(0, "end")
        if password != confirm:
            raise ValueError("Passwords do not match. Please enter them again.")
        self.game.register(self.username.get(), password, setup_admin=admin)
        messagebox.showinfo("Account created", "You can now log in.", parent=self.root)
        self.show_login()

    def show_home(self):
        user = self.game.current_user()
        self.clear("Welcome, " + user["username"],
                   "A new route. A fresh chance to make a difference.")
        locations = self.game.locations()
        hero = self.row()
        intro = self.card(hero)
        intro.pack(side="left", fill="both", expand=True, padx=(0, 18))
        self.label(intro, "FIELD MISSION / INDIA", color=GREEN, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 16))
        self.label(intro, "Explore. Take action.\nLeave a greener path.", font=("Segoe UI", 24, "bold"), wrap=430).pack(anchor="w")
        self.label(intro, f"{len(locations)} locations  ·  300 starting HP  ·  10 points per victory", color=MUTED,
                   wrap=420).pack(anchor="w", pady=(18, 14))
        self.label(intro, "See the challenge before you play, then compare\nthe photos after each victory.", color=MUTED, wrap=430).pack(anchor="w", pady=(0, 22))
        self.button(intro, "Start mission", self.start_mission, accent=True, vertical=True)
        if locations:
            self.photo_card(hero, dict(locations[0]), "after", 430, 225).pack(side="left", fill="both")
        self.label(self.page, "ON YOUR ROUTE", color=GREEN, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(22, 10))
        route = self.row()
        for index, location in enumerate(locations[:4], 1):
            panel = self.card(route)
            panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self.label(panel, f"{index:02}", color=GREEN, font=("Segoe UI", 16, "bold")).pack(anchor="w")
            self.label(panel, location["name"], font=("Segoe UI", 10), wrap=190).pack(anchor="w", pady=(5, 0))
        navigation = self.row()
        self.button(navigation, "Scores and history", self.show_scores)
        if user["role"] == "admin":
            self.button(navigation, "Manage locations", self.show_admin)
        self.button(navigation, "Log out", self.logout)
        self.button(navigation, "Exit", self.close)

    def start_mission(self):
        self.game.current_user()
        self.mission = Mission(self.game.locations())
        self.round_review = None
        self.show_mission()

    def show_mission(self):
        self.game.current_user()
        mission = self.mission
        if self.round_review is not None:
            self.show_round_result()
            return
        if mission.phase == "finished":
            self.show_result()
            return
        location = mission.location()
        location = dict(location)
        self.clear(location["name"], f"FIELD MISSION  /  STOP {mission.index + 1:02} OF {len(mission.locations):02}")
        self.stats()
        body = self.row()
        self.photo_card(body, location, "before", 440, 235).pack(side="left", fill="both", padx=(0, 22))
        details = ttk.Frame(body)
        details.pack(side="left", fill="both", expand=True)
        self.label(details, "THE CHALLENGE", color=GREEN, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.label(details, location["description"], wrap=430).pack(anchor="w", pady=(10, 14))
        self.label(details, location["fact"], color=MUTED, wrap=430).pack(anchor="w", pady=(0, 14))
        if mission.phase == "location":
            self.button(details, "Fight", lambda: self.mission_action("fight"), accent=True, vertical=True)
            self.button(details, "Skip location", lambda: self.mission_action("skip"), vertical=True)
        else:
            self.label(details, f"{location['enemy_name']}  /  {mission.enemy_hp} energy", color=GREEN,
                       font=("Segoe UI", 11, "bold"), wrap=430).pack(anchor="w")
            ttk.Progressbar(details, maximum=location["enemy_hp"], value=mission.enemy_hp).pack(fill="x", pady=(8, 12))
            for i, (name, low, high) in enumerate(ATTACKS):
                # i=i captures this button's own action number.
                self.button(details, f"{name} ({low}-{high})", lambda i=i: self.mission_action("attack", i), vertical=True)
        self.label(self.page, location.get("photo_note") or "Location photos are supplied by the administrator.",
                   color=MUTED, font=("Segoe UI", 9), wrap=970).pack(anchor="w", pady=(10, 0))
        self.text_box("\n".join(mission.log[-3:]), height=3)
        actions = self.row()
        self.button(actions, "End mission", self.end_mission)
        self.button(actions, "Log out", self.logout)

    def mission_action(self, action, number=None):
        self.game.current_user()
        location = dict(self.mission.location())
        resolved = self.mission.resolved
        if action == "fight":
            self.mission.fight()
        elif action == "skip":
            self.mission.skip()
        elif action == "attack":
            self.mission.attack(number)
        if self.mission.resolved > resolved:
            self.round_review = location
        self.show_mission()

    def show_round_result(self):
        location = self.round_review
        self.clear("One step towards a cleaner world.", location["name"] + "  /  CHALLENGE RESOLVED  /  +10 POINTS")
        self.stats()
        pair = self.row()
        for kind in ("before", "after"):
            self.photo_card(pair, location, kind, 430, 210).pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.label(self.page, location.get("photo_note") or "Before/after photos supplied by the administrator.",
                   color=MUTED, font=("Segoe UI", 10), wrap=970).pack(anchor="w", pady=(18, 10))
        self.label(self.page, location["fact"], wrap=970).pack(anchor="w", pady=(0, 16))
        controls = self.row()
        self.button(controls, "Continue", self.continue_mission, accent=True)
        self.button(controls, "Log out", self.logout)

    def continue_mission(self):
        self.round_review = None
        self.show_mission()

    def show_result(self):
        mission = self.mission
        self.round_review = None
        self.clear("Mission result: " + mission.outcome,
                   f"Score: {mission.score}    HP: {mission.hp}    "
                   f"Resolved: {mission.resolved}/{len(mission.locations)}    Skipped: {mission.skipped}")
        self.stats()
        self.text_box("\n".join(mission.log[-10:]), height=10)
        try:
            mission.save(self.game)
        except (sqlite3.Error, OSError) as error:
            ttk.Label(self.page, text="Result not saved. Fix storage access and retry.\n" + str(error),
                      wraplength=710).pack(anchor="w")
            self.button(self.row(), "Retry save", self.show_result)
            return
        ttk.Label(self.page, text="Result saved once. You are still logged in.").pack(anchor="w")
        self.button(self.row(), "Home", self.show_home)
        self.button(self.row(), "Log out", self.logout)

    def end_mission(self):
        if messagebox.askyesno("End mission?", "Save earned points and end this mission?", parent=self.root):
            self.mission.finish()
            self.show_result()

    def finish_before_leaving(self):
        if self.mission is not None and not self.mission.saved:
            if self.mission.phase != "finished":
                if not messagebox.askyesno("Leave mission?", "End this mission and save earned points?", parent=self.root):
                    return False
                self.mission.finish()
            try:
                self.mission.save(self.game)
            except (sqlite3.Error, OSError, PermissionError) as error:
                messagebox.showerror("Result not saved", str(error) + "\nPlease retry before leaving.", parent=self.root)
                self.show_result()
                return False
        return True

    def logout(self):
        if self.finish_before_leaving():
            self.mission = None
            self.round_review = None
            self.game.logout()
            self.show_login()

    def close(self):
        if self.finish_before_leaving():
            self.game.close()
            self.root.destroy()

    def show_scores(self):
        user = self.game.current_user()
        self.clear("Scores and history", "Leaderboard: each player's best saved score, across all mission outcomes.")
        board = self.game.db.execute("""SELECT u.username, MAX(r.score) AS best
            FROM runs r JOIN users u ON u.id=r.user_id GROUP BY u.id
            ORDER BY best DESC, u.username ASC LIMIT 10""").fetchall()
        text = "\n".join(f"{i}. {r['username']} — {r['best']} points" for i, r in enumerate(board, 1))
        text = (text or "No scores yet.") + "\n\nYOUR LAST FIVE RUNS (UTC)\n"
        for r in self.game.db.execute("SELECT * FROM runs WHERE user_id=? ORDER BY id DESC LIMIT 5", (user["id"],)):
            text += f"{r['score']} points | {r['outcome']} | {r['resolved']}/{r['total']} resolved | {r['ended_at']}\n"
        self.text_box(text, height=18)
        self.button(self.row(), "Home", self.show_home)

    def show_admin(self):
        self.game.current_user(admin=True)
        self.clear("Manage locations", "Select a location to edit or delete. Changes apply to future missions.")
        self.admin_locations = self.game.locations()
        self.location_list = tk.Listbox(self.page, height=10, font=("Segoe UI", 12), exportselection=False,
                                       bg=PANEL, fg=TEXT, selectbackground="#355647", selectforeground=TEXT,
                                       relief="flat", highlightbackground=EDGE, highlightcolor=GREEN,
                                       activestyle="none")
        self.location_list.pack(fill="both", expand=True, pady=12)
        for r in self.admin_locations:
            self.location_list.insert("end", r["name"])
        buttons = self.row()
        self.button(buttons, "Add location", lambda: self.show_location_form())
        self.button(buttons, "Edit selected", lambda: self.show_location_form(self.selected_location()))
        self.button(buttons, "Delete selected", self.delete_selected)
        self.button(self.row(), "Home", self.show_home)

    def selected_location(self):
        selected = self.location_list.curselection()
        if not selected:
            raise ValueError("Select a location first.")
        return dict(self.admin_locations[selected[0]])

    def delete_selected(self):
        location = self.selected_location()
        if messagebox.askyesno("Delete location?", location["name"], parent=self.root):
            self.game.delete_location(location["id"])
            self.show_admin()

    def show_location_form(self, location=None):
        self.game.current_user(admin=True)
        self.editing = location or {}
        self.clear("Edit location" if location else "Add location", "Set the challenge and add before/after photos. Changes apply to future missions.")
        columns = self.row()
        details = ttk.Frame(columns)
        details.pack(side="left", fill="both", expand=True, padx=(0, 24))
        media = ttk.Frame(columns)
        media.pack(side="left", fill="both", expand=True)
        self.fields = {}
        for key, label in [("name", "Location name"), ("description", "Description"),
                           ("fact", "Learning theme"), ("enemy_name", "Fictional challenge name"),
                           ("enemy_type", "Challenge type"), ("enemy_hp", "Challenge HP")]:
            self.fields[key] = self.entry(details, label, initial=str(self.editing.get(key, "")))
        self.label(details, "Challenge HP: 1–1000.\nPhotos are optional; the game also works without them.",
                   color=MUTED, font=("Segoe UI", 9), wrap=400).pack(anchor="w", pady=14)
        self.photo_values = {key: self.editing.get(key) or "" for key in PHOTO_KEYS}
        self.photo_previews = ttk.Frame(media)
        self.photo_previews.pack(fill="x")
        self.update_photo_previews()
        self.photo_fields = {}
        for key, label in [("before_credit", "Before: photographer / source / license"),
                           ("after_credit", "After: photographer / source / license"),
                           ("photo_note", "Photo context (shown to players)")]:
            self.photo_fields[key] = self.entry(media, label, initial=self.photo_values[key])
        self.label(media, "Choose JPG, PNG or WebP files (up to 12 MB / 20 MP).\nOnly add photos you own or have permission to reuse.",
                   color=MUTED, font=("Segoe UI", 9), wrap=440).pack(anchor="w", pady=12)
        self.button(self.row(), "Save location", self.save_location, accent=True)
        self.button(self.row(), "Cancel", self.show_admin)

    def update_photo_previews(self):
        for child in self.photo_previews.winfo_children():
            child.destroy()
        for kind in ("before", "after"):
            column = ttk.Frame(self.photo_previews)
            column.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self.photo_card(column, self.photo_values, kind, 180, 115).pack(fill="x")
            controls = self.row(column)
            self.button(controls, "Choose " + kind, lambda k=kind: self.choose_photo(k))
            self.button(self.row(column), "Remove " + kind, lambda k=kind: self.remove_photo(k))

    def choose_photo(self, kind):
        self.game.current_user(admin=True)
        filename = filedialog.askopenfilename(parent=self.root, title="Choose " + kind + " photo",
                    filetypes=[("Photos", "*.jpg *.jpeg *.png *.webp *.gif"), ("All files", "*.*")])
        if filename:
            self.photo_values[kind + "_photo"] = import_photo(filename)
            self.photo_values[kind + "_credit"] = ""
            self.photo_fields[kind + "_credit"].delete(0, "end")
            self.update_photo_previews()

    def remove_photo(self, kind):
        self.photo_values[kind + "_photo"] = ""
        self.photo_values[kind + "_credit"] = ""
        self.photo_fields[kind + "_credit"].delete(0, "end")
        self.update_photo_previews()

    def save_location(self):
        values = {key: entry.get() for key, entry in self.fields.items()}
        try:
            hp = int(values["enemy_hp"])
        except ValueError:
            raise ValueError("Challenge HP must be a whole number from 1 to 1000.")
        item = {"name": values["name"], "description": values["description"], "fact": values["fact"],
                "polluter": {"name": values["enemy_name"], "type": values["enemy_type"], "hp": hp}}
        for key, field in self.photo_fields.items():
            self.photo_values[key] = field.get()
        for kind in ("before", "after"):
            if self.photo_values[kind + "_photo"] and not self.photo_values[kind + "_credit"].strip():
                raise ValueError("Add the photographer and reuse permission for the " + kind + " photo.")
        self.game.save_location(item, self.editing.get("id"), photos=self.photo_values)
        self.show_admin()


def main():
    root = tk.Tk()
    root.withdraw()
    try:
        game = Game()
    except (OSError, ValueError, sqlite3.Error) as error:
        messagebox.showerror("Green Path could not start", str(error) + "\nFiles have not been reset.", parent=root)
        root.destroy()
        return
    app = GreenPathApp(root, game)
    root.deiconify()
    try:
        root.mainloop()
    finally:
        # Safe even when normal window-close has already closed the connection.
        game.close()


if __name__ == "__main__":
    main()
