import io
import uuid
from pathlib import Path
from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from .config import get_settings


def data_path(*parts: str) -> Path:
    p = Path(get_settings().data_dir).joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _read_limited(upload: UploadFile, max_mb: int) -> bytes:
    data = upload.file.read(max_mb * 1024 * 1024 + 1)
    if not data:
        raise ValueError("The file is empty.")
    if len(data) > max_mb * 1024 * 1024:
        raise ValueError(f"The file is larger than {max_mb} MB.")
    return data


def open_image(data: bytes) -> Image.Image:
    try:
        Image.open(io.BytesIO(data)).verify()
        img = Image.open(io.BytesIO(data))
        if img.format not in ("JPEG", "PNG"):
            raise ValueError("Upload a JPG or PNG image.")
        return ImageOps.exif_transpose(img)
    except (UnidentifiedImageError, OSError):
        raise ValueError("This file is not a valid JPG or PNG image.")


def save_student_image(upload: UploadFile, folder: str) -> str:
    """Validate, re-encode (strips metadata/embedded payloads) and store. Returns relative path."""
    img = open_image(_read_limited(upload, get_settings().max_image_mb))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img.thumbnail((1200, 1200))
    rel = f"{folder}/{uuid.uuid4().hex}.jpg"
    img.save(data_path(rel), "JPEG", quality=90)
    return rel


def save_template_preview(upload: UploadFile) -> None:
    img = open_image(_read_limited(upload, 10))
    img.thumbnail((2400, 2400))
    img.convert("RGB").save(data_path("template", "preview.jpg"), "JPEG", quality=92)


def delete_file(rel: str) -> None:
    try:
        data_path(rel).unlink(missing_ok=True)
    except OSError:
        pass
