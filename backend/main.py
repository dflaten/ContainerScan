from fastapi import FastAPI

from routers.containers import router as containers_router
from routers.labels import router as labels_router
from routers.rooms import router as rooms_router


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
