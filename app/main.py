from fastapi import FastAPI
from .routes import video

app = FastAPI(
    title="YouTube Dubbing MVP",
    version="0.1.0"
)

app.include_router(video.router, prefix="/api/v1/video", tags=["video"])