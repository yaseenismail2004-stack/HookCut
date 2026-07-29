from __future__ import annotations

import os
from pathlib import Path, PurePath
from uuid import uuid4


REQUIRED_STORAGE_DIRECTORIES = (
    "uploads",
    "temp",
    "audio",
    "transcripts",
    "clips",
    "subtitles",
)


class StoragePathError(ValueError):
    """Raised when a requested path escapes the configured storage root."""


class StorageService:
    """Creates and resolves project-local storage paths without deleting media."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    def initialize(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        for directory in REQUIRED_STORAGE_DIRECTORIES:
            (self._root / directory).mkdir(parents=True, exist_ok=True)

    def directories_ready(self) -> bool:
        return all((self._root / directory).is_dir() for directory in REQUIRED_STORAGE_DIRECTORIES)

    def project_write_permission(self) -> bool:
        return self._root.is_dir() and os.access(self._root, os.W_OK)

    def resolve(self, relative_path: str | PurePath) -> Path:
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise StoragePathError("Storage paths must remain below the configured storage root.")
        candidate = (self._root / path).resolve()
        if not candidate.is_relative_to(self._root):
            raise StoragePathError("Storage paths must remain below the configured storage root.")
        return candidate

    def new_upload_path(self, extension: str) -> tuple[str, Path]:
        stored_filename = f"{uuid4().hex}{extension.lower()}"
        return stored_filename, self.resolve(PurePath("uploads") / stored_filename)

    def remove_upload(self, stored_filename: str) -> None:
        path = self.resolve(PurePath("uploads") / stored_filename)
        if path.is_file():
            path.unlink()
