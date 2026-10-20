"""Run: python green_path_v3.py. A simple Tkinter GUI for Green Path."""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from green_path_core import Game, ATTACKS
from mission import Mission


class GreenPathApp:
    def __init__(self, root, game):
        self.root = root
        self.game = game
        self.mission = None
        self.buttons = {}
        root.title("Green Path V3")
        root.geometry("900x740")
        root.minsize(780, 680)
        root.configure(background="#edf3ee")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#edf3ee")
        style.configure("TLabel", background="#edf3ee", foreground="#183c2b", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        self.page = ttk.Frame(root, padding=24)
        self.page.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.show_login()

    def clear(self, title, subtitle=""):
        for child in self.page.winfo_children():
            child.destroy()
        self.buttons = {}
        ttk.Label(self.page, text=title, style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        if subtitle:
            ttk.Label(self.page, text=subtitle, wraplength=710).pack(anchor="w", pady=(0, 16))

    def button(self, parent, label, callback):
        def safe_callback():
            try:
                callback()
            except (ValueError, PermissionError, sqlite3.Error, OSError) as error:
                messagebox.showerror("Could not complete action", str(error), parent=self.root)
        widget = ttk.Button(parent, text=label, command=safe_callback)
        widget.pack(side="left", padx=(0, 8), pady=8)
        self.buttons[label] = widget
        return widget

    def row(self):
        frame = ttk.Frame(self.page)
        frame.pack(fill="x")
        return frame

    def entry(self, parent, label, secret=False, initial=""):
        ttk.Label(parent, text=label).pack(anchor="w", pady=(8, 3))
        widget = ttk.Entry(parent, show="*" if secret else "", font=("Segoe UI", 11))
        widget.pack(fill="x", pady=(0, 3))
        widget.insert(0, initial)
        return widget

    def text_box(self, text, height=8):
        box = ScrolledText(self.page, height=height, wrap="word", font=("Segoe UI", 11),
                           background="#ffffff", foreground="#183c2b", padx=10, pady=8)
        box.pack(fill="both", expand=True, pady=8)
        box.insert("1.0", text)
        box.configure(state="disabled")
        return box

    def show_login(self):
        self.clear("GREEN PATH V3", "An environmental adventure. Log in or create a player account.")
        self.username = self.entry(self.page, "Username")
        self.password = self.entry(self.page, "Password", secret=True)
        self.button(self.row(), "Log in", self.login)
        self.button(self.row(), "Create player account", lambda: self.show_registration(False))
        if not self.game.db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            self.button(self.row(), "First-time administrator setup", lambda: self.show_registration(True))
            ttk.Label(self.page, text="The project owner should complete administrator setup on a trusted computer.",
                      wraplength=710).pack(anchor="w", pady=12)
        ttk.Label(self.page, text="Five failed logins cause a 60-second cooldown.").pack(anchor="w", pady=10)
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
        self.button(self.row(), "Create account", lambda: self.register(admin))
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
                   "Explore four starter locations, face fictional challenges and earn points.")
        self.button(self.row(), "Start mission", self.start_mission)
        self.button(self.row(), "Scores and history", self.show_scores)
        if user["role"] == "admin":
            self.button(self.row(), "Manage locations", self.show_admin)
        self.button(self.row(), "Log out", self.logout)
        self.button(self.row(), "Exit", self.close)
        ttk.Label(self.page, text="Starting health: 300 HP. Each victory: 10 points.\n"
                  "After a victory you advance automatically. Skipping earns no points.\n"
                  "Combat and learning themes are fictional teaching activities.",
                  wraplength=710).pack(anchor="w", pady=22)

    def start_mission(self):
        self.game.current_user()
        self.mission = Mission(self.game.locations())
        self.show_mission()

    def show_mission(self):
        self.game.current_user()
        mission = self.mission
        if mission.phase == "finished":
            self.show_result()
            return
        location = mission.location()
        self.clear(location["name"], f"Location {mission.index + 1}/{len(mission.locations)}    "
                   f"HP: {mission.hp}    Score: {mission.score}")
        self.text_box(location["description"] + "\n\n" + location["fact"], height=4)
        controls = self.row()
        if mission.phase == "location":
            self.button(controls, "Fight", lambda: self.mission_action("fight"))
            self.button(controls, "Skip location", lambda: self.mission_action("skip"))
        else:
            ttk.Label(self.page, text=f"{location['enemy_name']}: {mission.enemy_hp} energy").pack(anchor="w")
            for i, (name, low, high) in enumerate(ATTACKS):
                # i=i captures this button's own action number.
                self.button(controls, f"{name} ({low}-{high})", lambda i=i: self.mission_action("attack", i))
        self.text_box("\n".join(mission.log[-8:]), height=7)
        actions = self.row()
        self.button(actions, "End mission", self.end_mission)
        self.button(actions, "Log out", self.logout)

    def mission_action(self, action, number=None):
        self.game.current_user()
        if action == "fight":
            self.mission.fight()
        elif action == "skip":
            self.mission.skip()
        elif action == "attack":
            self.mission.attack(number)
        self.show_mission()

    def show_result(self):
        mission = self.mission
        self.clear("Mission result: " + mission.outcome,
                   f"Score: {mission.score}    HP: {mission.hp}    "
                   f"Resolved: {mission.resolved}/{len(mission.locations)}    Skipped: {mission.skipped}")
        self.text_box("\n".join(mission.log[-12:]), height=12)
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
        self.location_list = tk.Listbox(self.page, height=10, font=("Segoe UI", 12), exportselection=False)
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
        self.clear("Edit location" if location else "Add location", "All fields are required. Challenge HP must be 1-1000.")
        self.fields = {}
        for key, label in [("name", "Location name"), ("description", "Description"),
                           ("fact", "Learning theme"), ("enemy_name", "Fictional challenge name"),
                           ("enemy_type", "Challenge type"), ("enemy_hp", "Challenge HP")]:
            self.fields[key] = self.entry(self.page, label, initial=str(self.editing.get(key, "")))
        self.button(self.row(), "Save location", self.save_location)
        self.button(self.row(), "Cancel", self.show_admin)

    def save_location(self):
        values = {key: entry.get() for key, entry in self.fields.items()}
        try:
            hp = int(values["enemy_hp"])
        except ValueError:
            raise ValueError("Challenge HP must be a whole number from 1 to 1000.")
        item = {"name": values["name"], "description": values["description"], "fact": values["fact"],
                "polluter": {"name": values["enemy_name"], "type": values["enemy_type"], "hp": hp}}
        self.game.save_location(item, self.editing.get("id"))
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
