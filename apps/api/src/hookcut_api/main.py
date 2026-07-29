from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hookcut_api.config import Settings, get_settings
from hookcut_api.db import create_session_factory
from hookcut_api.dependencies import get_storage_service
from hookcut_api.routers.videos import router as videos_router
from hookcut_api.routers.jobs import router as jobs_router
from hookcut_api.schemas import CapabilitiesResponse, HealthResponse
from hookcut_api.services.capabilities import detect_capabilities
from hookcut_api.services.storage import StorageService
from hookcut_api.services.transcription import TranscriptionProviderRegistry, build_provider_registry
from hookcut_api.services.worker import LocalJobWorker


def _configure_development_logging() -> None:
    logger = logging.getLogger("hookcut_api")
    logger.setLevel(logging.INFO)
    if any(handler.get_name() == "hookcut-development" for handler in logger.handlers):
        return
    handler = logging.StreamHandler()
    handler.set_name("hookcut-development")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def create_app(settings: Settings | None = None) -> FastAPI:
    _configure_development_logging()
    configured_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        storage = StorageService(configured_settings.resolved_storage_root)
        storage.initialize()
        app.state.storage = storage
        app.state.settings = configured_settings
        app.state.session_factory = create_session_factory(configured_settings)
        legacy_provider = getattr(app.state, "transcription_provider", None)
        # Test-only dependency injection remains supported, while production always
        # uses the explicit Gemini/OpenAI registry with no automatic fallback.
        providers = getattr(app.state, "transcription_providers", None)
        if not isinstance(providers, TranscriptionProviderRegistry):
            providers = TranscriptionProviderRegistry({"gemini": legacy_provider, "openai": legacy_provider}) if legacy_provider is not None else build_provider_registry(configured_settings)
        app.state.transcription_providers = providers
        app.state.worker = LocalJobWorker(app.state.session_factory, storage, configured_settings, providers)
        if configured_settings.worker_enabled:
            app.state.worker.start()
        yield
        app.state.worker.stop()

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
        return detect_capabilities(configured_settings, storage, bool(app.state.worker.running), app.state.transcription_providers.configured_names())

    app.include_router(videos_router)
    app.include_router(jobs_router)
    return app


app = create_app()
