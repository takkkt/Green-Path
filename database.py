"""Local accounts, starter locations and finished journey records."""
from datetime import datetime, timezone
import hashlib
import hmac
import json
import secrets
import sqlite3
from resources import APP_DIR, BASE, _prepare_resources

class Game:
    def __init__(self, database=None):
        _prepare_resources()
        self.db = sqlite3.connect(database or BASE / "green_path_v4.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.user_id = None
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript((APP_DIR / "schema.sql").read_text())
        if "art_style" not in [row[1] for row in self.db.execute("PRAGMA table_info(locations)")]:
            self.db.execute("ALTER TABLE locations ADD COLUMN art_style TEXT NOT NULL DEFAULT ''")
        if not self.db.execute("SELECT 1 FROM settings WHERE key='seeded'").fetchone():
            locations = json.loads((BASE / "starter_locations.json").read_text())
            with self.db:
                for place in locations:
                    enemy = place["polluter"]
                    self.db.execute("INSERT INTO locations(name,description,fact,enemy_name,enemy_type,enemy_hp) VALUES (?,?,?,?,?,?)",
                                    (place["name"], place["description"], place["fact"], enemy["name"], enemy["type"], enemy["hp"]))
                self.db.execute("INSERT INTO settings VALUES ('seeded','yes')")
        if not self.db.execute("SELECT 1 FROM settings WHERE key='photos_seeded'").fetchone():
            photos = json.loads((BASE / "starter_photos.json").read_text())
            with self.db:
                for photo in photos:
                    row = self.db.execute("SELECT id FROM locations WHERE name=?", (photo["name"],)).fetchone()
                    if row:
                        values = tuple(photo.get(k, "") for k in ("before_photo", "after_photo", "before_credit", "after_credit", "photo_note"))
                        self.db.execute("INSERT OR IGNORE INTO location_photos VALUES (?,?,?,?,?,?)", (row["id"],) + values)
                self.db.execute("INSERT INTO settings VALUES ('photos_seeded','yes')")
    def register(self, username, password):
        username = username.strip().lower()
        if not 3 <= len(username) <= 24 or not username[0].isalpha() or not username.replace("_", "").isalnum():
            raise ValueError("Use 3-24 letters, digits or underscores, starting with a letter.")
        if not 12 <= len(password) <= 128 or password.isspace():
            raise ValueError("Use a passphrase of 12-128 characters.")
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
        try:
            with self.db:
                self.db.execute("INSERT INTO users(username,salt,digest,iterations,role) VALUES (?,?,?,?,'player')",
                                (username, salt, digest, 600_000))
        except sqlite3.IntegrityError:
            raise ValueError("That username is already taken.") from None
    def login(self, username, password):
        self.user_id = None
        row = self.db.execute("SELECT * FROM users WHERE username=?", (username.strip().lower(),)).fetchone()
        if row and len(password) <= 128:
            digest = hashlib.pbkdf2_hmac("sha256", password.encode(), row["salt"], row["iterations"])
            if hmac.compare_digest(digest, row["digest"]):
                self.user_id = row["id"]
                return True
        return False
    def locations(self):
        return self.db.execute("SELECT l.*, p.* FROM locations l LEFT JOIN location_photos p ON l.id=p.location_id ORDER BY l.id").fetchall()
    def has_admin(self):
        return self.db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone() is not None
    def is_admin(self):
        return self.db.execute("SELECT 1 FROM users WHERE id=? AND role='admin'", (self.user_id,)).fetchone() is not None
    def require_admin(self):
        if not self.is_admin():
            raise PermissionError("Sign in with the admin account to edit maps.")
    def claim_admin(self):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.has_admin() or self.user_id is None:
                raise PermissionError("An admin is already set up. Use that account to edit maps.")
            if self.db.execute("UPDATE users SET role='admin' WHERE id=?", (self.user_id,)).rowcount != 1:
                raise PermissionError("Log in before setting up admin.")
    def save_location(self, item, location_id=None):
        self.require_admin()
        values = [str(item.get(key) or "").strip() for key in ("name", "description", "fact", "art_style", "enemy_hp")]
        if not all(values[:3]) or len(values[0]) > 60 or any(len(value) > 1200 for value in values[1:3]):
            raise ValueError("Give the map a name (up to 60 characters), a story and a fact (up to 1,200 each).")
        if values[3] not in ("taj", "river", "city", "glacier", "factory") or not values[4].isascii() or not values[4].isdigit() or not 1 <= int(values[4]) <= 200:
            raise ValueError("Choose a line drawing and a whole-number strength from 1 to 200.")
        with self.db:
            if self.db.execute("SELECT 1 FROM locations WHERE lower(name)=lower(?) AND id!=?", (values[0], location_id or -1)).fetchone():
                raise ValueError("That map name is already in the route. Try a different name.")
            if location_id is None:
                return self.db.execute("INSERT INTO locations(name,description,fact,art_style,enemy_hp,enemy_name,enemy_type) VALUES (?,?,?,?,?,'Pollution','Custom')", values).lastrowid
            if self.db.execute("UPDATE locations SET name=?,description=?,fact=?,art_style=?,enemy_hp=? WHERE id=?", values + [location_id]).rowcount != 1:
                raise ValueError("This map has already been removed. Return to the route list.")
            return location_id
    def delete_location(self, location_id):
        self.require_admin()
        with self.db:
            if self.db.execute("DELETE FROM locations WHERE id=?", (location_id,)).rowcount != 1:
                raise ValueError("This map has already been removed.")
    def save_run(self, mission):
        if self.user_id is None:
            raise PermissionError("Log in before saving.")
        with self.db:
            self.db.execute("INSERT INTO runs(user_id,score,resolved,skipped,total,hp,outcome,ended_at) VALUES (?,?,?,?,?,?,?,?)",
                            (self.user_id, mission.score, mission.resolved, mission.skipped, len(mission.locations),
                             mission.hp, mission.outcome, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    def leaderboard(self):
        return self.db.execute("SELECT u.username, MAX(r.score) AS best FROM users u JOIN runs r ON u.id=r.user_id GROUP BY u.id ORDER BY best DESC,u.username LIMIT 10").fetchall()
    def close(self):
        self.db.close()
