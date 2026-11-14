from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")

web_root = Path(__file__).parent / "web"
app.mount("/static", StaticFiles(directory=web_root / "static"), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(web_root / "index.html")

