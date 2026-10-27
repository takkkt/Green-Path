"""Battle rules; positions use a 900 by 360 arena, independent of the window."""
from dataclasses import dataclass
import math
import random

WIDTH, HEIGHT = 900, 360
COOLDOWNS = {"attack": .45, "parry": 1.7, "dodge": 1.0, "heavy": 5.5}

@dataclass
class Projectile:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    damage: int
    radius: int = 7

@dataclass
class Timing:
    kind: str
    started: float
    duration: float
    center: float
    perfect: float
    damage: int = 0
    def progress(self, now):
        return (now - self.started) / self.duration
    def quality(self, now):
        distance = abs(self.progress(now) - self.center)
        return "perfect" if distance <= self.perfect else "partial" if distance <= .23 else "failed"

def segment_distance(x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    length = dx * dx + dy * dy
    t = max(0, min(1, -(x0 * dx + y0 * dy) / length)) if length else 0
    return math.hypot(x0 + dx * t, y0 + dy * t)

class Combat:
    def __init__(self, stage, base_hp, hp=300, rng=None):
        self.stage = stage
        self.rng = rng or random.Random()
        pressure = (base_hp * 2 + 80 + stage * 90) * (.92 if stage else 1) * .82
        self.enemy_max = self.enemy_hp = max(60, round(pressure / 10) * 10)
        self.hp, self.x, self.y = hp, 450., 274.
        self.time = self.world_time = self.accumulator = 0.
        self.ready = dict.fromkeys(COOLDOWNS, 0.)
        self.invulnerable = self.dash_until = self.guard_until = 0.
        self.direction = self.dash_direction = (0, -1)
        self.qte = None
        self.shots, self.warnings = [], []
        self.wave = self.serial = 0
        self.next_wave = .35
        self.paused, self.state = False, "active"
        self.notice = "Keep moving. Watch the openings."

    @property
    def enraged(self):
        fraction, seconds = (.30, 30) if self.stage == 0 else (.25, 34)
        return self.enemy_hp <= self.enemy_max * fraction or self.world_time >= seconds
    def cooldown(self, action):
        return max(0, self.ready[action] - self.time)

    def incoming(self, horizon=None):
        candidates = []
        for shot in self.shots:
            rx, ry = shot.x - self.x, shot.y - self.y
            speed = shot.vx ** 2 + shot.vy ** 2
            approach = -(rx * shot.vx + ry * shot.vy)
            if not speed or approach <= 0:
                continue
            eta = approach / speed
            miss = math.hypot(rx + shot.vx * eta, ry + shot.vy * eta)
            margin = 5 if horizon is not None else 24
            if math.hypot(rx, ry) <= 180 + shot.radius and miss <= 7 + shot.radius + margin:
                if horizon is None or eta <= horizon:
                    candidates.append((math.hypot(rx, ry), shot.id, shot))
        return min(candidates, key=lambda entry: entry[:2])[-1] if candidates else None

    def begin_timing(self, action, damage=0):
        duration = max(.78, {"attack": 1.08, "heavy": 1.22, "parry": .98}[action] - min(self.stage, 7) * .02)
        perfect = max(.055, .085 - min(self.stage, 7) * .004) * (.75 if action == "heavy" else 1)
        self.qte = Timing(action, self.time, duration, self.rng.uniform(.57, .73), perfect, damage)
        if action == "heavy":
            self.ready[action] = self.time + COOLDOWNS[action]
        self.notice = "Caught it! K again in the bright centre." if action == "parry" else "Same key again in the bright centre."

    def catch(self):
        shot = self.incoming()
        if shot is None:
            return False
        if self.qte:
            action = self.qte.kind
            self.ready[action] = max(self.ready[action], self.time + COOLDOWNS[action])
        self.shots.remove(shot)
        self.guard_until = 0
        self.begin_timing("parry", shot.damage)
        return True

    def request(self, action):
        if self.paused or self.state != "active":
            return False
        if self.qte and action in ("confirm", self.qte.kind):
            self.resolve(self.qte.quality(self.time))
            return True
        if action not in COOLDOWNS or self.cooldown(action):
            return False
        if action == "dodge":
            if self.qte and self.qte.kind == "parry":
                return False
            if self.qte:
                old = self.qte.kind
                self.ready[old] = max(self.ready[old], self.time + COOLDOWNS[old])
                self.qte = None
            perfect = self.incoming(.24) is not None
            self.dash_direction, self.dash_until = self.direction, self.time + .18
            self.invulnerable = max(self.invulnerable, self.time + (.4 if perfect else .2))
            self.ready[action] = self.time + COOLDOWNS[action]
            self.guard_until = 0
            if perfect:
                self.ready["heavy"] = max(self.time, self.ready["heavy"] - .65)
            self.notice = "Perfect dodge! Heavy recharges a little faster." if perfect else "Keep your feet light."
        elif action == "parry":
            if not self.catch() and self.guard_until <= self.time:
                self.guard_until = self.time + .26
                self.notice = "Guard up. Catch a cyan-ringed shot."
        elif self.qte is None:
            self.guard_until = 0
            self.begin_timing(action)
        else:
            return False
        return True

    def resolve(self, quality):
        qte, self.qte = self.qte, None
        if qte.kind != "heavy":
            self.ready[qte.kind] = self.time + COOLDOWNS[qte.kind]
        damage = 0
        if qte.kind == "parry":
            if quality == "perfect":
                damage = 35 + self.stage * 4
                self.invulnerable = max(self.invulnerable, self.time + .45)
                self.shots = [s for s in self.shots if math.hypot(s.x - self.x, s.y - self.y) > 105]
            else:
                self.hurt(5 if quality == "partial" else qte.damage, force=True)
                damage = 16 + self.stage * 2 if quality == "partial" else 0
        elif quality != "failed":
            damage = {"attack": (13, 22), "heavy": (42, 72)}[qte.kind][quality == "perfect"]
        self.notice = f"{quality.title()} {qte.kind}!" + (f" A {damage}-point hit." if damage else " Reset and try again.")
        if self.state == "active":
            self.enemy_hp = max(0, self.enemy_hp - damage)
            if self.enemy_hp == 0:
                self.state = "won"

    def hurt(self, amount, force=False):
        if self.state == "active" and (force or self.time >= self.invulnerable):
            self.hp = max(0, self.hp - amount)
            self.invulnerable = self.time + .8
            self.notice = "The smog catches you. Find an opening!"
            if self.hp == 0:
                self.state = "lost"

    def advance(self, seconds, movement=(0, 0)):
        if self.paused or self.state != "active":
            return
        self.accumulator += max(0, seconds)
        while self.accumulator + 1e-10 >= 1 / 120 and self.state == "active":
            self.accumulator -= 1 / 120
            self.step(1 / 120, movement)

    def step(self, dt, movement):
        self.time += dt
        dx, dy = movement
        length = math.hypot(dx, dy)
        if length:
            self.direction = (dx / length, dy / length)
        dx, dy = self.dash_direction if self.time < self.dash_until else self.direction if length else (0, 0)
        speed = 690 if self.time < self.dash_until else 235
        old_x, old_y = self.x, self.y
        self.x = max(7, min(WIDTH - 7, self.x + dx * speed * dt))
        self.y = max(7, min(HEIGHT - 7, self.y + dy * speed * dt))
        if self.time <= self.guard_until and not self.cooldown("parry"):
            self.catch()
        self.world_time += dt * (.38 if self.qte and self.qte.kind == "parry" else 1)
        if self.qte and self.qte.progress(self.time) >= 1:
            self.resolve("failed")
        if self.state != "active":
            return
        if self.world_time >= self.next_wave:
            self.prepare_wave()
        for warning in self.warnings[:]:
            fires_at, shots, gap = warning
            if self.world_time >= fires_at:
                self.warnings.remove(warning)
                self.shots.extend(shots[:max(0, 110 - len(self.shots))])
        kept = []
        for shot in self.shots:
            px, py = shot.x, shot.y
            step = dt * (.38 if self.qte and self.qte.kind == "parry" else 1)
            shot.x += shot.vx * step
            shot.y += shot.vy * step
            if segment_distance(px - old_x, py - old_y, shot.x - self.x, shot.y - self.y) <= 7 + shot.radius:
                if not (self.qte and self.qte.kind == "parry"):
                    self.hurt(shot.damage)
            elif -35 < shot.x < WIDTH + 35 and -35 < shot.y < HEIGHT + 35:
                kept.append(shot)
        self.shots = kept

    def prepare_wave(self):
        stage = min(self.stage, 3)
        speed = (125 + min(self.stage, 7) * 20) * (.96 if self.stage else 1) * (1.12 if self.enraged else 1)
        damage = 14 + min(self.stage, 7) * 3 - (2 if self.stage else 0) + (2 if self.enraged else 0)
        interval = max(.66, 1.18 - min(self.stage, 7) * .12 + (.06 if self.stage else 0))
        self.next_wave = self.world_time + interval * (.9 if self.enraged else 1)
        pattern = self.wave % (2 + stage)
        self.wave += 1
        shots, gap = [], -1
        def add(x, y, vx, vy):
            self.serial += 1
            shots.append(Projectile(self.serial, x, y, vx, vy, damage))
        if pattern == 0 or stage == 0:
            x = WIDTH * (.5 if self.wave % 2 else .25)
            aim = math.atan2(self.y + 12, self.x - x)
            for offset in range(-(1 + stage), 2 + stage):
                angle = aim + offset * .22
                add(x, -12, math.cos(angle) * speed, math.sin(angle) * speed)
        elif pattern == 1:
            gap = self.rng.uniform(130, WIDTH - 130)
            for x in range(25, WIDTH, 42):
                if abs(x - gap) > max(100, 126 - stage * 6):
                    add(x, -12, 0, speed * .86)
        elif pattern == 2:
            x = -12 if self.wave % 2 else WIDTH + 12
            for y in (60, 160, 260):
                aim = math.atan2(self.y - y, self.x - x)
                for offset in (-.14, .14):
                    add(x, y, math.cos(aim + offset) * speed, math.sin(aim + offset) * speed)
        else:
            gap = max(95, min(WIDTH - 95, self.x + self.rng.choice((-120, 120))))
            for x in range(18, WIDTH, 32):
                if abs(x - gap) > 104:
                    add(x, -12, math.sin(self.wave) * 28, speed * .82)
        lead = max(.7, .96 - stage * .04)
        self.warnings.append((self.world_time + lead, shots, gap))
