from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/auth/openapi.json",
    docs_url="/api/v1/openapi",
    redoc_url="/api/v1/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

# Healthcheck
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
