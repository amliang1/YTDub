import ffmpeg
import os
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

class VideoProcessor:
    def __init__(self, output_dir: str = "processed_videos"):
        """
        Initialize video processor.
        
        Args:
            output_dir: Directory to store processed videos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def merge_audio_video(self, video_path: str, audio_path: str, output_filename: str,
                         adjust_volume: bool = True) -> str:
        """
        Merge video with new audio track.
        
        Args:
            video_path: Path to input video file
            audio_path: Path to new audio file
            output_filename: Name for the output file
            adjust_volume: Whether to normalize audio volume
            
        Returns:
            Path to the output video file
        """
        try:
            output_path = str(self.output_dir / output_filename)
            
            # Input streams
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)
            
            if adjust_volume:
                # Normalize audio volume
                audio = audio.filter('loudnorm')
            
            # Merge video with new audio
            stream = ffmpeg.output(
                video,
                audio,
                output_path,
                vcodec='copy',  # Copy video codec to avoid re-encoding
                acodec='aac',   # Convert audio to AAC
                strict='experimental',
                loglevel='error'
            )
            
            # Run FFmpeg command
            ffmpeg.run(stream, overwrite_output=True)
            
            if not os.path.exists(output_path):
                raise Exception(f"Failed to create output video: {output_path}")
            
            logger.info(f"Successfully merged video and audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging video and audio: {str(e)}")
            raise

    def extract_audio(self, video_path: str, output_filename: str) -> str:
        """
        Extract audio track from video.
        
        Args:
            video_path: Path to input video file
            output_filename: Name for the output audio file
            
        Returns:
            Path to the extracted audio file
        """
        try:
            output_path = str(self.output_dir / output_filename)
            
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='pcm_s16le',  # Convert to WAV format
                ac=1,                # Convert to mono
                ar='16k',           # Set sample rate to 16kHz
                loglevel='error'
            )
            
            ffmpeg.run(stream, overwrite_output=True)
            
            if not os.path.exists(output_path):
                raise Exception(f"Failed to extract audio: {output_path}")
            
            logger.info(f"Successfully extracted audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise

    def cleanup(self, *file_paths: str) -> None:
        """
        Remove temporary files.
        
        Args:
            file_paths: Paths to files to remove
        """
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    logger.info(f"Removed file: {path}")
            except Exception as e:
                logger.error(f"Error removing file {path}: {str(e)}")
