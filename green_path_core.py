"""Accounts, locations and saved scores."""
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time

START_HP = 300
POINTS_PER_WIN = 10
HASH_ITERATIONS = 600_000
MAX_FAILURES = 5
LOCK_SECONDS = 60
ATTACKS = [("Quick Sweep", 10, 11), ("Heavy Splash", 7, 15),
           ("Power Clean", 3, 20)]
BASE = Path(__file__).resolve().parent


def clean_text(value, maximum=2000):
    """Allow spaces and punctuation, but not blank or terminal-control text."""
    if not isinstance(value, str):
        raise ValueError("Text must be a string.")
    value = value.strip()
    if not value or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError(f"Enter 1 to {maximum} characters without control characters.")
    return value


def normalize_username(value):
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,23}", value):
        raise ValueError("Username: 3-24 letters, digits or underscores; start with a letter.")
    return value


def validate_password(password):
    if not 12 <= len(password) <= 128 or password.isspace():
        raise ValueError("Use a password/passphrase of 12-128 characters.")


def password_digest(password, salt, iterations=HASH_ITERATIONS):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def validate_location(item):
    if not isinstance(item, dict) or not isinstance(item.get("polluter"), dict):
        raise ValueError("Invalid location record.")
    enemy = item["polluter"]
    hp = enemy.get("hp")
    if type(hp) is not int or not 1 <= hp <= 1000:
        raise ValueError("Polluter HP must be a whole number from 1 to 1000.")
    return (clean_text(item.get("name"), 100),
            clean_text(item.get("description")), clean_text(item.get("fact")),
            clean_text(enemy.get("name"), 100), clean_text(enemy.get("type"), 100), hp)


class Game:
    """Owns the database connection and the current in-memory login session."""

    def __init__(self, database=BASE / "green_path_v3.sqlite3",
                 seed_file=BASE / "starter_locations.json"):
        self.user_id = None
        self.db = sqlite3.connect(database)
        self.db.row_factory = sqlite3.Row
        try:
            self.db.execute("PRAGMA foreign_keys = ON")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                    salt BLOB NOT NULL, digest BLOB NOT NULL,
                    iterations INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('player','admin')),
                    failures INTEGER NOT NULL DEFAULT 0,
                    locked_until REAL NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                    description TEXT NOT NULL, fact TEXT NOT NULL,
                    enemy_name TEXT NOT NULL, enemy_type TEXT NOT NULL,
                    enemy_hp INTEGER NOT NULL CHECK(enemy_hp BETWEEN 1 AND 1000));
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                    score INTEGER NOT NULL CHECK(score >= 0),
                    resolved INTEGER NOT NULL, skipped INTEGER NOT NULL,
                    total INTEGER NOT NULL, hp INTEGER NOT NULL,
                    outcome TEXT NOT NULL CHECK(outcome IN
                        ('completed','visited','defeated','abandoned','interrupted')),
                    ended_at TEXT NOT NULL);
            """)
            if not self.db.execute("SELECT 1 FROM settings WHERE key='seeded'").fetchone():
                data = json.loads(Path(seed_file).read_text(encoding="utf-8-sig"))
                if not isinstance(data, list) or not data:
                    raise ValueError("Starter locations must be a non-empty JSON list.")
                records = [validate_location(item) for item in data]
                with self.db:
                    self.db.executemany("""INSERT INTO locations
                        (name,description,fact,enemy_name,enemy_type,enemy_hp)
                        VALUES (?,?,?,?,?,?)""", records)
                    self.db.execute("INSERT INTO settings VALUES ('seeded','yes')")
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.logout()
        self.db.close()

    def logout(self):
        self.user_id = None

    def current_user(self, admin=False):
        user = self.db.execute("SELECT * FROM users WHERE id=?", (self.user_id,)).fetchone()
        if user is None or (admin and user["role"] != "admin"):
            raise PermissionError("Please log in with the required account role.")
        return user

    def register(self, username, password, setup_admin=False):
        username = normalize_username(username)
        validate_password(password)
        salt = secrets.token_bytes(16)
        digest = password_digest(password, salt)
        # An immediate transaction makes the first-admin check and insert atomic.
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if setup_admin and self.db.execute(
                    "SELECT 1 FROM users WHERE role='admin'").fetchone():
                raise ValueError("An administrator already exists. Setup is disabled.")
            self.db.execute("""INSERT INTO users
                (username,salt,digest,iterations,role) VALUES (?,?,?,?,?)""",
                (username, salt, digest, HASH_ITERATIONS, "admin" if setup_admin else "player"))
            self.db.commit()
        except sqlite3.IntegrityError:
            self.db.rollback()
            raise ValueError("That username is unavailable.")
        except BaseException:
            self.db.rollback()
            raise

    def login(self, username, password, now=None):
        self.logout()  # A failed switch must not retain the previous user's access.
        now = time.time() if now is None else now
        username = normalize_username(username)
        if len(password) > 128:
            return False
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            user = self.db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            if user is None:
                password_digest(password, bytes(16))  # Similar work for unknown accounts.
                return False
            if user["locked_until"] > now:
                return False
            candidate = password_digest(password, user["salt"], user["iterations"])
            if not hmac.compare_digest(candidate, user["digest"]):
                failures = (0 if user["locked_until"] else user["failures"]) + 1
                until = now + LOCK_SECONDS if failures >= MAX_FAILURES else 0
                self.db.execute("UPDATE users SET failures=?, locked_until=? WHERE id=?",
                                (failures, until, user["id"]))
                return False
            self.db.execute("UPDATE users SET failures=0, locked_until=0 WHERE id=?", (user["id"],))
        self.user_id = user["id"]
        return True

    def locations(self):
        return self.db.execute("SELECT * FROM locations ORDER BY id").fetchall()

    def save_location(self, item, location_id=None):
        self.current_user(admin=True)
        values = validate_location(item)
        with self.db:
            if location_id is None:
                self.db.execute("""INSERT INTO locations
                    (name,description,fact,enemy_name,enemy_type,enemy_hp)
                    VALUES (?,?,?,?,?,?)""", values)
            else:
                result = self.db.execute("""UPDATE locations SET name=?,description=?,fact=?,
                    enemy_name=?,enemy_type=?,enemy_hp=? WHERE id=?""", values + (location_id,))
                if result.rowcount != 1:
                    raise ValueError("Location no longer exists.")

    def delete_location(self, location_id):
        self.current_user(admin=True)
        with self.db:
            result = self.db.execute("DELETE FROM locations WHERE id=?", (location_id,))
            if result.rowcount != 1:
                raise ValueError("Location no longer exists.")

    def save_run(self, score, resolved, skipped, total, hp, outcome):
        user = self.current_user()
        with self.db:
            self.db.execute("""INSERT INTO runs
                (user_id,score,resolved,skipped,total,hp,outcome,ended_at)
                VALUES (?,?,?,?,?,?,?,?)""", (user["id"], score, resolved, skipped,
                total, hp, outcome, datetime.now(timezone.utc).isoformat(timespec="seconds")))
