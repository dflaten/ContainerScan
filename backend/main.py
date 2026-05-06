from fastapi import FastAPI


app = FastAPI(
    title="ContainerScan API",
    version="0.1.0",
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
