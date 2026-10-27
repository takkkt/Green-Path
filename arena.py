"""Tk presents Combat state; the simulation never creates a widget."""
import math
import time
import tkinter as tk
from tkinter import ttk
from art import draw_landmark, drawing_for
from combat import COOLDOWNS
from dialogue import fact_deck
from theme import BG, PANEL, CHARCOAL, EDGE, TEXT, MUTED, CYAN, MAGENTA, SAGE, YELLOW, INK, FONT, MONO, action_button

KEYS = {"j": "attack", "1": "attack", "k": "parry", "2": "parry", "space": "dodge", "3": "dodge", "l": "heavy", "4": "heavy"}
LABELS = {"attack": "J  Attack", "parry": "K  Parry", "dodge": "Space  Dodge", "heavy": "L  Heavy"}
ACTION_COLORS = {"attack": MAGENTA, "parry": CYAN, "dodge": SAGE, "heavy": YELLOW}

class Arena(tk.Frame):
    def __init__(self, parent, combat, location, done, retreat):
        super().__init__(parent, bg=BG)
        self.combat, self.location, self.done = combat, location, done
        self.root, self.held, self.releases = self.winfo_toplevel(), set(), {}
        self.timer, self.stopped, self.ended = None, False, False
        self.previous, self.deadline = time.perf_counter(), time.perf_counter()
        self.bullets, self.scale, self.ox, self.oy = {}, 1, 0, 0
        self.facts, self.next_fact = fact_deck(location["name"]), 12
        self.hud = tk.Label(self, bg=BG, fg=TEXT, font=(MONO, 11), anchor="w")
        self.hud.pack(fill="x", pady=(5, 13))
        self.canvas = tk.Canvas(self, bg=BG, height=460, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.status = tk.Label(self, bg=BG, fg=TEXT, font=(FONT, 11), wraplength=850)
        self.status.pack(pady=(9, 3))
        self.guide = tk.Label(self, text=self.facts.next(), bg=BG, fg=MUTED, font=(FONT, 10), wraplength=850, height=2, anchor="w", justify="left", pady=3)
        self.guide.pack(fill="x", pady=(3, 11))
        controls = tk.Frame(self, bg=BG)
        controls.pack(fill="x")
        self.buttons = {}
        for action in COOLDOWNS:
            ttk.Style(self).configure(action + ".TButton", background=ACTION_COLORS[action], foreground=INK, padding=(11, 9), font=(MONO, 11, "bold"))
            button = action_button(controls, LABELS[action], lambda a=action: combat.request(a), action + ".TButton", side="left", expand=True, fill="x", padx=(0, 7))
            self.buttons[action] = button
        ttk.Button(controls, text="Pause P", command=self.pause).pack(side="left", padx=4)
        ttk.Button(controls, text="Retreat", command=retreat).pack(side="left")
        self.canvas.bind("<Configure>", self.resize)
        self.bindings = [(event, self.root.bind(event, callback, add="+")) for event, callback in
                         (("<KeyPress>", self.key_down), ("<KeyRelease>", self.key_up), ("<FocusOut>", self.focus_out))]
        self.timer = self.after(16, self.frame)
    def point(self, x, y):
        return self.ox + x * self.scale, self.oy + y * self.scale
    def box(self, x0, y0, x1, y1):
        return *self.point(x0, y0), *self.point(x1, y1)
    def resize(self, event):
        self.scale = min(event.width / 960, event.height / 540)
        self.ox, self.oy = (event.width - 960 * self.scale) / 2, (event.height - 540 * self.scale) / 2
        c = self.canvas
        c.delete("all")
        self.bullets.clear()
        c.create_rectangle(*self.box(30, 150, 930, 510), fill=CHARCOAL, outline=CHARCOAL, width=1, tags="playfield")
        self.core = draw_landmark(c, drawing_for(self.location), self.point, self.box)
        self.player = c.create_polygon(0, 0, 0, 0, 0, 0, fill=CYAN, outline=YELLOW)
        self.ring = c.create_oval(0, 0, 0, 0, outline=CYAN, width=2)
        self.cue = c.create_oval(0, 0, 0, 0, outline=CYAN, width=2)
        self.gap = c.create_rectangle(0, 0, 0, 0, outline=SAGE, dash=(4, 4))
        self.telegraph = c.create_oval(0, 0, 0, 0, outline=YELLOW, width=2)
        self.qte_items = [c.create_rectangle(*self.box(225, 12, 735, 118), fill=BG, outline=EDGE, width=1),
                          c.create_text(*self.point(480, 35), fill=TEXT, font=(MONO, 12, "bold")),
                          c.create_rectangle(*self.box(254, 62, 706, 81), fill=CHARCOAL, outline=""),
                          c.create_rectangle(0, 0, 0, 0, fill=SAGE, outline=""),
                          c.create_rectangle(0, 0, 0, 0, fill=CYAN, outline=""),
                          c.create_line(0, 0, 0, 0, fill=MAGENTA, width=3)]
        self.render()
    def key_down(self, event):
        key = event.keysym.lower()
        if key in self.releases:
            self.after_cancel(self.releases.pop(key))
        if key in self.held:
            return "break"
        self.held.add(key)
        if key in ("p", "escape"):
            self.pause()
        elif key == "return" or key in KEYS:
            self.combat.request("confirm" if key == "return" else KEYS[key])
        return "break"
    def key_up(self, event):
        key = event.keysym.lower()
        self.releases[key] = self.after(8, lambda: self.held.discard(key))
        return "break"
    def pause(self):
        self.combat.paused = not self.combat.paused
        self.held.clear()
    def focus_out(self, event):
        def check():
            if not self.stopped and self.root.focus_displayof() is None:
                self.combat.paused = True
                self.held.clear()
        self.after_idle(check)
    def frame(self):
        if self.stopped:
            return
        now = time.perf_counter()
        movement = (int(bool(self.held & {"d", "right"})) - int(bool(self.held & {"a", "left"})),
                    int(bool(self.held & {"s", "down"})) - int(bool(self.held & {"w", "up"})))
        self.combat.advance(min(.05, now - self.previous), movement)
        self.previous = now
        e = self.combat
        if not e.paused and not e.qte and e.time >= self.next_fact:
            self.guide.configure(text=self.facts.next())
            self.next_fact = e.time + 12
        self.render()
        if e.state != "active" and not self.ended:
            self.ended = True
            self.timer = self.after(450, self.done)
            return
        self.deadline = max(self.deadline + 1 / 60, now)
        self.timer = self.after(max(1, round((self.deadline - time.perf_counter()) * 1000)), self.frame)
    def render(self):
        if not hasattr(self, "player"):
            return
        c, e = self.canvas, self.combat
        self.hud.configure(text=f"{self.location['name']}     YOU {e.hp}/300     POLLUTION {e.enemy_hp}/{e.enemy_max}")
        self.status.configure(text="Paused. P / Esc to continue." if e.paused else e.notice)
        alive = {shot.id for shot in e.shots}
        for key in set(self.bullets) - alive:
            c.delete(self.bullets.pop(key))
        for shot in e.shots:
            if shot.id not in self.bullets:
                self.bullets[shot.id] = c.create_oval(0, 0, 0, 0, fill=MAGENTA if shot.id % 2 else YELLOW, outline=YELLOW, width=1)
            c.coords(self.bullets[shot.id], *self.box(shot.x + 23, shot.y + 143, shot.x + 37, shot.y + 157))
        x, y = e.x + 30, e.y + 150
        c.coords(self.player, *self.point(x, y - 10), *self.point(x + 9, y), *self.point(x, y + 10), *self.point(x - 9, y))
        c.itemconfigure(self.player, fill=YELLOW if e.time < e.invulnerable else CYAN)
        radius = 20 + math.sin(e.time * 12) * 4
        c.coords(self.ring, *self.box(x - radius, y - radius, x + radius, y + radius))
        protected = e.time < max(e.invulnerable, e.guard_until) or (e.qte and e.qte.kind == "parry")
        c.itemconfigure(self.ring, state="normal" if protected else "hidden")
        target = e.incoming() if not e.cooldown("parry") and not (e.qte and e.qte.kind == "parry") else None
        c.itemconfigure(self.cue, state="normal" if target else "hidden")
        if target:
            c.coords(self.cue, *self.box(target.x + 16, target.y + 136, target.x + 44, target.y + 164))
        c.itemconfigure(self.gap, state="normal" if e.warnings and e.warnings[0][2] >= 0 else "hidden")
        c.itemconfigure(self.telegraph, state="normal" if e.warnings else "hidden")
        if e.warnings:
            _, shots, gap = e.warnings[0]
            c.coords(self.gap, *self.box(gap - 40, 152, gap + 100, 170))
            sx, sy = shots[0].x + 30, shots[0].y + 150
            c.coords(self.telegraph, *self.box(sx - 8, sy - 8, sx + 8, sy + 8))
        c.itemconfigure(self.core, fill=CYAN if e.notice.startswith("Perfect") else MAGENTA)
        for action, button in self.buttons.items():
            cooldown = e.cooldown(action)
            button.configure(text=LABELS[action] + (f"  {cooldown:.1f}s" if cooldown else ""))
            button.state(["disabled"] if e.paused or e.state != "active" or (cooldown and not (e.qte and e.qte.kind == action)) else ["!disabled"])
        for item in self.qte_items:
            c.itemconfigure(item, state="normal" if e.qte else "hidden")
            c.tag_raise(item)
        if e.qte:
            q = e.qte
            c.itemconfigure(self.qte_items[1], text=q.kind.upper() + " / press the same key again")
            for item, half in ((self.qte_items[3], .23), (self.qte_items[4], q.perfect)):
                c.coords(item, *self.box(254 + 452 * (q.center - half), 62, 254 + 452 * (q.center + half), 81))
            marker = 254 + 452 * min(1, q.progress(e.time))
            c.coords(self.qte_items[5], *self.box(marker, 55, marker, 88))
    def stop(self):
        self.stopped = True
        for timer in [self.timer, *self.releases.values()]:
            if timer:
                self.after_cancel(timer)
        for event, binding in self.bindings:
            self.root.unbind(event, binding)
