import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.core.config import settings
from src.grpc import start_grpc_server, stop_grpc_server
from src.grpc.client import VenueDirectoryClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    venue_client = VenueDirectoryClient.from_settings()
    app.state.venue_directory_client = venue_client

    grpc_server, grpc_health = await start_grpc_server()

    if settings.GRPC_STARTUP_CHECKS_ENABLED:
        try:
            await venue_client.wait_until_serving()
        except Exception as exc:
            logger.warning(
                "gRPC startup health check failed for venue-directory: %s; continuing with lazy reconnect",
                exc,
            )
    app.state.grpc_server = grpc_server
    app.state.grpc_health = grpc_health
    try:
        yield
    finally:
        await stop_grpc_server(grpc_server, grpc_health)
        await venue_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        root_path=settings.APP_ROOT_PATH,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS", "PUT"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router)
    return app


app = create_app()

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
