import os
import shutil
import pytest
from pathlib import Path
from app.services.storage_service import StorageService

@pytest.fixture
def storage_service(tmp_path):
    """Create a temporary storage service for testing."""
    storage_dir = tmp_path / "storage_test"
    service = StorageService(str(storage_dir))
    yield service
    # Cleanup after tests
    if storage_dir.exists():
        shutil.rmtree(storage_dir)

def test_storage_structure_creation(storage_service):
    """Test that the storage service creates the expected directory structure."""
    base_path = Path(storage_service.base_path)
    expected_dirs = [
        base_path / "videos" / "original",
        base_path / "videos" / "dubbed",
        base_path / "audio" / "extracted",
        base_path / "audio" / "tts",
        base_path / "temp"
    ]
    
    for directory in expected_dirs:
        assert directory.exists(), f"Directory {directory} was not created"
        assert directory.is_dir(), f"{directory} is not a directory"

def test_generate_filename(storage_service):
    """Test filename generation with various inputs."""
    # Test basic filename
    filename = storage_service._generate_filename("test.mp4")
    assert filename.endswith("test.mp4")
    assert len(filename) > len("test.mp4")  # Should include timestamp
    
    # Test with prefix
    filename = storage_service._generate_filename("test.mp4", "video_123")
    assert filename.startswith("video_123_")
    assert filename.endswith("test.mp4")
    
    # Test with special characters
    filename = storage_service._generate_filename("test!@#$%^&*.mp4")
    assert "!@#$%^&*" not in filename
    assert filename.endswith("test.mp4")

def test_save_original_video(storage_service, tmp_path):
    """Test saving an original video file."""
    # Create a test video file
    test_video = tmp_path / "test_video.mp4"
    test_video.write_bytes(b"test video content")
    
    video_path = storage_service.save_original_video(str(test_video), "123")
    assert os.path.exists(video_path)
    assert Path(video_path).parent == Path(storage_service.base_path) / "videos" / "original"
    assert "123" in video_path
    assert Path(video_path).read_bytes() == b"test video content"

def test_save_extracted_audio(storage_service, tmp_path):
    """Test saving an extracted audio file."""
    test_audio = tmp_path / "test_audio.wav"
    test_audio.write_bytes(b"test audio content")
    
    audio_path = storage_service.save_extracted_audio(str(test_audio), "123")
    assert os.path.exists(audio_path)
    assert Path(audio_path).parent == Path(storage_service.base_path) / "audio" / "extracted"
    assert "123" in audio_path
    assert Path(audio_path).read_bytes() == b"test audio content"

def test_save_tts_audio(storage_service, tmp_path):
    """Test saving a TTS audio file."""
    test_tts = tmp_path / "test_tts.wav"
    test_tts.write_bytes(b"test tts content")
    
    tts_path = storage_service.save_tts_audio(str(test_tts), "123")
    assert os.path.exists(tts_path)
    assert Path(tts_path).parent == Path(storage_service.base_path) / "audio" / "tts"
    assert "123" in tts_path
    assert Path(tts_path).read_bytes() == b"test tts content"

def test_save_dubbed_video(storage_service, tmp_path):
    """Test saving a dubbed video file."""
    test_dubbed = tmp_path / "test_dubbed.mp4"
    test_dubbed.write_bytes(b"test dubbed content")
    
    dubbed_path = storage_service.save_dubbed_video(str(test_dubbed), "123")
    assert os.path.exists(dubbed_path)
    assert Path(dubbed_path).parent == Path(storage_service.base_path) / "videos" / "dubbed"
    assert "123" in dubbed_path
    assert Path(dubbed_path).read_bytes() == b"test dubbed content"

def test_get_temp_path(storage_service):
    """Test getting temporary file paths."""
    temp_path = storage_service.get_temp_path(".mp4")
    assert temp_path.parent == Path(storage_service.base_path) / "temp"
    assert temp_path.suffix == ".mp4"
    assert "processing" in str(temp_path)

def test_cleanup_temp_files(storage_service):
    """Test cleaning up temporary files."""
    # Create some test temp files
    temp_dir = Path(storage_service.base_path) / "temp"
    test_files = [
        temp_dir / "test_123_file1.tmp",
        temp_dir / "test_123_file2.tmp",
        temp_dir / "test_456_file3.tmp"  # Should not be deleted
    ]
    
    for file in test_files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"test content")
    
    # Clean up files for video_id "123"
    storage_service.cleanup_temp_files("123")
    
    # Check that only files with "123" were deleted
    assert not test_files[0].exists()
    assert not test_files[1].exists()
    assert test_files[2].exists()

def test_get_file_path(storage_service, tmp_path):
    """Test retrieving file paths."""
    # Create test files
    video_path = storage_service.base_path / "videos" / "original" / "test_123_video.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(b"test content")
    
    # Test finding existing file
    found_path = storage_service.get_file_path("original", "123", "video")
    assert found_path == video_path
    
    # Test with non-existent file
    not_found = storage_service.get_file_path("original", "999", "nonexistent")
    assert not_found is None
    
    # Test with invalid file type
    invalid_type = storage_service.get_file_path("invalid", "123", "video")
    assert invalid_type is None
