"""Local photo loading and importing."""
import hashlib
import io
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError

BASE = Path(__file__).resolve().parent
PHOTO_DIR = BASE / "photos"
PHOTO_KEYS = ("before_photo", "after_photo", "before_credit", "after_credit", "photo_note")


def photo_path(name):
    path = (BASE / name).resolve()
    if not path.is_relative_to(PHOTO_DIR.resolve()):
        raise ValueError("Photos must be stored in the project's photos folder.")
    return path


def read_photo(filename, size=(800, 450)):
    try:
        if Path(filename).stat().st_size > 12 * 1024 * 1024:
            raise ValueError("Choose a photo smaller than 12 MB.")
        with Image.open(filename) as image:
            if image.width * image.height > 20_000_000:
                raise ValueError("Choose a photo smaller than 20 megapixels.")
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail(size, Image.Resampling.LANCZOS)
            return image.copy()
    except (UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise ValueError("This file could not be read as a photo.") from error


def import_photo(filename):
    image = read_photo(filename)
    data = io.BytesIO()
    image.save(data, format="PNG")
    content = data.getvalue()
    name = "uploads/" + hashlib.sha256(content).hexdigest()[:24] + ".png"
    path = PHOTO_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(content)
    return "photos/" + name


def validate_photos(values):
    result = []
    for key in PHOTO_KEYS:
        value = values.get(key, "")
        if not isinstance(value, str) or len(value) > 2000:
            raise ValueError("Photo paths and credits must be text under 2000 characters.")
        value = value.strip()
        if key.endswith("_photo") and value:
            path = photo_path(value)
            if path.suffix.lower() != ".png" or not path.is_file():
                raise ValueError("Choose the photo again; its stored PNG file is missing.")
        result.append(value)
    return tuple(result)
