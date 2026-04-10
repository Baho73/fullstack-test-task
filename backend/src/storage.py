#

import logging
from pathlib import Path

from fastapi import UploadFile

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "files"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 64 * 1024  # 64 KB chunks for streaming


async def save_file(upload_file: UploadFile, file_id: str) -> tuple[str, int]:
    suffix = Path(upload_file.filename or "").suffix
    stored_name = f"{file_id}{suffix}"
    stored_path = STORAGE_DIR / stored_name

    size = 0
    with stored_path.open("wb") as f:
        while True:
            chunk = await upload_file.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
            size += len(chunk)

    return stored_name, size


def delete_file(stored_name: str) -> None:
    stored_path = STORAGE_DIR / stored_name
    if stored_path.exists():
        stored_path.unlink()


def get_path(stored_name: str) -> Path:
    stored_path = STORAGE_DIR / stored_name
    if not stored_path.exists():
        raise FileNotFoundError(f"Stored file not found: {stored_name}")
    return stored_path
