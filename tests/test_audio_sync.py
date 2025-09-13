from pathlib import Path
import numpy as np
import soundfile as sf

from app.services.audio_sync import AudioSynchronizationService
from app.models.translation_job import AudioChunk


def synth(freq=440.0, sr=16000, dur=1.0):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return 0.1 * np.sin(2 * np.pi * freq * t).astype(np.float32)


def test_audio_synchronization_alignment(tmp_path):
    sr = 16000

    # Target timing (original):
    # chunk1: 0.0-1.0, gap 0.2, chunk2: 1.2-2.0, gap 0.3, chunk3: 2.3-3.5
    c1 = AudioChunk(chunk_id="c1", file_path="", start_time=0.0, end_time=1.0, duration=1.0)
    c2 = AudioChunk(chunk_id="c2", file_path="", start_time=1.2, end_time=2.0, duration=0.8)
    c3 = AudioChunk(chunk_id="c3", file_path="", start_time=2.3, end_time=3.5, duration=1.2)

    # Translated audio durations (mismatched): 0.9, 1.0, 1.5
    p1 = tmp_path / "c1.wav"
    p2 = tmp_path / "c2.wav"
    p3 = tmp_path / "c3.wav"
    sf.write(str(p1), synth(dur=0.9, sr=sr), sr)
    sf.write(str(p2), synth(dur=1.0, sr=sr), sr)
    sf.write(str(p3), synth(dur=1.5, sr=sr), sr)
    c1.translated_audio_path = str(p1)
    c2.translated_audio_path = str(p2)
    c3.translated_audio_path = str(p3)

    out_path = tmp_path / "aligned.wav"
    svc = AudioSynchronizationService(sample_rate=sr)
    result = svc.render_aligned_track([c1, c2, c3], str(out_path))
    assert Path(result).exists()

    y, sro = sf.read(result)
    assert sro == sr
    assert abs(len(y) - int(3.5 * sr)) <= int(0.01 * sr)  # within 10 ms

    # Check the first gap (1.0-1.2s) is near-silent
    g1_start = int(1.0 * sr)
    g1_end = int(1.2 * sr)
    gap1 = y[g1_start:g1_end]
    assert np.mean(np.abs(gap1)) < 1e-3

