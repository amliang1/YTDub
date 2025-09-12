import pytest
from datetime import datetime, timedelta
from app.models.translation_job import (
    AudioChunk, 
    JobStatus, 
    TranslationJob, 
    TranslationJobDB,
    JobStage
)


class TestAudioChunk:
    """Test AudioChunk data model"""
    
    def test_audio_chunk_creation(self):
        """Test AudioChunk creation with required fields"""
        chunk = AudioChunk(
            chunk_id="chunk_001",
            file_path="/path/to/chunk.wav",
            start_time=0.0,
            end_time=30.5,
            duration=30.5
        )
        
        assert chunk.chunk_id == "chunk_001"
        assert chunk.file_path == "/path/to/chunk.wav"
        assert chunk.start_time == 0.0
        assert chunk.end_time == 30.5
        assert chunk.duration == 30.5
        assert chunk.transcribed_text is None
        assert chunk.translated_text is None
        assert chunk.translated_audio_path is None
    
    def test_audio_chunk_with_optional_fields(self):
        """Test AudioChunk creation with optional fields"""
        chunk = AudioChunk(
            chunk_id="chunk_002",
            file_path="/path/to/chunk2.wav",
            start_time=30.5,
            end_time=61.0,
            duration=30.5,
            transcribed_text="Hello world",
            translated_text="Hola mundo",
            translated_audio_path="/path/to/translated.wav"
        )
        
        assert chunk.transcribed_text == "Hello world"
        assert chunk.translated_text == "Hola mundo"
        assert chunk.translated_audio_path == "/path/to/translated.wav"
    
    def test_audio_chunk_serialization(self):
        """Test AudioChunk to_dict and from_dict methods"""
        original_chunk = AudioChunk(
            chunk_id="chunk_003",
            file_path="/path/to/chunk3.wav",
            start_time=61.0,
            end_time=91.5,
            duration=30.5,
            transcribed_text="Test transcription",
            translated_text="Transcripción de prueba"
        )
        
        # Test serialization
        chunk_dict = original_chunk.to_dict()
        expected_keys = {
            'chunk_id', 'file_path', 'start_time', 'end_time', 'duration',
            'transcribed_text', 'translated_text', 'translated_audio_path'
        }
        assert set(chunk_dict.keys()) == expected_keys
        
        # Test deserialization
        restored_chunk = AudioChunk.from_dict(chunk_dict)
        assert restored_chunk.chunk_id == original_chunk.chunk_id
        assert restored_chunk.file_path == original_chunk.file_path
        assert restored_chunk.start_time == original_chunk.start_time
        assert restored_chunk.end_time == original_chunk.end_time
        assert restored_chunk.duration == original_chunk.duration
        assert restored_chunk.transcribed_text == original_chunk.transcribed_text
        assert restored_chunk.translated_text == original_chunk.translated_text


class TestJobStatus:
    """Test JobStatus data model"""
    
    def test_job_status_creation(self):
        """Test JobStatus creation with required fields"""
        status = JobStatus(
            job_id="job_123",
            stage=JobStage.DOWNLOADING,
            progress=0.25
        )
        
        assert status.job_id == "job_123"
        assert status.stage == JobStage.DOWNLOADING
        assert status.progress == 0.25
        assert status.estimated_completion is None
        assert status.error is None
    
    def test_job_status_with_optional_fields(self):
        """Test JobStatus creation with optional fields"""
        completion_time = datetime.utcnow() + timedelta(minutes=30)
        status = JobStatus(
            job_id="job_124",
            stage=JobStage.TRANSLATING,
            progress=0.75,
            estimated_completion=completion_time,
            error="Translation service timeout"
        )
        
        assert status.estimated_completion == completion_time
        assert status.error == "Translation service timeout"
    
    def test_job_status_serialization(self):
        """Test JobStatus to_dict and from_dict methods"""
        completion_time = datetime.utcnow() + timedelta(minutes=15)
        original_status = JobStatus(
            job_id="job_125",
            stage=JobStage.SYNTHESIZING,
            progress=0.9,
            estimated_completion=completion_time
        )
        
        # Test serialization
        status_dict = original_status.to_dict()
        expected_keys = {'job_id', 'stage', 'progress', 'estimated_completion', 'error'}
        assert set(status_dict.keys()) == expected_keys
        assert status_dict['stage'] == JobStage.SYNTHESIZING.value
        
        # Test deserialization
        restored_status = JobStatus.from_dict(status_dict)
        assert restored_status.job_id == original_status.job_id
        assert restored_status.stage == original_status.stage
        assert restored_status.progress == original_status.progress
        assert restored_status.estimated_completion == original_status.estimated_completion
    
    def test_job_status_serialization_without_completion_time(self):
        """Test JobStatus serialization when estimated_completion is None"""
        status = JobStatus(
            job_id="job_126",
            stage=JobStage.COMPLETE,
            progress=1.0
        )
        
        status_dict = status.to_dict()
        assert status_dict['estimated_completion'] is None
        
        restored_status = JobStatus.from_dict(status_dict)
        assert restored_status.estimated_completion is None


