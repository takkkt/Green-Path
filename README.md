# Green Path

A Python/Tkinter game about fighting pollution at the Taj Mahal, the Ganga, Delhi and Gangotri. Dodge the pollutants, time your attacks and try to finish the route with your health intact.

Project by **Akshith Kesari**.

## Run the game

Use Python 3.10 or newer with Tkinter. Pillow is the only extra package.

Clone this repository, or download and extract its ZIP. Open a terminal in the project folder.

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python green_path_v4.py
```

**Windows**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe green_path_v4.py
```

After the first setup, just run the last command. Keep all the Python files, `dialogue.json`, `schema.sql` and `green_path_assets.zip` together. Leave the asset ZIP zipped. If you update the files, close the old game window and launch it again.

The Python.org installers for Windows and macOS include Tkinter. On Linux, install your distribution's Python Tk package if Tkinter is missing.

## Play

Create a player with a username and a passphrase of 12-128 characters, then sign in.

| Key | Action |
| --- | --- |
| WASD / arrows | Move |
| J / 1 | Attack |
| K / 2 | Parry |
| Space / 3 | Dodge |
| L / 4 | Heavy attack |
| Enter | Confirm a timing event |
| P / Esc | Pause or resume |

Attack and heavy need two presses: open the timing bar, then press again in the cyan zone. Heavy does more damage and takes 5.5 seconds to recharge.

For a parry, look for the cyan ring around an incoming shot. Press K to catch it and K again to time the counter. A perfect parry blocks the hit and damages the enemy. A partial parry costs five HP and deals less damage. A failed parry takes the caught shot's damage. Holding the key does not count as a second press.

You start with 300 HP for the whole route. Clearing a stop earns ten points; skipping earns none. Later stops bring more pressure. Switching away from the game pauses the fight.

## Edit maps

An admin account gets **Edit maps** on the home screen. If this copy has no admin yet, sign in, choose **Set up admin** and confirm. That gives your current account the admin role.

Choose a map to edit or remove, or use **Add a map**. You can change its name, arrival story, fact, line drawing and base strength. New maps use one of five drawing templates; existing maps keep their photos. The editor does not upload new photos.

Changes apply to your next route. Removing a map asks for confirmation and keeps saved scores and photo files.

## Files and presentation

The game is split into twelve Python modules:

| Area | Files |
| --- | --- |
| Startup and interface | `green_path_v4.py`, `app.py`, `theme.py` |
| SQL, admin and files | `database.py`, `admin.py`, `resources.py` |
| Rules, route and dialogue | `combat.py`, `mission.py`, `dialogue.py` |
| Animation, drawings and photos | `arena.py`, `art.py`, `photos.py` |

The [four-person presentation guide](docs/Green_Path_Four_Speaker_Guide.pdf) explains the connections, movement calculations, Taj Mahal drawing and the functions behind each visible feature.

`schema.sql` defines the SQLite tables. `dialogue.json` holds the story text and fact sources. The asset ZIP contains starter data and photos.

## Saves and photo credits

New installs create `green_path_data` for accounts, photos and scores. Keep it when updating. An older database beside the launcher is used automatically. Finished results are saved; an unfinished battle does not resume after restarting.

The game works offline after setup. Photo pairs are illustrative contrasts, not proof of a real cleanup. Sources and reuse licences are in [PHOTO_CREDITS.md](PHOTO_CREDITS.md); pollution fact sources are also listed in the game's Credits window.
