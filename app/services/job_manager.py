from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import uuid
import threading
from sqlalchemy.orm import Session
from ..models.translation_job import (
    TranslationJob, 
    TranslationJobDB, 
    JobStatus, 
    JobStage, 
    AudioChunk
)
from ..core.database import get_db


@dataclass
class VideoTranslationRequest:
    """Request model for video translation"""
    youtube_url: str
    source_language: str
    target_language: str
    user_id: Optional[str] = None


class JobManager:
    """Service for managing translation jobs with in-memory and persistent storage"""
    
    def __init__(self):
        self._jobs: Dict[str, TranslationJob] = {}
        self._lock = threading.RLock()
        
    def create_job(self, request: VideoTranslationRequest) -> str:
        """Create a new translation job and return job ID"""
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        job = TranslationJob(
            job_id=job_id,
            youtube_url=request.youtube_url,
            source_language=request.source_language,
            target_language=request.target_language,
            status=JobStage.DOWNLOADING,
            progress=0.0,
            created_at=now,
            updated_at=now
        )
        
        with self._lock:
            self._jobs[job_id] = job
            
        # Persist to database
        self._save_job_to_db(job)
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[TranslationJob]:
        """Get job by ID, first from memory then from database"""
        with self._lock:
            if job_id in self._jobs:
                return self._jobs[job_id]
        
        # Try to load from database
        job = self._load_job_from_db(job_id)
        if job:
            with self._lock:
                self._jobs[job_id] = job
        
        return job
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get current job status"""
        job = self.get_job(job_id)
        if job:
            return job.get_status()
        return None
    
    def update_progress(self, job_id: str, stage: JobStage, progress: float) -> bool:
        """Update job progress and stage"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        job.status = stage
        job.progress = max(0.0, min(1.0, progress))  # Clamp between 0 and 1
        job.updated_at = datetime.utcnow()
        
        with self._lock:
            self._jobs[job_id] = job
            
        # Update database
        self._update_job_in_db(job)
        
        return True
    
    def update_job_paths(self, job_id: str, video_path: str = None, audio_path: str = None) -> bool:
        """Update job file paths"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        if video_path:
            job.video_path = video_path
        if audio_path:
            job.audio_path = audio_path
        job.updated_at = datetime.utcnow()
        
        with self._lock:
            self._jobs[job_id] = job
            
        # Update database
        self._update_job_in_db(job)
        
        return True
    
    def add_audio_chunks(self, job_id: str, chunks: List[AudioChunk]) -> bool:
        """Add audio chunks to job"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        job.chunks.extend(chunks)
        job.updated_at = datetime.utcnow()
        
        with self._lock:
            self._jobs[job_id] = job
            
        # Update database
        self._update_job_in_db(job)
        
        return True
    
    def update_chunk(self, job_id: str, chunk_id: str, **updates) -> bool:
        """Update specific audio chunk properties"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        for chunk in job.chunks:
            if chunk.chunk_id == chunk_id:
                for key, value in updates.items():
                    if hasattr(chunk, key):
                        setattr(chunk, key, value)
                break
        else:
            return False  # Chunk not found
            
        job.updated_at = datetime.utcnow()
        
        with self._lock:
            self._jobs[job_id] = job
            
        # Update database
        self._update_job_in_db(job)
        
        return True
    
    def mark_job_complete(self, job_id: str, result_path: str) -> bool:
        """Mark job as complete with final result path"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        job.status = JobStage.COMPLETE
        job.progress = 1.0
        job.final_video_path = result_path
        job.updated_at = datetime.utcnow()
        
        with self._lock:
            self._jobs[job_id] = job
            
        # Update database
        self._update_job_in_db(job)
        
        return True
    
    def mark_job_failed(self, job_id: str, error: str) -> bool:
        """Mark job as failed with error message"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        job.status = JobStage.FAILED
        job.error_message = error
        job.updated_at = datetime.utcnow()
        
        with self._lock:
            self._jobs[job_id] = job
            
        # Update database
        self._update_job_in_db(job)
        
        return True
    
    def list_jobs(self, limit: int = 100, offset: int = 0) -> List[TranslationJob]:
        """List jobs with pagination"""
        db = next(get_db())
        try:
            db_jobs = db.query(TranslationJobDB).offset(offset).limit(limit).all()
            return [db_job.to_translation_job() for db_job in db_jobs]
        finally:
            db.close()
    
    def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """Clean up jobs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        db = next(get_db())
        try:
            # Remove from database
            deleted_count = db.query(TranslationJobDB).filter(
                TranslationJobDB.created_at < cutoff_date
            ).delete()
            db.commit()
            
            # Remove from memory cache
            with self._lock:
                jobs_to_remove = [
                    job_id for job_id, job in self._jobs.items()
                    if job.created_at < cutoff_date
                ]
                for job_id in jobs_to_remove:
                    del self._jobs[job_id]
            
            return deleted_count
        finally:
            db.close()
    
    def get_active_jobs_count(self) -> int:
        """Get count of active (non-complete, non-failed) jobs"""
        try:
            db = next(get_db())
        except StopIteration:
            return 0
        try:
            return db.query(TranslationJobDB).filter(
                TranslationJobDB.status.notin_([JobStage.COMPLETE.value, JobStage.FAILED.value])
            ).count()
        finally:
            db.close()
    
    def _save_job_to_db(self, job: TranslationJob) -> None:
        """Save job to database"""
        try:
            db = next(get_db())
        except StopIteration:
            return 0
        try:
            db_job = TranslationJobDB.from_translation_job(job)
            db.add(db_job)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _update_job_in_db(self, job: TranslationJob) -> None:
        """Update existing job in database"""
        try:
            db = next(get_db())
        except StopIteration:
            return None
        try:
            db_job = db.query(TranslationJobDB).filter(
                TranslationJobDB.job_id == job.job_id
            ).first()
            
            if db_job:
                db_job.update_from_translation_job(job)
                db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _load_job_from_db(self, job_id: str) -> Optional[TranslationJob]:
        """Load job from database"""
        try:
            db = next(get_db())
        except StopIteration:
            return None
        try:
            db_job = db.query(TranslationJobDB).filter(
                TranslationJobDB.job_id == job_id
            ).first()
            if db_job:
                return db_job.to_translation_job()
            return None
        except Exception:
            return None
        finally:
            try:
                db.close()
            except Exception:
                pass


# Global job manager instance
job_manager = JobManager()
