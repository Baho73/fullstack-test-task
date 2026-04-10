# FILE: backend/src/storage.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Файловые операции: сохранение upload на диск (streaming), удаление, резолв путей.
#   SCOPE: save_file, delete_file, get_path, STORAGE_DIR
#   DEPENDS: none
#   LINKS: M-STORAGE, V-M-STORAGE
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   STORAGE_DIR - base storage directory (created on import)
#   save_file - stream UploadFile to disk, return (stored_name, size)
#   delete_file - remove stored file from disk (safe if missing)
#   get_path - resolve stored_name to full Path, raise if missing
# END_MODULE_MAP

import logging
from pathlib import Path

from fastapi import UploadFile

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "files"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 64 * 1024  # 64 KB chunks for streaming


# START_CONTRACT: save_file
#   PURPOSE: Stream upload content to disk in chunks, return (stored_name, file_size).
#   INPUTS: { upload_file: UploadFile, file_id: str }
#   OUTPUTS: { tuple[str, int] - (stored_name, size_in_bytes) }
#   SIDE_EFFECTS: Creates a file on disk at STORAGE_DIR / stored_name.
#   LINKS: M-SERVICE-FILES
# END_CONTRACT: save_file

# START_BLOCK_SAVE_FILE
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
# END_BLOCK_SAVE_FILE


# START_CONTRACT: delete_file
#   PURPOSE: Remove a stored file from disk. Safe to call if file doesn't exist.
#   INPUTS: { stored_name: str }
#   OUTPUTS: none
#   SIDE_EFFECTS: Removes file from disk if it exists.
#   LINKS: M-SERVICE-FILES
# END_CONTRACT: delete_file

# START_BLOCK_DELETE_FILE
def delete_file(stored_name: str) -> None:
    stored_path = STORAGE_DIR / stored_name
    if stored_path.exists():
        stored_path.unlink()
# END_BLOCK_DELETE_FILE


# START_CONTRACT: get_path
#   PURPOSE: Resolve stored_name to full filesystem path. Raises FileNotFoundError if missing.
#   INPUTS: { stored_name: str }
#   OUTPUTS: { Path - full path to stored file }
#   SIDE_EFFECTS: none
#   LINKS: M-SERVICE-FILES, M-TASKS
# END_CONTRACT: get_path

# START_BLOCK_GET_PATH
def get_path(stored_name: str) -> Path:
    stored_path = STORAGE_DIR / stored_name
    if not stored_path.exists():
        raise FileNotFoundError(f"Stored file not found: {stored_name}")
    return stored_path
# END_BLOCK_GET_PATH

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.0.0 - Extracted from service.py; streaming upload via chunks instead of
#                  reading entire file into memory; safe delete; get_path with FileNotFoundError]
# END_CHANGE_SUMMARY
