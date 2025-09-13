from app.core.celery_app import celery
from celery import chain, states
from app.models.video import Video
from sqlalchemy.orm import Session
from app.core.database import get_db
from .translate import translate_text_task
from .tts import generate_tts_task
from .merge import merge_audio_video_task
from app.services.video_downloader import VideoDownloader
from app.services.transcriber import Transcriber
import os

# Initialize services
downloader = VideoDownloader()
transcriber = Transcriber(model_name="base")

@celery.task(name="transcribe_video")
def transcribe_video_task(video_id: int):
    """
    Task to download video, extract audio, and transcribe its content.
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get video from database
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": "Video not found"}
        
        # Update status to downloading
        video.status = "downloading"
        db.commit()
        
        # Download video and extract audio (saved into storage)
        result = downloader.download(video.youtube_url, str(video.id))
        if not result:
            video.status = "failed"
            db.commit()
            return {"status": "error", "message": "Failed to download video"}
            
        video_path, audio_path = result
        # Persist file paths
        video.video_path = video_path
        video.audio_path = audio_path
        db.commit()
        
        # Update status to transcribing
        video.status = "transcribing"
        db.commit()
        
        # Transcribe audio
        try:
            transcribed_text = transcriber.transcribe(audio_path)
            
            # Update video with transcription
            video.transcription = transcribed_text
            video.status = "transcribed"
            db.commit()
            
            # Chain the next tasks
            target_lang = video.target_language or "es"
            workflow = chain(
                translate_text_task.s(video_id, "auto", target_lang),
                generate_tts_task.s(),
                merge_audio_video_task.s()
            )
            workflow.apply_async()
            
            return {
                "status": "success", 
                "video_id": video_id, 
                "transcription": transcribed_text
            }
            
        finally:
            # No explicit cleanup here; VideoDownloader already removed temps
            pass
        
    except Exception as e:
        # Update status to failed if there's an error
        if video:
            video.status = "failed"
            db.commit()
        return {"status": "error", "message": str(e)}
