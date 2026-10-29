# Green Path

Green Path is a Python game about environmental challenges at the Taj Mahal, the Ganga, Delhi and Gangotri. Players move around an arena, avoid incoming pollutants, and use timed attacks, parries and dodges to clear each location. Health carries across the route, and finished results can be recorded on a local leaderboard.

The interface uses Tkinter, with line drawings, location photos and short environmental facts. Accounts, map settings and scores are stored locally. The game works offline after setup.

## Requirements

- Python 3.10 or newer with Tkinter.
- Pillow, installed from `requirements.txt`.
- Git if cloning the repository; otherwise download and extract the repository ZIP.

Keep the Python files, `dialogue.json`, `schema.sql`, `PHOTO_CREDITS.md` and `green_path_assets.zip` in the project folder. Leave `green_path_assets.zip` zipped; the game prepares its resources automatically.

## Run on Windows

Open PowerShell in the project folder. If cloning the repository, run these first:

```powershell
git clone https://github.com/takkkt/Green-Path.git
cd Green-Path
```

Create a virtual environment, install the requirement and start the game:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe green_path_v4.py
```

For later launches, run only the last command.

If using Git Bash instead of PowerShell:

```bash
py -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python green_path_v4.py
```

## Run on macOS or Linux

Open a terminal in the project folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python green_path_v4.py
```

On Linux, install your distribution's Python Tk package if Tkinter is missing. You can check Tkinter with `python3 -m tkinter`.

## First start and controls

Create a player account with a username and a passphrase of 12-128 characters, then sign in. Start the route from the home screen.

| Key | Action |
| --- | --- |
| WASD / arrow keys | Move |
| J / 1 | Attack |
| K / 2 | Parry |
| Space / 3 | Dodge |
| L / 4 | Heavy attack |
| Enter | Confirm a timing event |
| P / Esc | Pause or resume |

Attack and heavy attack use a timing bar: press once to begin, then press again in the highlighted zone. To parry, catch an incoming shot when its cyan ring appears, then press again to time the counter. Switching away from the game pauses combat.

If this installation has no administrator, sign in and choose **Set up admin**. An administrator can use **Edit maps** to add, edit or remove locations. Map changes apply to the next route; the current editor preserves existing photo pairs and does not import new photos.

## Saved data

New installations create a `green_path_data` folder for accounts, resources and scores. Keep that folder when updating. If `green_path_v4.sqlite3` already exists beside the launcher, the game uses that location instead. Finished results are saved locally; an unfinished battle cannot be resumed after restarting.

Photo pairs are illustrative contrasts from different dates and viewpoints. Photo sources and reuse licences are listed in [PHOTO_CREDITS.md](PHOTO_CREDITS.md), and fact sources are available in the game's Credits window.
