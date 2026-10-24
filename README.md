# Green Path V4

A Python game about environmental challenges at Indian locations. It has a Tkinter interface, local accounts, a leaderboard, and location photos. Each mission starts with 300 HP. A victory earns 10 points and shows a before/after photo comparison before moving on.

## Run on Windows

Install Python 3.10 or newer with Tkinter, and Git. Pillow is the only extra Python package; it is listed in `requirements.txt`.

### Git Bash

```bash
git clone https://github.com/takkkt/Green-Path.git
cd Green-Path
py -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python green_path_v4.py
```

### PowerShell

```powershell
git clone https://github.com/takkkt/Green-Path.git
cd Green-Path
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe green_path_v4.py
```

If you downloaded the ZIP, extract it and open a terminal in the project folder. Start from `py -m venv .venv` in either set of commands.

## First start

The game creates `green_path_v4.sqlite3` locally. There are no preset accounts, passwords, or scores. The project owner should complete **First-time administrator setup** on their own computer. Other players can use **Create player account**.

An administrator can add or edit locations under **Manage locations**. Choose the before/after photos, enter their credits, and save. Imported photos are copied into `photos/uploads/`. The database and uploaded photos are ignored by Git.

## Files

- `green_path_v4.py`: screens, buttons and display updates.
- `green_path_core.py`: accounts, validation and SQLite storage.
- `mission.py`: health, attacks, score and mission state.
- `photos.py`: reading, resizing and importing photos.
- `starter_locations.json` and `starter_photos.json`: the default route and photo settings.

The game works offline after setup. Keep the bundled `photos` folder with the code. Photo pairs are illustrative contrasts from different dates and viewpoints, rather than proof of an actual cleanup. Sources and reuse licenses are in [PHOTO_CREDITS.md](PHOTO_CREDITS.md).
