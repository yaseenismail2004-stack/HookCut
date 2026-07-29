from __future__ import annotations

from pathlib import Path

import pytest

from hookcut_api.services.storage import REQUIRED_STORAGE_DIRECTORIES, StoragePathError, StorageService


def test_storage_initialization_creates_required_directories(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "storage")
    storage.initialize()
    assert storage.directories_ready() is True
    assert all((storage.root / name).is_dir() for name in REQUIRED_STORAGE_DIRECTORIES)


@pytest.mark.parametrize("unsafe_path", ["../outside.mp4", "uploads/../../outside.mp4", "C:/outside.mp4"])
def test_storage_rejects_path_traversal(tmp_path: Path, unsafe_path: str) -> None:
    storage = StorageService(tmp_path / "storage")
    storage.initialize()
    with pytest.raises(StoragePathError):
        storage.resolve(unsafe_path)
