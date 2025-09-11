from celery import Celery

celery = Celery(
    "ytdub",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=[
        "app.workers.transcribe",
        "app.workers.translate",
        "app.workers.tts",
        "app.workers.merge"
    ]
)

# Optional configurations
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
