import unittest
import os
from pathlib import Path
from app.services.video_downloader import VideoDownloader
from app.services.transcriber import Transcriber
from app.services.translator import Translator
from app.services.tts import AllTalkTTS
from app.services.video_processor import VideoProcessor
from app.core.logging import get_logger
from typing import Optional, Tuple

logger = get_logger(__name__)

class TestDubbingWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Set up test environment"""
        cls.test_dir = Path("test_outputs")
        cls.test_dir.mkdir(exist_ok=True)
        
        # Initialize services
        cls.video_downloader = VideoDownloader(output_dir=str(cls.test_dir))
        cls.transcriber = Transcriber()
        cls.translator = Translator()
        cls.tts = AllTalkTTS()
        cls.video_processor = VideoProcessor(output_dir=str(cls.test_dir))
        
        # Test video URL (short video for testing)
        cls.test_video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo (first YouTube video)
        
    def setUp(self) -> None:
        """Set up before each test"""
        self.cleanup_test_files()
        
    def tearDown(self) -> None:
        """Clean up after each test"""
        self.cleanup_test_files()
        
    def cleanup_test_files(self) -> None:
        """Remove test files"""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Error cleaning up {file}: {e}")
    
    def test_1_video_download(self) -> None:
        """Test video downloading"""
        try:
            result: Optional[Tuple[str, str]] = self.video_downloader.download(self.test_video_url)
            self.assertIsNotNone(result, "Download failed")
            video_path, audio_path = result
            
            self.assertTrue(os.path.exists(video_path), "Video file not found")
            self.assertTrue(os.path.exists(audio_path), "Audio file not found")
            
            # Check file sizes
            self.assertGreater(os.path.getsize(video_path), 0, "Video file is empty")
            self.assertGreater(os.path.getsize(audio_path), 0, "Audio file is empty")
            
        except Exception as e:
            self.fail(f"Video download test failed: {str(e)}")
    
    def test_2_transcription(self) -> None:
        """Test transcription"""
        try:
            # First download the video
            result: Optional[Tuple[str, str]] = self.video_downloader.download(self.test_video_url)
            self.assertIsNotNone(result, "Download failed")
            _, audio_path = result
            
            # Transcribe the audio
            transcribed_text: str = self.transcriber.transcribe(audio_path)
            
            self.assertIsNotNone(transcribed_text, "Transcription failed")
            self.assertIsInstance(transcribed_text, str, "Transcription result should be string")
            self.assertGreater(len(transcribed_text), 0, "Transcription is empty")
            
        except Exception as e:
            self.fail(f"Transcription test failed: {str(e)}")
    
    def test_3_translation(self) -> None:
        """Test translation"""
        try:
            test_text = "Never gonna give you up, never gonna let you down"
            target_language = "es"  # Spanish
            
            # Translate the text
            translated_text: str = self.translator.translate(
                text=test_text,
                target_language=target_language
            )
            
            self.assertIsNotNone(translated_text, "Translation failed")
            self.assertIsInstance(translated_text, str, "Translation result should be string")
            self.assertGreater(len(translated_text), 0, "Translation is empty")
            self.assertNotEqual(translated_text, test_text, "Translation same as input")
            
        except Exception as e:
            self.fail(f"Translation test failed: {str(e)}")
    
    def test_4_text_to_speech(self) -> None:
        """Test text-to-speech"""
        self.skipTest("Skipping TTS test until TTS service is implemented")
    
    def test_5_video_processing(self) -> None:
        """Test video processing"""
        self.skipTest("Skipping video processing test until TTS service is implemented")
    
    def test_6_full_workflow(self) -> None:
        """Test the entire dubbing workflow"""
        self.skipTest("Skipping full workflow test until TTS service is implemented")

if __name__ == '__main__':
    unittest.main()
