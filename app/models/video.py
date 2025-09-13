from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from ..core.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    youtube_url = Column(String, unique=True, index=True)
    transcription = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    status = Column(String, default="pending")
    # New fields for end-to-end workflow tracking
    target_language = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    output_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
