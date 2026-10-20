"""Mission state and combat rules."""
import random
from green_path_core import ATTACKS, START_HP, POINTS_PER_WIN


class Mission:
    def __init__(self, locations, rng=None):
        if not locations:
            raise ValueError("No locations available. Ask an administrator to add one.")
        self.locations = [dict(row) for row in locations]
        self.rng = rng or random.Random()
        self.index = 0
        self.hp = START_HP
        self.enemy_hp = 0
        self.score = 0
        self.resolved = 0
        self.skipped = 0
        self.phase = "location"  # location, combat, or finished
        self.outcome = None
        self.saved = False
        self.log = ["Mission started. Each victory earns 10 points."]

    def require_phase(self, phase):
        if self.phase != phase:
            raise ValueError("That action is not available now.")

    def location(self):
        return self.locations[self.index]

    def fight(self):
        self.require_phase("location")
        self.enemy_hp = self.location()["enemy_hp"]
        self.phase = "combat"
        self.log.append("Encounter started: " + self.location()["enemy_name"])
        if not self.rng.choice([True, False]):
            self.enemy_turn()

    def attack(self, action):
        self.require_phase("combat")
        if type(action) is not int or not 0 <= action < len(ATTACKS):
            raise ValueError("Choose one of the three actions.")
        name, low, high = ATTACKS[action]
        damage = self.rng.randint(low, high)
        self.enemy_hp = max(0, self.enemy_hp - damage)
        self.log.append(f"{name}: {damage} damage. Challenge energy: {self.enemy_hp}.")
        if self.enemy_hp == 0:
            self.score += POINTS_PER_WIN
            self.resolved += 1
            self.log.append("Challenge resolved. +10 points.")
            self.advance()
        else:
            self.enemy_turn()

    def enemy_turn(self):
        damage = self.rng.randint(3, 8)
        self.hp = max(0, self.hp - damage)
        self.log.append(f"Challenge deals {damage} damage. Your HP: {self.hp}.")
        if self.hp == 0:
            self.finish("defeated")

    def skip(self):
        self.require_phase("location")
        self.skipped += 1
        self.log.append("Skipped: " + self.location()["name"])
        self.advance()

    def advance(self):
        self.index += 1
        if self.index == len(self.locations):
            self.finish("completed" if self.skipped == 0 else "visited")
        else:
            self.phase = "location"

    def finish(self, outcome="abandoned"):
        if self.phase != "finished":
            self.phase = "finished"
            self.outcome = outcome
            self.log.append("Mission result: " + outcome)

    def save(self, game):
        """Save once. If writing fails, leave saved=False so the user can retry."""
        self.require_phase("finished")
        if not self.saved:
            game.save_run(self.score, self.resolved, self.skipped,
                          len(self.locations), self.hp, self.outcome)
            self.saved = True
