from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import json


class JobStage(str, Enum):
    DOWNLOADING = "downloading"
    CHUNKING = "chunking"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    SYNTHESIZING = "synthesizing"
    RECONSTRUCTING = "reconstructing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class AudioChunk:
    """Data model for audio chunks with timing and processing metadata"""
    chunk_id: str
    file_path: str
    start_time: float
    end_time: float
    duration: float
    transcribed_text: Optional[str] = None
    translated_text: Optional[str] = None
    translated_audio_path: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'chunk_id': self.chunk_id,
            'file_path': self.file_path,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'transcribed_text': self.transcribed_text,
            'translated_text': self.translated_text,
            'translated_audio_path': self.translated_audio_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AudioChunk':
        """Create AudioChunk from dictionary"""
        return cls(**data)


@dataclass
class JobStatus:
    """Data model for job status tracking"""
    job_id: str
    stage: JobStage
    progress: float  # 0.0 to 1.0
    estimated_completion: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'job_id': self.job_id,
            'stage': self.stage.value,
            'progress': self.progress,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'error': self.error
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JobStatus':
        """Create JobStatus from dictionary"""
        estimated_completion = None
        if data.get('estimated_completion'):
            estimated_completion = datetime.fromisoformat(data['estimated_completion'])
        
        return cls(
            job_id=data['job_id'],
            stage=JobStage(data['stage']),
            progress=data['progress'],
            estimated_completion=estimated_completion,
            error=data.get('error')
        )


@dataclass
class TranslationJob:
    """Data model for translation job with all processing metadata"""
    job_id: str
    youtube_url: str
    source_language: str
    target_language: str
    status: JobStage
    progress: float
    created_at: datetime
    updated_at: datetime
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    chunks: List[AudioChunk] = field(default_factory=list)
    final_video_path: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'job_id': self.job_id,
            'youtube_url': self.youtube_url,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'status': self.status.value,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'video_path': self.video_path,
            'audio_path': self.audio_path,
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'final_video_path': self.final_video_path,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TranslationJob':
        """Create TranslationJob from dictionary"""
        chunks = [AudioChunk.from_dict(chunk_data) for chunk_data in data.get('chunks', [])]
        
        return cls(
            job_id=data['job_id'],
            youtube_url=data['youtube_url'],
            source_language=data['source_language'],
            target_language=data['target_language'],
            status=JobStage(data['status']),
            progress=data['progress'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            video_path=data.get('video_path'),
            audio_path=data.get('audio_path'),
            chunks=chunks,
            final_video_path=data.get('final_video_path'),
            error_message=data.get('error_message')
        )

    def get_status(self) -> JobStatus:
        """Get current job status"""
        return JobStatus(
            job_id=self.job_id,
            stage=self.status,
            progress=self.progress,
            error=self.error_message
        )


class TranslationJobDB(Base):
    """SQLAlchemy model for persistent job storage"""
    __tablename__ = "translation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    youtube_url = Column(String, nullable=False)
    source_language = Column(String, nullable=False)
    target_language = Column(String, nullable=False)
    status = Column(String, nullable=False, default=JobStage.DOWNLOADING.value)
    progress = Column(Float, nullable=False, default=0.0)
    video_path = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    chunks_data = Column(JSON, nullable=True)  # Serialized chunks
    final_video_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_translation_job(self) -> TranslationJob:
        """Convert database model to TranslationJob dataclass"""
        chunks = []
        if self.chunks_data:
            chunks = [AudioChunk.from_dict(chunk_data) for chunk_data in self.chunks_data]

        return TranslationJob(
            job_id=self.job_id,
            youtube_url=self.youtube_url,
            source_language=self.source_language,
            target_language=self.target_language,
            status=JobStage(self.status),
            progress=self.progress,
            created_at=self.created_at,
            updated_at=self.updated_at,
            video_path=self.video_path,
            audio_path=self.audio_path,
            chunks=chunks,
            final_video_path=self.final_video_path,
            error_message=self.error_message
        )

    @classmethod
    def from_translation_job(cls, job: TranslationJob) -> 'TranslationJobDB':
        """Create database model from TranslationJob dataclass"""
        chunks_data = [chunk.to_dict() for chunk in job.chunks] if job.chunks else None
        
        return cls(
            job_id=job.job_id,
            youtube_url=job.youtube_url,
            source_language=job.source_language,
            target_language=job.target_language,
            status=job.status.value,
            progress=job.progress,
            video_path=job.video_path,
            audio_path=job.audio_path,
            chunks_data=chunks_data,
            final_video_path=job.final_video_path,
            error_message=job.error_message
        )

    def update_from_translation_job(self, job: TranslationJob) -> None:
        """Update database model from TranslationJob dataclass"""
        self.status = job.status.value
        self.progress = job.progress
        self.video_path = job.video_path
        self.audio_path = job.audio_path
        self.chunks_data = [chunk.to_dict() for chunk in job.chunks] if job.chunks else None
        self.final_video_path = job.final_video_path
        self.error_message = job.error_message
        self.updated_at = job.updated_at