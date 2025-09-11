import os
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from app.services.video_downloader import VideoDownloader
from app.services.storage_service import StorageService

@pytest.fixture
def mock_storage_service(tmp_path):
    """Create a mock storage service."""
    storage = StorageService(str(tmp_path / "storage"))
    return storage

@pytest.fixture
def video_downloader(mock_storage_service):
    """Create a VideoDownloader instance with mock storage service."""
    return VideoDownloader(storage_service=mock_storage_service)

def create_mock_yt_dlp_info():
    """Create a mock YouTube video info dictionary."""
    return {
        'id': 'test_video_id',
        'title': 'Test Video',
        'duration': 100,
        'ext': 'mp4'
    }

@patch('yt_dlp.YoutubeDL')
def test_download_success(mock_yt_dlp, video_downloader, tmp_path):
    """Test successful video download and audio extraction."""
    # Setup mock YoutubeDL
    mock_instance = Mock()
    mock_instance.extract_info.return_value = create_mock_yt_dlp_info()
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance
    
    # Create test files that yt-dlp would normally create
    temp_video = video_downloader.storage_service.get_temp_path(".mp4")
    temp_audio = video_downloader.storage_service.get_temp_path(".wav")
    
    # Create the files
    temp_video.parent.mkdir(parents=True, exist_ok=True)
    temp_video.write_bytes(b"test video content")
    temp_audio.write_bytes(b"test audio content")
    
    # Test the download
    result = video_downloader.download("https://youtube.com/watch?v=test123", "test_id")
    
    assert result is not None
    video_path, audio_path = result
    
    # Verify files were moved to correct locations
    assert Path(video_path).exists()
    assert Path(audio_path).exists()
    assert "original" in video_path
    assert "extracted" in audio_path
    assert "test_id" in video_path
    assert "test_id" in audio_path

@patch('yt_dlp.YoutubeDL')
def test_download_failure_video_missing(mock_yt_dlp, video_downloader):
    """Test handling of missing video file after download."""
    # Setup mock YoutubeDL
    mock_instance = Mock()
    mock_instance.extract_info.return_value = create_mock_yt_dlp_info()
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance
    
    # Don't create the expected files - simulate download failure
    
    result = video_downloader.download("https://youtube.com/watch?v=test123", "test_id")
    assert result is None

@patch('yt_dlp.YoutubeDL')
def test_download_failure_audio_missing(mock_yt_dlp, video_downloader, tmp_path):
    """Test handling of missing audio file after download."""
    # Setup mock YoutubeDL
    mock_instance = Mock()
    mock_instance.extract_info.return_value = create_mock_yt_dlp_info()
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance
    
    # Create only video file, simulate audio extraction failure
    temp_video = video_downloader.storage_service.get_temp_path(".mp4")
    temp_video.parent.mkdir(parents=True, exist_ok=True)
    temp_video.write_bytes(b"test video content")
    
    result = video_downloader.download("https://youtube.com/watch?v=test123", "test_id")
    assert result is None

@patch('yt_dlp.YoutubeDL')
def test_download_exception_handling(mock_yt_dlp, video_downloader):
    """Test handling of yt-dlp exceptions."""
    # Setup mock YoutubeDL to raise an exception
    mock_instance = Mock()
    mock_instance.extract_info.side_effect = Exception("Download failed")
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance
    
    result = video_downloader.download("https://youtube.com/watch?v=test123", "test_id")
    assert result is None

def test_cleanup(video_downloader, tmp_path):
    """Test cleanup of temporary files."""
    # Create test files
    test_video = tmp_path / "test_video.mp4"
    test_audio = tmp_path / "test_audio.wav"
    
    test_video.write_bytes(b"test video content")
    test_audio.write_bytes(b"test audio content")
    
    # Test cleanup
    video_downloader.cleanup(str(test_video), str(test_audio))
    
    assert not test_video.exists()
    assert not test_audio.exists()
