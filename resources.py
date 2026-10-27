"""Default assets and save paths; old databases keep their original location."""
import hashlib
import io
from pathlib import Path
import zipfile

APP_DIR = Path(__file__).resolve().parent
BASE = APP_DIR if (APP_DIR / "green_path_v4.sqlite3").exists() else APP_DIR / "green_path_data"
_RESOURCE_NAMES = ("starter_locations.json", "starter_photos.json", "PHOTO_CREDITS.md") + tuple(
    f"photos/{place}_{kind}.png" for place in ("taj", "ganga", "delhi", "glacier") for kind in ("before", "after"))
_ASSET_SHA256 = "9c8c90077f7cc174421cd0cad18882a7bc0fb8d39d7bc3517f9db650abd05bb3"

def _prepare_resources():
    if all((BASE / name).is_file() for name in _RESOURCE_NAMES):
        return
    archive = APP_DIR / "green_path_assets.zip"
    if not archive.is_file():
        raise ValueError("Keep green_path_assets.zip in the same folder as the Python files.")
    content = archive.read_bytes()
    if hashlib.sha256(content).hexdigest() != _ASSET_SHA256:
        raise ValueError("The asset archive is damaged. Download it again.")
    with zipfile.ZipFile(io.BytesIO(content)) as bundle:
        for name in _RESOURCE_NAMES:
            target = BASE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with target.open("xb") as output:
                    output.write(bundle.read(name))
            except FileExistsError:
                pass