class TestTranslationJob:
    """Test TranslationJob data model"""
    
    def test_translation_job_creation(self):
        """Test TranslationJob creation with required fields"""
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="job_001",
            youtube_url="https://youtube.com/watch?v=test123",
            source_language="en",
            target_language="es",
            status=JobStage.DOWNLOADING,
            progress=0.0,
            created_at=now,
            updated_at=now
        )
        
        assert job.job_id == "job_001"
        assert job.youtube_url == "https://youtube.com/watch?v=test123"
        assert job.source_language == "en"
        assert job.target_language == "es"
        assert job.status == JobStage.DOWNLOADING
        assert job.progress == 0.0
        assert job.created_at == now
        assert job.updated_at == now
        assert job.chunks == []
    
    def test_translation_job_with_chunks(self):
        """Test TranslationJob with audio chunks"""
        now = datetime.utcnow()
        chunks = [
            AudioChunk("chunk_1", "/path/1.wav", 0.0, 30.0, 30.0),
            AudioChunk("chunk_2", "/path/2.wav", 30.0, 60.0, 30.0)
        ]
        
        job = TranslationJob(
            job_id="job_002",
            youtube_url="https://youtube.com/watch?v=test456",
            source_language="fr",
            target_language="de",
            status=JobStage.CHUNKING,
            progress=0.3,
            created_at=now,
            updated_at=now,
            chunks=chunks
        )
        
        assert len(job.chunks) == 2
        assert job.chunks[0].chunk_id == "chunk_1"
        assert job.chunks[1].chunk_id == "chunk_2"
    
    def test_translation_job_get_status(self):
        """Test TranslationJob get_status method"""
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="job_003",
            youtube_url="https://youtube.com/watch?v=test789",
            source_language="ja",
            target_language="ko",
            status=JobStage.TRANSLATING,
            progress=0.6,
            created_at=now,
            updated_at=now,
            error_message="Partial translation failure"
        )
        
        status = job.get_status()
        assert isinstance(status, JobStatus)
        assert status.job_id == "job_003"
        assert status.stage == JobStage.TRANSLATING
        assert status.progress == 0.6
        assert status.error == "Partial translation failure"
    
    def test_translation_job_serialization(self):
        """Test TranslationJob to_dict and from_dict methods"""
        now = datetime.utcnow()
        chunks = [
            AudioChunk("chunk_1", "/path/1.wav", 0.0, 30.0, 30.0, "Hello", "Hola"),
            AudioChunk("chunk_2", "/path/2.wav", 30.0, 60.0, 30.0, "World", "Mundo")
        ]
        
        original_job = TranslationJob(
            job_id="job_004",
            youtube_url="https://youtube.com/watch?v=serialization_test",
            source_language="en",
            target_language="es",
            status=JobStage.COMPLETE,
            progress=1.0,
            created_at=now,
            updated_at=now,
            video_path="/path/to/video.mp4",
            audio_path="/path/to/audio.wav",
            chunks=chunks,
            final_video_path="/path/to/final.mp4"
        )
        
        # Test serialization
        job_dict = original_job.to_dict()
        expected_keys = {
            'job_id', 'youtube_url', 'source_language', 'target_language',
            'status', 'progress', 'created_at', 'updated_at', 'video_path',
            'audio_path', 'chunks', 'final_video_path', 'error_message'
        }
        assert set(job_dict.keys()) == expected_keys
        assert len(job_dict['chunks']) == 2
        
        # Test deserialization
        restored_job = TranslationJob.from_dict(job_dict)
        assert restored_job.job_id == original_job.job_id
        assert restored_job.youtube_url == original_job.youtube_url
        assert restored_job.source_language == original_job.source_language
        assert restored_job.target_language == original_job.target_language
        assert restored_job.status == original_job.status
        assert restored_job.progress == original_job.progress
        assert restored_job.video_path == original_job.video_path
        assert restored_job.audio_path == original_job.audio_path
        assert len(restored_job.chunks) == 2
        assert restored_job.chunks[0].chunk_id == "chunk_1"
        assert restored_job.chunks[1].chunk_id == "chunk_2"
        assert restored_job.final_video_path == original_job.final_video_path


