"""Simple screens: login, route, fights, photo reviews and records."""
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from arena import Arena
from admin import setup_admin, show_admin
from art import draw_login_hero
from dialogue import FACTS, LOGIN_FLAVOUR, ShuffleBag, scene_for
from mission import Mission
from photos import PhotoView
from resources import BASE
from theme import BG, PANEL, TEXT, MUTED, CYAN, SAGE, MAGENTA, YELLOW, INK, ERROR, EDGE, FONT, TITLE, action_button

class App:
    def __init__(self, root, game):
        self.root, self.game, self.mission, self.arena = root, game, None, None
        self.pool = ThreadPoolExecutor(max_workers=2)
        self.quip_timer = None
        self.quips = ShuffleBag(LOGIN_FLAVOUR)
        root.title("Green Path · Bauhaus")
        root.geometry("1040x800")
        root.minsize(960, 720)
        root.configure(bg=BG)
        root.option_add("*Font", (FONT, 11))
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TButton", background=BG, foreground=TEXT, borderwidth=0, relief="flat", padding=(0, 7), font=(FONT, 11), anchor="w", focusthickness=1, focuscolor=EDGE)
        style.map("TButton", background=[("disabled", PANEL), ("pressed", PANEL), ("active", CYAN)], foreground=[("disabled", MUTED), ("active", INK)])
        style.configure("Primary.TButton", background=MAGENTA, foreground=INK, padding=(19, 12), font=(TITLE, 12, "bold"))
        style.map("Primary.TButton", background=[("active", CYAN)], foreground=[("active", INK)])
        style.configure("TEntry", fieldbackground=BG, foreground=TEXT, insertcolor=TEXT, bordercolor=EDGE, lightcolor=BG, darkcolor=BG, borderwidth=1, relief="solid", padding=(10, 9))
        style.map("TEntry", bordercolor=[("focus", MAGENTA)], lightcolor=[("focus", MAGENTA)], darkcolor=[("focus", MAGENTA)])
        style.configure("TCombobox", fieldbackground=BG, background=BG, foreground=TEXT, arrowcolor=TEXT, bordercolor=EDGE, padding=7)
        style.map("TCombobox", fieldbackground=[("readonly", BG)], foreground=[("readonly", TEXT)])
        style.configure("Vertical.TScrollbar", background=PANEL, troughcolor=BG, arrowcolor=TEXT, lightcolor=PANEL, darkcolor=PANEL, bordercolor=BG, borderwidth=0)
        self.page = tk.Frame(root, bg=BG, padx=31, pady=23)
        self.page.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.login_screen()
    def clear(self, title):
        if self.arena:
            self.arena.stop()
            self.arena = None
        if self.quip_timer:
            self.root.after_cancel(self.quip_timer)
            self.quip_timer = None
        for child in self.page.winfo_children():
            child.destroy()
        if title:
            self.say(title, 26, TEXT)
            tk.Frame(self.page, bg=EDGE, height=1).pack(fill="x", pady=(0, 13))
    def say(self, text, size=11, color=TEXT, parent=None):
        label = tk.Label(parent or self.page, text=text, bg=(parent or self.page).cget("background"), fg=color,
                         font=(TITLE if size >= 20 else FONT, size, "bold" if size >= 20 else "normal"), wraplength=900, justify="left", anchor="w")
        label.pack(anchor="w", pady=(3, 11))
        return label
    def button(self, text, callback, primary=False, parent=None):
        def run():
            try:
                callback()
            except (ValueError, PermissionError, sqlite3.Error, OSError) as error:
                messagebox.showerror("Try that again", str(error), parent=self.root)
        return action_button(parent or self.page, text, run, "Primary.TButton" if primary else "TButton", anchor="w", pady=(9, 4))
    def login_screen(self):
        self.clear("")
        self.say("A GAME BY AKSHITH KESARI", 9, MUTED)
        spread = tk.Frame(self.page, bg=BG)
        spread.pack(fill="x", pady=(37, 19))
        story, divider = tk.Frame(spread, bg=BG), tk.Frame(spread, bg=EDGE)
        story.pack(side="left", anchor="n", padx=(0, 33))
        divider.pack(side="left", anchor="n", pady=(11, 0))
        form = tk.Frame(divider, bg=BG, padx=23, pady=0)
        form.pack(padx=(1, 0))
        hero = tk.Canvas(story, width=430, height=286, bg=BG, highlightthickness=0)
        hero.pack(anchor="w")
        draw_login_hero(hero, 430)
        self.flavour = self.say("", 15, ERROR, story)
        self.flavour.configure(wraplength=375, height=4, anchor="nw", fg=TEXT, pady=19)
        self.rotate_quip()
        self.say("PLAYER ENTRY / 01", 9, MUTED, form)
        self.say("take a breath.", 27, TEXT, form)
        self.say("Username", 10, MUTED, form)
        self.username = ttk.Entry(form, width=29)
        self.username.pack(anchor="w")
        self.say("Passphrase / 12-128 characters", 10, MUTED, form)
        self.password = ttk.Entry(form, width=29, show="*")
        self.password.pack(anchor="w")
        self.password.bind("<Return>", lambda event: self.authenticate(False))
        self.feedback = self.say("", 10, ERROR, form)
        self.feedback.configure(height=3, wraplength=285, anchor="nw")
        self.button("Log in & play", lambda: self.authenticate(False), True, form)
        self.button("New here? Create a player", lambda: self.authenticate(True), parent=form)
        self.button("Credits", self.credits)
        self.say("Admin? Use your usual login, then choose Edit maps.", 9, MUTED)
        self.username.focus_set()
    def rotate_quip(self):
        if self.quip_timer:
            self.root.after_cancel(self.quip_timer)
        self.flavour.configure(text=self.quips.next())
        self.quip_timer = self.root.after(6500, self.rotate_quip)
    def authenticate(self, create):
        try:
            if create:
                self.game.register(self.username.get(), self.password.get())
            if not self.game.login(self.username.get(), self.password.get()):
                raise ValueError("Check your username and passphrase.")
            self.home()
        except (ValueError, sqlite3.Error) as error:
            self.feedback.configure(text=str(error))
    def home(self):
        self.clear("GREEN PATH")
        self.say("The air has attitude. You have four moves.", 17, TEXT)
        places = self.game.locations()
        for number, place in enumerate(places[:4], 1):
            self.say(f"{number:02}   {place['name']}", 14)
        if len(places) > 4:
            self.say(f"And {len(places) - 4} more stops on this route.", 10, MUTED)
        self.say("WASD / arrows to move. J attack / K parry / Space dodge / L heavy.\nPress an action again in the bright zone. P / Esc pauses.", 10, MUTED)
        if places:
            self.button("Head out on the route", self.start, True)
        else:
            self.say("The route is empty. An admin can add a map to get things moving.", color=ERROR)
        if self.game.is_admin() or not self.game.has_admin():
            self.button("Edit maps" if self.game.is_admin() else "Set up admin", lambda: show_admin(self) if self.game.is_admin() else setup_admin(self))
        self.button("Leaderboard", self.records)
        self.button("Credits", self.credits)
        self.button("Log out", self.logout)
    def logout(self):
        self.game.user_id = None
        self.login_screen()
    def start(self):
        self.mission = Mission(self.game.locations())
        self.briefing()
    def briefing(self):
        m = self.mission
        if m.outcome:
            return self.result()
        place = m.location
        self.clear(place["name"])
        self.say(f"STOP {m.index + 1}/{len(m.locations)}     {m.hp} HP     {m.score} points", color=TEXT)
        self.say(scene_for(place)["arrival"])
        if place["before_photo"]:
            PhotoView(self.page, self.pool, place["before_photo"]).pack(pady=12)
        self.button("I'm ready", self.fight, True)
        self.button("Skip this stop", self.skip)
        self.button("End route", self.retreat)
    def skip(self):
        self.mission.skip()
        self.briefing()
    def fight(self):
        self.clear("")
        place = self.mission.location
        self.arena = Arena(self.page, self.mission.fight(), place, self.battle_finished, self.retreat)
        self.arena.pack(fill="both", expand=True)
    def battle_finished(self):
        place = self.mission.location
        won = self.mission.combat.state == "won"
        self.mission.finish_battle()
        if not won:
            return self.result()
        self.clear("Stop cleared. +10 points!")
        self.say(scene_for(place)["victory"])
        pair = tk.Frame(self.page, bg=BG)
        pair.pack(pady=12)
        for kind in (kind for kind in ("before", "after") if place[kind + "_photo"]):
            column = tk.Frame(pair, bg=BG)
            column.pack(side="left", padx=12)
            self.say(kind.upper(), 10, TEXT, column)
            PhotoView(column, self.pool, place[kind + "_photo"]).pack()
        if place["photo_note"]:
            self.say(place["photo_note"], color=MUTED)
        self.say(place["fact"], color=TEXT)
        self.button("Continue", self.briefing, True)
    def result(self):
        m = self.mission
        self.clear("Look how far you came." if m.outcome == "completed" else "Catch your breath.")
        try:
            m.save(self.game)
        except (sqlite3.Error, OSError) as error:
            self.say(f"Your record needs another try: {error}", color=ERROR)
            return self.button("Try saving again", self.result, True)
        self.say(f"{m.score} points     {m.resolved}/{len(m.locations)} stops cleared     {m.hp} HP", 17, TEXT)
        self.button("Try again", self.start, True)
        self.button("Home", self.home)
    def retreat(self):
        self.mission.outcome = "abandoned"
        if self.arena:
            self.mission.hp = self.arena.combat.hp
        self.result()
    def records(self):
        self.clear("FIELD RECORDS")
        board = self.game.leaderboard()
        if not board:
            self.say("No footprints yet. Finish a journey to leave the first score.", 17, TEXT)
        for rank, row in enumerate(board, 1):
            self.say(f"{rank:02}    {row['username']}    {row['best']} points", 16, TEXT)
        self.button("Home", self.home)
    def credits(self):
        window = tk.Toplevel(self.root)
        window.title("Green Path - Credits")
        box = ScrolledText(window, width=90, height=30, wrap="word", bg=BG, fg=TEXT, font=(FONT, 11), padx=19, pady=17)
        box.pack(fill="both", expand=True)
        sources = "\n".join(dict.fromkeys(source for topic, text, source in FACTS))
        box.insert("1.0", (BASE / "PHOTO_CREDITS.md").read_text() + "\n\nFACT SOURCES\n" + sources)
        box.configure(state="disabled")
    def close(self):
        if self.mission and not self.mission.saved:
            was_paused = self.arena.combat.paused if self.arena else False
            if self.arena:
                self.arena.combat.paused = True
            if not messagebox.askyesno("Save and leave?", "End this journey and keep earned points?", parent=self.root):
                if self.arena:
                    self.arena.combat.paused = was_paused
                return
            try:
                self.mission.outcome = self.mission.outcome or "abandoned"
                if self.arena:
                    self.mission.hp = self.arena.combat.hp
                self.mission.save(self.game)
            except (OSError, sqlite3.Error) as error:
                messagebox.showerror("Save failed", str(error), parent=self.root)
                return
        if self.arena:
            self.arena.stop()
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()
