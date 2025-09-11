import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

class StorageService:
    def __init__(self, base_path: str = "storage"):
        """Initialize storage service with base path for all files."""
        self.base_path = Path(base_path)
        self._create_storage_structure()

    def _create_storage_structure(self):
        """Create the basic storage directory structure."""
        directories = [
            self.base_path / "videos" / "original",  # Original downloaded videos
            self.base_path / "videos" / "dubbed",    # Final dubbed videos
            self.base_path / "audio" / "extracted",  # Extracted audio from videos
            self.base_path / "audio" / "tts",        # Generated TTS audio
            self.base_path / "temp"                  # Temporary processing files
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, original_name: str, prefix: str = "") -> str:
        """Generate a unique filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = "".join(c for c in original_name if c.isalnum() or c in "._- ")
        return f"{prefix}_{timestamp}_{clean_name}" if prefix else f"{timestamp}_{clean_name}"

    def save_original_video(self, file_path: str, video_id: str) -> str:
        """Save the downloaded video to storage."""
        filename = self._generate_filename(Path(file_path).name, f"video_{video_id}")
        target_path = self.base_path / "videos" / "original" / filename
        shutil.copy2(file_path, target_path)
        return str(target_path)

    def save_extracted_audio(self, file_path: str, video_id: str) -> str:
        """Save extracted audio from video."""
        filename = self._generate_filename(Path(file_path).name, f"audio_{video_id}")
        target_path = self.base_path / "audio" / "extracted" / filename
        shutil.copy2(file_path, target_path)
        return str(target_path)

    def save_tts_audio(self, file_path: str, video_id: str) -> str:
        """Save generated TTS audio."""
        filename = self._generate_filename(Path(file_path).name, f"tts_{video_id}")
        target_path = self.base_path / "audio" / "tts" / filename
        shutil.copy2(file_path, target_path)
        return str(target_path)

    def save_dubbed_video(self, file_path: str, video_id: str) -> str:
        """Save the final dubbed video."""
        filename = self._generate_filename(Path(file_path).name, f"dubbed_{video_id}")
        target_path = self.base_path / "videos" / "dubbed" / filename
        shutil.copy2(file_path, target_path)
        return str(target_path)

    def get_temp_path(self, suffix: str = "") -> Path:
        """Get a temporary file path for processing."""
        filename = self._generate_filename("temp", "processing") + suffix
        return self.base_path / "temp" / filename

    def cleanup_temp_files(self, video_id: str):
        """Clean up temporary files for a specific video."""
        temp_dir = self.base_path / "temp"
        pattern = f"*{video_id}*"
        for file_path in temp_dir.glob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")

    def get_file_path(self, file_type: str, video_id: str, filename: str) -> Optional[Path]:
        """Get the path for a specific file type and video ID."""
        type_map = {
            "original": self.base_path / "videos" / "original",
            "dubbed": self.base_path / "videos" / "dubbed",
            "extracted_audio": self.base_path / "audio" / "extracted",
            "tts": self.base_path / "audio" / "tts"
        }
        
        if file_type not in type_map:
            return None
            
        base_dir = type_map[file_type]
        pattern = f"*{video_id}*{filename}*"
        matches = list(base_dir.glob(pattern))
        return matches[0] if matches else None