class TestTranslationJobDB:
    """Test TranslationJobDB database model"""
    
    def test_translation_job_db_creation(self):
        """Test TranslationJobDB creation"""
        db_job = TranslationJobDB(
            job_id="db_job_001",
            youtube_url="https://youtube.com/watch?v=db_test",
            source_language="en",
            target_language="fr",
            status=JobStage.DOWNLOADING.value,
            progress=0.1
        )
        
        assert db_job.job_id == "db_job_001"
        assert db_job.youtube_url == "https://youtube.com/watch?v=db_test"
        assert db_job.source_language == "en"
        assert db_job.target_language == "fr"
        assert db_job.status == JobStage.DOWNLOADING.value
        assert db_job.progress == 0.1
    
    def test_translation_job_db_conversion(self):
        """Test conversion between TranslationJobDB and TranslationJob"""
        now = datetime.utcnow()
        chunks = [
            AudioChunk("chunk_1", "/path/1.wav", 0.0, 30.0, 30.0)
        ]
        
        # Create TranslationJob
        job = TranslationJob(
            job_id="conversion_test",
            youtube_url="https://youtube.com/watch?v=conversion",
            source_language="de",
            target_language="it",
            status=JobStage.TRANSCRIBING,
            progress=0.4,
            created_at=now,
            updated_at=now,
            chunks=chunks,
            video_path="/path/to/video.mp4"
        )
        
        # Convert to DB model
        db_job = TranslationJobDB.from_translation_job(job)
        assert db_job.job_id == job.job_id
        assert db_job.youtube_url == job.youtube_url
        assert db_job.source_language == job.source_language
        assert db_job.target_language == job.target_language
        assert db_job.status == job.status.value
        assert db_job.progress == job.progress
        assert db_job.video_path == job.video_path
        assert db_job.chunks_data is not None
        assert len(db_job.chunks_data) == 1
        
        # Convert back to TranslationJob
        restored_job = db_job.to_translation_job()
        assert restored_job.job_id == job.job_id
        assert restored_job.youtube_url == job.youtube_url
        assert restored_job.source_language == job.source_language
        assert restored_job.target_language == job.target_language
        assert restored_job.status == job.status
        assert restored_job.progress == job.progress
        assert restored_job.video_path == job.video_path
        assert len(restored_job.chunks) == 1
        assert restored_job.chunks[0].chunk_id == "chunk_1"
    
    def test_translation_job_db_update(self):
        """Test updating TranslationJobDB from TranslationJob"""
        now = datetime.utcnow()
        
        # Create initial DB job
        db_job = TranslationJobDB(
            job_id="update_test",
            youtube_url="https://youtube.com/watch?v=update",
            source_language="zh",
            target_language="ja",
            status=JobStage.DOWNLOADING.value,
            progress=0.0
        )
        
        # Create updated TranslationJob
        updated_job = TranslationJob(
            job_id="update_test",
            youtube_url="https://youtube.com/watch?v=update",
            source_language="zh",
            target_language="ja",
            status=JobStage.COMPLETE,
            progress=1.0,
            created_at=now,
            updated_at=now,
            final_video_path="/path/to/final.mp4"
        )
        
        # Update DB job
        db_job.update_from_translation_job(updated_job)
        
        assert db_job.status == JobStage.COMPLETE.value
        assert db_job.progress == 1.0
        assert db_job.final_video_path == "/path/to/final.mp4"
        assert db_job.updated_at == updated_job.updated_at