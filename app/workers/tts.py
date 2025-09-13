from app.core.celery_app import celery
from app.models.video import Video
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.tts import AllTalkTTS
from app.core.logging import get_logger
from app.services.storage_service import StorageService
import os

logger = get_logger(__name__)
tts_service = AllTalkTTS()
storage_service = StorageService()

@celery.task(name="generate_tts")
def generate_tts_task(chain_data: dict):
    """
    Task to generate text-to-speech audio from translated text using AllTalk TTS.
    """
    try:
        video_id = chain_data["video_id"]
        text = chain_data["text"]
        target_lang = chain_data["target_lang"]
        
        # Get database session
        db = next(get_db())
        
        # Update video status
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": "Video not found"}
        
        video.status = "generating_audio"
        db.commit()

        try:
            # Generate speech using AllTalk
            output_filename = f"audio_{video_id}.wav"
            audio_path = tts_service.generate_speech(
                text=text,
                output_file=output_filename,
                language=target_lang
            )
            
            logger.info(f"Generated audio file for video {video_id}: {audio_path}")

            # Move generated audio into storage-managed location
            try:
                stored_audio_path = storage_service.save_tts_audio(audio_path, str(video_id))
                # Update chain data with the stored path
                audio_path = stored_audio_path
            except Exception as storage_err:
                logger.error(f"Failed to store TTS audio for video {video_id}: {storage_err}")
            
            # Update status
            video.status = "audio_generated"
            db.commit()
            
            chain_data.update({
                "status": "success",
                "audio_path": audio_path,
            })
            return chain_data
            
        except Exception as tts_error:
            logger.error(f"TTS generation failed for video {video_id}: {str(tts_error)}")
            raise tts_error
        
    except Exception as e:
        # Update status to failed if there's an error
        if 'video' in locals():
            video.status = "failed"
            db.commit()
        logger.error(f"Error in generate_tts_task for video {video_id}: {str(e)}")
        return {"status": "error", "message": str(e)}
