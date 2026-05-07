from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import get_settings
from routers.containers import router as containers_router
from routers.images import router as images_router
from routers.labels import router as labels_router
from routers.rooms import router as rooms_router


settings = get_settings()
Path(settings.image_storage_path).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ContainerScan API",
    version="0.1.0",
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    """Report basic API liveness.

    Returns:
        dict[str, str]: A minimal status payload indicating the API is up.
    """
    return {"status": "ok"}


app.include_router(rooms_router)
app.include_router(labels_router)
app.include_router(containers_router)
app.include_router(images_router)
app.mount("/images", StaticFiles(directory=settings.image_storage_path), name="images")
