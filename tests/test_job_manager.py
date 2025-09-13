import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.services.job_manager import JobManager, VideoTranslationRequest
from app.models.translation_job import (
    TranslationJob, 
    TranslationJobDB, 
    JobStatus, 
    JobStage, 
    AudioChunk
)


class TestVideoTranslationRequest(unittest.TestCase):
    """Test VideoTranslationRequest data model"""
    
    def test_video_translation_request_creation(self):
        """Test VideoTranslationRequest creation"""
        request = VideoTranslationRequest(
            youtube_url="https://youtube.com/watch?v=test123",
            source_language="en",
            target_language="es"
        )
        
        assert request.youtube_url == "https://youtube.com/watch?v=test123"
        assert request.source_language == "en"
        assert request.target_language == "es"
        assert request.user_id is None
    
    def test_video_translation_request_with_user_id(self):
        """Test VideoTranslationRequest creation with user_id"""
        request = VideoTranslationRequest(
            youtube_url="https://youtube.com/watch?v=test456",
            source_language="fr",
            target_language="de",
            user_id="user_123"
        )
        
        assert request.user_id == "user_123"


class TestJobManager(unittest.TestCase):
    """Test JobManager service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.job_manager = JobManager()
        self.sample_request = VideoTranslationRequest(
            youtube_url="https://youtube.com/watch?v=test123",
            source_language="en",
            target_language="es"
        )
    
    @patch('app.services.job_manager.get_db')
    def test_create_job(self, mock_get_db):
        """Test job creation"""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        job_id = self.job_manager.create_job(self.sample_request)
        
        # Verify job ID is generated
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0
        
        # Verify job is stored in memory
        job = self.job_manager.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.youtube_url == self.sample_request.youtube_url
        assert job.source_language == self.sample_request.source_language
        assert job.target_language == self.sample_request.target_language
        assert job.status == JobStage.DOWNLOADING
        assert job.progress == 0.0
        
        # Verify database save was called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_job_from_memory(self):
        """Test getting job from memory cache"""
        # Create a job directly in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="memory_test",
            youtube_url="https://youtube.com/watch?v=memory",
            source_language="ja",
            target_language="ko",
            status=JobStage.CHUNKING,
            progress=0.2,
            created_at=now,
            updated_at=now
        )
        
        self.job_manager._jobs["memory_test"] = job
        
        retrieved_job = self.job_manager.get_job("memory_test")
        assert retrieved_job is not None
        assert retrieved_job.job_id == "memory_test"
        assert retrieved_job.status == JobStage.CHUNKING
        assert retrieved_job.progress == 0.2
    
    @patch('app.services.job_manager.get_db')
    def test_get_job_from_database(self, mock_get_db):
        """Test getting job from database when not in memory"""
        # Mock database session and query
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # Mock database job
        mock_db_job = Mock(spec=TranslationJobDB)
        mock_db_job.to_translation_job.return_value = TranslationJob(
            job_id="db_test",
            youtube_url="https://youtube.com/watch?v=db",
            source_language="de",
            target_language="fr",
            status=JobStage.TRANSLATING,
            progress=0.5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_query.first.return_value = mock_db_job
        mock_get_db.return_value = iter([mock_db])
        
        retrieved_job = self.job_manager.get_job("db_test")
        
        assert retrieved_job is not None
        assert retrieved_job.job_id == "db_test"
        assert retrieved_job.status == JobStage.TRANSLATING
        assert retrieved_job.progress == 0.5
        
        # Verify job is now cached in memory
        cached_job = self.job_manager._jobs.get("db_test")
        assert cached_job is not None
        assert cached_job.job_id == "db_test"
    
    def test_get_job_status(self):
        """Test getting job status"""
        # Create a job in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="status_test",
            youtube_url="https://youtube.com/watch?v=status",
            source_language="ru",
            target_language="en",
            status=JobStage.SYNTHESIZING,
            progress=0.8,
            created_at=now,
            updated_at=now,
            error_message="Minor synthesis issue"
        )
        
        self.job_manager._jobs["status_test"] = job
        
        status = self.job_manager.get_job_status("status_test")
        assert status is not None
        assert isinstance(status, JobStatus)
        assert status.job_id == "status_test"
        assert status.stage == JobStage.SYNTHESIZING
        assert status.progress == 0.8
        assert status.error == "Minor synthesis issue"
    
    def test_get_job_status_nonexistent(self):
        """Test getting status for nonexistent job"""
        status = self.job_manager.get_job_status("nonexistent")
        assert status is None
    
    @patch('app.services.job_manager.get_db')
    def test_update_progress(self, mock_get_db):
        """Test updating job progress"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_db_job = Mock()
        mock_query.first.return_value = mock_db_job
        mock_get_db.return_value = iter([mock_db])
        
        # Create a job in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="progress_test",
            youtube_url="https://youtube.com/watch?v=progress",
            source_language="ar",
            target_language="en",
            status=JobStage.DOWNLOADING,
            progress=0.0,
            created_at=now,
            updated_at=now
        )
        
        self.job_manager._jobs["progress_test"] = job
        
        # Update progress
        success = self.job_manager.update_progress("progress_test", JobStage.TRANSCRIBING, 0.3)
        
        assert success is True
        
        # Verify job was updated
        updated_job = self.job_manager.get_job("progress_test")
        assert updated_job.status == JobStage.TRANSCRIBING
        assert updated_job.progress == 0.3
        assert updated_job.updated_at > now
        
        # Verify database update was called
        mock_db_job.update_from_translation_job.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_update_progress_clamps_values(self):
        """Test that progress values are clamped between 0 and 1"""
        # Create a job in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="clamp_test",
            youtube_url="https://youtube.com/watch?v=clamp",
            source_language="hi",
            target_language="en",
            status=JobStage.DOWNLOADING,
            progress=0.0,
            created_at=now,
            updated_at=now
        )
        
        self.job_manager._jobs["clamp_test"] = job
        
        with patch('app.services.job_manager.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = iter([mock_db])
            
            # Test negative progress
            self.job_manager.update_progress("clamp_test", JobStage.DOWNLOADING, -0.5)
            updated_job = self.job_manager.get_job("clamp_test")
            assert updated_job.progress == 0.0
            
            # Test progress > 1
            self.job_manager.update_progress("clamp_test", JobStage.COMPLETE, 1.5)
            updated_job = self.job_manager.get_job("clamp_test")
            assert updated_job.progress == 1.0
    
    @patch('app.services.job_manager.get_db')
    def test_update_job_paths(self, mock_get_db):
        """Test updating job file paths"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_db_job = Mock()
        mock_query.first.return_value = mock_db_job
        mock_get_db.return_value = iter([mock_db])
        
        # Create a job in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="paths_test",
            youtube_url="https://youtube.com/watch?v=paths",
            source_language="pt",
            target_language="en",
            status=JobStage.DOWNLOADING,
            progress=0.1,
            created_at=now,
            updated_at=now
        )
        
        self.job_manager._jobs["paths_test"] = job
        
        # Update paths
        success = self.job_manager.update_job_paths(
            "paths_test", 
            video_path="/path/to/video.mp4",
            audio_path="/path/to/audio.wav"
        )
        
        assert success is True
        
        # Verify paths were updated
        updated_job = self.job_manager.get_job("paths_test")
        assert updated_job.video_path == "/path/to/video.mp4"
        assert updated_job.audio_path == "/path/to/audio.wav"
    
    @patch('app.services.job_manager.get_db')
    def test_add_audio_chunks(self, mock_get_db):
        """Test adding audio chunks to job"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_db_job = Mock()
        mock_query.first.return_value = mock_db_job
        mock_get_db.return_value = iter([mock_db])
        
        # Create a job in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="chunks_test",
            youtube_url="https://youtube.com/watch?v=chunks",
            source_language="it",
            target_language="en",
            status=JobStage.CHUNKING,
            progress=0.2,
            created_at=now,
            updated_at=now
        )
        
        self.job_manager._jobs["chunks_test"] = job
        
        # Add chunks
        chunks = [
            AudioChunk("chunk_1", "/path/1.wav", 0.0, 30.0, 30.0),
            AudioChunk("chunk_2", "/path/2.wav", 30.0, 60.0, 30.0)
        ]
        
        success = self.job_manager.add_audio_chunks("chunks_test", chunks)
        
        assert success is True
        
        # Verify chunks were added
        updated_job = self.job_manager.get_job("chunks_test")
        assert len(updated_job.chunks) == 2
        assert updated_job.chunks[0].chunk_id == "chunk_1"
        assert updated_job.chunks[1].chunk_id == "chunk_2"
    
    @patch('app.services.job_manager.get_db')
    def test_update_chunk(self, mock_get_db):
        """Test updating specific audio chunk"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_db_job = Mock()
        mock_query.first.return_value = mock_db_job
        mock_get_db.return_value = iter([mock_db])
        
        # Create a job with chunks in memory
        now = datetime.utcnow()
        chunks = [
            AudioChunk("chunk_1", "/path/1.wav", 0.0, 30.0, 30.0),
            AudioChunk("chunk_2", "/path/2.wav", 30.0, 60.0, 30.0)
        ]
        
        job = TranslationJob(
            job_id="update_chunk_test",
            youtube_url="https://youtube.com/watch?v=update_chunk",
            source_language="nl",
            target_language="en",
            status=JobStage.TRANSCRIBING,
            progress=0.4,
            created_at=now,
            updated_at=now,
            chunks=chunks
        )
        
        self.job_manager._jobs["update_chunk_test"] = job
        
        # Update chunk
        success = self.job_manager.update_chunk(
            "update_chunk_test", 
            "chunk_1",
            transcribed_text="Hello world",
            translated_text="Hola mundo"
        )
        
        assert success is True
        
        # Verify chunk was updated
        updated_job = self.job_manager.get_job("update_chunk_test")
        updated_chunk = next(c for c in updated_job.chunks if c.chunk_id == "chunk_1")
        assert updated_chunk.transcribed_text == "Hello world"
        assert updated_chunk.translated_text == "Hola mundo"
        
        # Verify other chunk was not affected
        other_chunk = next(c for c in updated_job.chunks if c.chunk_id == "chunk_2")
        assert other_chunk.transcribed_text is None
        assert other_chunk.translated_text is None
    
    def test_update_chunk_nonexistent_chunk(self):
        """Test updating nonexistent chunk"""
        # Create a job with chunks in memory
        now = datetime.utcnow()
        chunks = [AudioChunk("chunk_1", "/path/1.wav", 0.0, 30.0, 30.0)]
        
        job = TranslationJob(
            job_id="nonexistent_chunk_test",
            youtube_url="https://youtube.com/watch?v=nonexistent",
            source_language="sv",
            target_language="en",
            status=JobStage.TRANSCRIBING,
            progress=0.4,
            created_at=now,
            updated_at=now,
            chunks=chunks
        )
        
        self.job_manager._jobs["nonexistent_chunk_test"] = job
        
        # Try to update nonexistent chunk
        success = self.job_manager.update_chunk(
            "nonexistent_chunk_test", 
            "nonexistent_chunk",
            transcribed_text="This should fail"
        )
        
        assert success is False
    
    @patch('app.services.job_manager.get_db')
    def test_mark_job_complete(self, mock_get_db):
        """Test marking job as complete"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_db_job = Mock()
        mock_query.first.return_value = mock_db_job
        mock_get_db.return_value = iter([mock_db])
        
        # Create a job in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="complete_test",
            youtube_url="https://youtube.com/watch?v=complete",
            source_language="tr",
            target_language="en",
            status=JobStage.RECONSTRUCTING,
            progress=0.9,
            created_at=now,
            updated_at=now
        )
        
        self.job_manager._jobs["complete_test"] = job
        
        # Mark as complete
        success = self.job_manager.mark_job_complete("complete_test", "/path/to/final.mp4")
        
        assert success is True
        
        # Verify job was marked complete
        updated_job = self.job_manager.get_job("complete_test")
        assert updated_job.status == JobStage.COMPLETE
        assert updated_job.progress == 1.0
        assert updated_job.final_video_path == "/path/to/final.mp4"
    
    @patch('app.services.job_manager.get_db')
    def test_mark_job_failed(self, mock_get_db):
        """Test marking job as failed"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_db_job = Mock()
        mock_query.first.return_value = mock_db_job
        mock_get_db.return_value = iter([mock_db])
        
        # Create a job in memory
        now = datetime.utcnow()
        job = TranslationJob(
            job_id="failed_test",
            youtube_url="https://youtube.com/watch?v=failed",
            source_language="pl",
            target_language="en",
            status=JobStage.TRANSLATING,
            progress=0.6,
            created_at=now,
            updated_at=now
        )
        
        self.job_manager._jobs["failed_test"] = job
        
        # Mark as failed
        error_message = "Translation service unavailable"
        success = self.job_manager.mark_job_failed("failed_test", error_message)
        
        assert success is True
        
        # Verify job was marked failed
        updated_job = self.job_manager.get_job("failed_test")
        assert updated_job.status == JobStage.FAILED
        assert updated_job.error_message == error_message
    
    @patch('app.services.job_manager.get_db')
    def test_list_jobs(self, mock_get_db):
        """Test listing jobs with pagination"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Mock database jobs
        mock_db_jobs = [Mock(spec=TranslationJobDB) for _ in range(3)]
        for i, mock_db_job in enumerate(mock_db_jobs):
            mock_db_job.to_translation_job.return_value = TranslationJob(
                job_id=f"list_job_{i}",
                youtube_url=f"https://youtube.com/watch?v=list_{i}",
                source_language="en",
                target_language="es",
                status=JobStage.DOWNLOADING,
                progress=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        mock_query.all.return_value = mock_db_jobs
        mock_get_db.return_value = iter([mock_db])
        
        # List jobs
        jobs = self.job_manager.list_jobs(limit=10, offset=0)
        
        assert len(jobs) == 3
        assert all(isinstance(job, TranslationJob) for job in jobs)
        assert jobs[0].job_id == "list_job_0"
        assert jobs[1].job_id == "list_job_1"
        assert jobs[2].job_id == "list_job_2"
        
        # Verify pagination parameters were used
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(10)
    
    @patch('app.services.job_manager.get_db')
    def test_cleanup_old_jobs(self, mock_get_db):
        """Test cleaning up old jobs"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 2  # 2 jobs deleted
        mock_get_db.return_value = iter([mock_db])
        
        # Add some old jobs to memory cache
        old_date = datetime.utcnow() - timedelta(days=10)
        old_job1 = TranslationJob(
            job_id="old_job_1",
            youtube_url="https://youtube.com/watch?v=old1",
            source_language="en",
            target_language="es",
            status=JobStage.COMPLETE,
            progress=1.0,
            created_at=old_date,
            updated_at=old_date
        )
        old_job2 = TranslationJob(
            job_id="old_job_2",
            youtube_url="https://youtube.com/watch?v=old2",
            source_language="en",
            target_language="fr",
            status=JobStage.FAILED,
            progress=0.5,
            created_at=old_date,
            updated_at=old_date
        )
        
        self.job_manager._jobs["old_job_1"] = old_job1
        self.job_manager._jobs["old_job_2"] = old_job2
        
        # Cleanup old jobs
        deleted_count = self.job_manager.cleanup_old_jobs(days_old=7)
        
        assert deleted_count == 2
        
        # Verify jobs were removed from memory
        assert "old_job_1" not in self.job_manager._jobs
        assert "old_job_2" not in self.job_manager._jobs
        
        # Verify database delete was called
        mock_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @patch('app.services.job_manager.get_db')
    def test_get_active_jobs_count(self, mock_get_db):
        """Test getting count of active jobs"""
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_get_db.return_value = iter([mock_db])
        
        count = self.job_manager.get_active_jobs_count()
        
        assert count == 5
        mock_query.count.assert_called_once()