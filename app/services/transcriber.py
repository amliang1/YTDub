import whisper
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

class Transcriber:
    def __init__(self, model_name: str = "base"):
        """
        Initialize Whisper transcriber with specified model.
        Available models: tiny, base, small, medium, large
        """
        self.model = whisper.load_model(model_name)
        logger.info(f"Loaded Whisper model: {model_name}")

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            result = self.model.transcribe(audio_path)
            transcribed_text = result["text"].strip()
            
            logger.info(f"Successfully transcribed audio: {audio_path}")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_path}: {str(e)}")
            raise
