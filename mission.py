"""Route state: one battle at a time, carried health and ten points per win."""
from combat import Combat

class Mission:
    def __init__(self, locations):
        if not locations:
            raise ValueError("This route has no locations.")
        self.locations = [dict(row) for row in locations]
        self.index, self.hp, self.score = 0, 300, 0
        self.resolved = self.skipped = 0
        self.outcome = None
        self.saved = False
        self.combat = None

    @property
    def location(self):
        return self.locations[self.index]
    def fight(self):
        self.combat = Combat(self.index, self.location["enemy_hp"], self.hp)
        return self.combat
    def finish_battle(self):
        self.hp = self.combat.hp
        if self.combat.state == "won":
            self.score += 10
            self.resolved += 1
            self.advance()
        else:
            self.outcome = "defeated"
    def advance(self):
        self.index += 1
        if self.index == len(self.locations):
            self.outcome = "visited" if self.skipped else "completed"
    def skip(self):
        self.skipped += 1
        self.advance()
    def save(self, game):
        if not self.saved:
            game.save_run(self)
            self.saved = True
