from app.core.celery_app import celery
from app.models.video import Video
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.translator import Translator
from app.core.logging import get_logger

logger = get_logger(__name__)
translator = Translator()

@celery.task(name="translate_text")
def translate_text_task(video_id: int, source_lang: str, target_lang: str):
    """
    Task to translate the transcribed text to the target language.
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Update video status
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": "Video not found"}
        
        if not video.transcription:
            return {"status": "error", "message": "No transcription available"}
        
        video.status = "translating"
        db.commit()

        try:
            # Translate the text
            translated_text = translator.translate(
                text=video.transcription,
                target_language=target_lang,
                source_language=source_lang if source_lang != "auto" else None
            )
            
            # Update video with translation
            video.translated_text = translated_text
            video.status = "translated"
            db.commit()
            
            logger.info(f"Successfully translated video {video_id} to {target_lang}")
            return {
                "status": "success", 
                "video_id": video_id,
                "text": translated_text,
                "target_lang": target_lang
            }
            
        except Exception as translation_error:
            logger.error(f"Translation failed for video {video_id}: {str(translation_error)}")
            raise translation_error
        
    except Exception as e:
        # Update status to failed if there's an error
        if video:
            video.status = "failed"
            db.commit()
        logger.error(f"Error in translate_text_task for video {video_id}: {str(e)}")
        return {"status": "error", "message": str(e)}
