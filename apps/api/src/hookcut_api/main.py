from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hookcut_api.config import Settings, get_settings
from hookcut_api.db import create_session_factory
from hookcut_api.dependencies import get_storage_service
from hookcut_api.routers.videos import router as videos_router
from hookcut_api.schemas import CapabilitiesResponse, HealthResponse
from hookcut_api.services.capabilities import detect_capabilities
from hookcut_api.services.storage import StorageService


def create_app(settings: Settings | None = None) -> FastAPI:
    configured_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        storage = StorageService(configured_settings.resolved_storage_root)
        storage.initialize()
        app.state.storage = storage
        app.state.settings = configured_settings
        app.state.session_factory = create_session_factory(configured_settings)
        yield

    app = FastAPI(title="HookCut API", version=configured_settings.app_version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[configured_settings.web_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="hookcut-api", version=configured_settings.app_version)

    @app.get("/api/system/capabilities", response_model=CapabilitiesResponse, tags=["system"])
    def capabilities(storage: StorageService = Depends(get_storage_service)) -> CapabilitiesResponse:
        return detect_capabilities(configured_settings, storage)

    app.include_router(videos_router)
    return app


app = create_app()
