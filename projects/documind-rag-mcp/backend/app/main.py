"""FastAPI composition root for DocuMind REST and MCP.

The Streamable HTTP MCP server is mounted at /mcp on the same ASGI app, so
one deployment serves both protocols over the same service layer.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .core.errors import AppError
from .core.settings import get_settings
from .core.wiring import Container, build_container
from .mcp_server import build_mcp

_LOCAL_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


def _allowed_origins() -> list[str]:
    origins = list(_LOCAL_ORIGINS)
    configured = get_settings().frontend_origin.strip().rstrip("/")
    if configured.startswith(("https://", "http://")) and configured not in origins:
        origins.append(configured)
    return origins


def create_app(container: Container | None = None) -> FastAPI:
    resolved = container or build_container()
    mcp = build_mcp(resolved)
    mcp_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(
        title="DocuMind RAG + MCP",
        version="0.1.0",
        description="Evidence-gated PDF question answering with validated citations.",
        lifespan=lifespan,
    )
    app.state.container = resolved
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Session-ID"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "request_validation_error",
                    "message": "The request is missing or contains invalid fields.",
                }
            },
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An internal error occurred.",
                }
            },
        )

    app.include_router(router)
    app.mount("/", mcp_app)  # serves POST/GET /mcp; REST routes match first
    return app


app = create_app()
