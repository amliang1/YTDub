import numpy as np
import soundfile as sf
from pathlib import Path

from app.services.audio_chunking import AudioChunkingService


def synth_tone(freq=440.0, sr=16000, dur=1.0):
    t = np.linspace(0, dur, int(sr*dur), endpoint=False)
    return 0.1 * np.sin(2 * np.pi * freq * t)


def test_audio_chunking_simple(tmp_path):
    sr = 16000
    # tone - silence - tone pattern
    tone1 = synth_tone(sr=sr, dur=1.0)
    silence = np.zeros(int(sr * 0.5))
    tone2 = synth_tone(sr=sr, dur=1.0)
    y = np.concatenate([tone1, silence, tone2])

    audio_path = tmp_path / "sample.wav"
    sf.write(str(audio_path), y, sr)

    svc = AudioChunkingService(output_dir=str(tmp_path / "chunks"), target_sr=sr)
    chunks = svc.chunk(str(audio_path))

    # Expect two chunks for the two tone regions
    assert len(chunks) == 2
    # Validate timing ordering and reasonable durations
    assert chunks[0].start_time < chunks[0].end_time
    assert chunks[0].duration > 0.2
    assert Path(chunks[0].file_path).exists()

