from app.core.celery_app import celery
from app.models.video import Video
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.video_processor import VideoProcessor
from app.core.logging import get_logger
from app.services.storage_service import StorageService
import os

logger = get_logger(__name__)
video_processor = VideoProcessor()
storage_service = StorageService()

@celery.task(name="merge_audio_video")
def merge_audio_video_task(chain_data: dict):
    """
    Task to merge the generated audio with the original video using FFmpeg.
    """
    try:
        video_id = chain_data["video_id"]
        audio_path = chain_data["audio_path"]
        
        # Get database session
        db = next(get_db())
        
        # Update video status
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": "Video not found"}
        
        video.status = "merging"
        db.commit()

        try:
            # Get the original video path from the database
            video_path = video.video_path  # Assuming we stored this during download
            
            # Merge video with new audio
            output_filename = f"dubbed_video_{video_id}.mp4"
            output_path = video_processor.merge_audio_video(
                video_path=video_path,
                audio_path=audio_path,
                output_filename=output_filename,
                adjust_volume=True
            )

            # Move final dubbed video into storage
            try:
                stored_output_path = storage_service.save_dubbed_video(output_path, str(video_id))
                output_path = stored_output_path
            except Exception as storage_err:
                logger.error(f"Failed to store dubbed video for {video_id}: {storage_err}")
            
            logger.info(f"Successfully merged video {video_id} with new audio")
            
            # Update status and store output path
            video.status = "completed"
            video.output_path = output_path
            db.commit()
            
            # Clean up temporary files (tts audio already copied to storage)
            try:
                video_processor.cleanup(audio_path)
            except Exception as cleanup_err:
                logger.warning(f"Cleanup warning for video {video_id}: {cleanup_err}
                ")
            
            return {
                "status": "success", 
                "video_id": video_id,
                "output_path": output_path
            }
            
        except Exception as merge_error:
            logger.error(f"Error merging video {video_id}: {str(merge_error)}")
            raise merge_error
        
    except Exception as e:
        # Update status to failed if there's an error
        if 'video' in locals():
            video.status = "failed"
            db.commit()
        logger.error(f"Error in merge_audio_video_task for video {video_id}: {str(e)}")
        return {"status": "error", "message": str(e)}
