-- Tables used by database.py. Existing accounts and scores are kept.
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, salt BLOB NOT NULL,
    digest BLOB NOT NULL, iterations INTEGER NOT NULL, role TEXT NOT NULL DEFAULT 'player',
    failures INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, fact TEXT NOT NULL,
    enemy_name TEXT NOT NULL, enemy_type TEXT NOT NULL, enemy_hp INTEGER NOT NULL,
    art_style TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS location_photos (
    location_id INTEGER PRIMARY KEY REFERENCES locations(id) ON DELETE CASCADE,
    before_photo TEXT NOT NULL, after_photo TEXT NOT NULL, before_credit TEXT NOT NULL,
    after_credit TEXT NOT NULL, photo_note TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    score INTEGER NOT NULL, resolved INTEGER NOT NULL, skipped INTEGER NOT NULL,
    total INTEGER NOT NULL, hp INTEGER NOT NULL, outcome TEXT NOT NULL, ended_at TEXT NOT NULL);
