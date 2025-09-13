from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, HttpUrl

from ..core.database import get_db
from ..models.video import Video
from ..workers.transcribe import transcribe_video_task
from ..workers.translate import translate_text_task
from ..workers.tts import generate_tts_task
from ..workers.merge import merge_audio_video_task

router = APIRouter()

class VideoRequest(BaseModel):
    youtube_url: HttpUrl
    target_language: str

class VideoResponse(BaseModel):
    id: int
    youtube_url: str
    status: str
    transcription: Optional[str] = None
    translated_text: Optional[str] = None
    target_language: Optional[str] = None
    output_path: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None

@router.post("/process", response_model=VideoResponse)
def process_video(request: VideoRequest, db: Session = Depends(get_db)):
    """
    Process a YouTube video for dubbing.
    """
    # Check if video already exists
    existing_video = db.query(Video).filter(Video.youtube_url == str(request.youtube_url)).first()
    if existing_video:
        return VideoResponse(
            id=existing_video.id,
            youtube_url=existing_video.youtube_url,
            status=existing_video.status,
            transcription=existing_video.transcription,
            translated_text=existing_video.translated_text,
            target_language=existing_video.target_language,
            output_path=existing_video.output_path
        )

    # Create new video record
    video = Video(
        youtube_url=str(request.youtube_url),
        status="pending",
        target_language=request.target_language
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Start the processing chain
    task = transcribe_video_task.delay(video.id)

    return VideoResponse(
        id=video.id,
        youtube_url=video.youtube_url,
        status=video.status,
        target_language=video.target_language,
        output_path=video.output_path
    )

@router.get("/video/{video_id}", response_model=VideoResponse)
def get_video_status(video_id: int, db: Session = Depends(get_db)):
    """
    Get the status of a video processing job.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return VideoResponse(
        id=video.id,
        youtube_url=video.youtube_url,
        status=video.status,
        transcription=video.transcription,
        translated_text=video.translated_text,
        target_language=video.target_language,
        output_path=video.output_path
    )

@router.post("/test/transcribe/{video_id}", response_model=TaskResponse)
async def test_transcribe(video_id: int):
    """
    Test the transcription task
    """
    task = transcribe_video_task.delay(video_id)
    return TaskResponse(task_id=task.id, status=task.status)

@router.post("/test/translate/{video_id}", response_model=TaskResponse)
async def test_translate(video_id: int):
    """
    Test the translation task
    """
    task = translate_text_task.delay(video_id, "en", "es")
    return TaskResponse(task_id=task.id, status=task.status)

@router.post("/test/tts/{video_id}", response_model=TaskResponse)
async def test_tts(video_id: int):
    """
    Test the TTS task
    """
    chain_data = {"video_id": video_id, "text": "Sample text", "target_lang": "es"}
    task = generate_tts_task.delay(chain_data)
    return TaskResponse(task_id=task.id, status=task.status)

@router.post("/test/merge/{video_id}", response_model=TaskResponse)
async def test_merge(video_id: int):
    """
    Test the merge task
    """
    chain_data = {"video_id": video_id, "audio_path": "/tmp/sample.wav"}
    task = merge_audio_video_task.delay(chain_data)
    return TaskResponse(task_id=task.id, status=task.status)
