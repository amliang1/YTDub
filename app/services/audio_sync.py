from typing import List, Optional
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa

from ..models.translation_job import AudioChunk
from ..core.logging import get_logger


logger = get_logger(__name__)


class AudioSynchronizationService:
    """
    Reconstruct a single speech track from translated chunk audios, preserving
    original timing by inserting silences and time-stretching per-chunk audio
    to match the target durations.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    def _stretch_to_duration(self, y: np.ndarray, current_dur: float, target_dur: float) -> np.ndarray:
        if target_dur <= 0:
            return np.zeros(0, dtype=np.float32)
        if current_dur <= 0 or y.size == 0:
            return np.zeros(int(round(target_dur * self.sr)), dtype=np.float32)

        # librosa time_stretch: output duration = current_dur / rate
        rate = max(1e-3, current_dur / target_dur)
        try:
            y_out = librosa.effects.time_stretch(y.astype(np.float32), rate=rate)
        except Exception:
            # Fallback: simple resample if stretching fails
            target_len = int(round(target_dur * self.sr))
            if len(y) < 2:
                return np.zeros(target_len, dtype=np.float32)
            y_out = librosa.resample(y.astype(np.float32), orig_sr=self.sr, target_sr=self.sr * (len(y) / max(1, target_len)))

        # Trim/pad to exact target length
        target_len = int(round(target_dur * self.sr))
        if len(y_out) > target_len:
            y_out = y_out[:target_len]
        elif len(y_out) < target_len:
            pad = np.zeros(target_len - len(y_out), dtype=np.float32)
            y_out = np.concatenate([y_out, pad])
        return y_out.astype(np.float32)

    def render_aligned_track(self, chunks: List[AudioChunk], output_path: str) -> str:
        if not chunks:
            raise ValueError("no chunks provided")

        # Determine final length from target end times
        max_end = max(c.end_time for c in chunks)
        total_len = int(round(max_end * self.sr))
        out = np.zeros(total_len, dtype=np.float32)

        # Place each chunk at its start position
        for c in sorted(chunks, key=lambda x: x.start_time):
            start = int(round(c.start_time * self.sr))
            end = int(round(c.end_time * self.sr))
            target_len = max(0, end - start)
            if target_len == 0:
                continue

            y: Optional[np.ndarray] = None
            if c.translated_audio_path:
                try:
                    y, sr_in = sf.read(c.translated_audio_path)
                    if y.ndim > 1:
                        y = y.mean(axis=1)
                    if sr_in != self.sr:
                        y = librosa.resample(y.astype(np.float32), orig_sr=sr_in, target_sr=self.sr)
                except Exception as e:
                    logger.error("Failed to read translated audio for chunk %s: %s", c.chunk_id, e)
            if y is None:
                y = np.zeros(target_len, dtype=np.float32)

            current_dur = len(y) / float(self.sr)
            target_dur = target_len / float(self.sr)
            y_fit = self._stretch_to_duration(y, current_dur, target_dur)

            stop = min(len(out), start + len(y_fit))
            if stop > start:
                out[start:stop] += y_fit[: stop - start]

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(out_path), out, self.sr)
        return str(out_path)

