import os
import yt_dlp
from typing import Optional, Tuple
from pathlib import Path
from app.core.logging import get_logger
from app.services.storage_service import StorageService

logger = get_logger(__name__)

class VideoDownloader:
    def __init__(self, storage_service: Optional[StorageService] = None):
        """
        Initialize VideoDownloader with optional StorageService.
        If no StorageService is provided, a new one will be created.
        """
        self.storage_service = storage_service or StorageService()
        
        self.ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'merge_output_format': 'mp4'
        }

    def download(self, url: str, video_id: str) -> Optional[Tuple[str, str]]:
        """
        Download video from YouTube URL and extract audio.
        
        Args:
            url: YouTube video URL
            video_id: ID to use for file naming and tracking
            
        Returns:
            Tuple of (video_path, audio_path) if successful, None if failed
        """
        try:
            # Get temporary paths for download
            temp_video = self.storage_service.get_temp_path(".mp4")
            temp_audio = self.storage_service.get_temp_path(".wav")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract video info first
                info = ydl.extract_info(url, download=False)
                yt_video_id = info['id']
                
                # Update options for video download
                video_opts = dict(self.ydl_opts)
                video_opts['outtmpl'] = str(temp_video)
                video_opts.pop('postprocessors', None)  # Remove audio extraction for video download
                
                # Download video
                with yt_dlp.YoutubeDL(video_opts) as video_dl:
                    video_dl.download([url])
                
                # Update options for audio extraction
                audio_opts = dict(self.ydl_opts)
                audio_opts['outtmpl'] = str(temp_video)
                audio_opts['format'] = 'bestaudio'
                audio_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }]
                
                # Download and extract audio
                with yt_dlp.YoutubeDL(audio_opts) as audio_dl:
                    audio_dl.download([url])
                
                if not temp_video.exists():
                    logger.error(f"Video file not found at {temp_video}")
                    return None
                if not temp_audio.exists():
                    logger.error(f"Audio file not found at {temp_audio}")
                    return None
                
                # Move files to permanent storage
                final_video_path = self.storage_service.save_original_video(str(temp_video), video_id)
                final_audio_path = self.storage_service.save_extracted_audio(str(temp_audio), video_id)
                
                # Clean up temporary files
                self.cleanup(str(temp_video), str(temp_audio))
                
                logger.info(f"Successfully downloaded video and extracted audio for {url}")
                return final_video_path, final_audio_path
                
        except Exception as e:
            logger.error(f"Error downloading video {url}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return None

    def cleanup(self, video_path: str, audio_path: str) -> None:
        """
        Remove temporary downloaded video and audio files.
        """
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            logger.info(f"Cleaned up temporary files: {video_path}, {audio_path}")
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")
