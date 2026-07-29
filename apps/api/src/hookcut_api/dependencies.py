from __future__ import annotations

from typing import cast

from fastapi import Request

from hookcut_api.services.storage import StorageService


def get_storage_service(request: Request) -> StorageService:
    return cast(StorageService, request.app.state.storage)
