import uuid
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path

import numpy as np
import librosa
import soundfile as sf

from ..models.translation_job import AudioChunk


class AudioChunkingService:
    """
    Chunk audio by detecting speech segments using simple energy-based VAD.
    Produces small WAV files per chunk and returns AudioChunk metadata.
    """

    def __init__(self, output_dir: str = "temp/chunks", target_sr: int = 16000):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_sr = target_sr

    def _detect_segments(
        self,
        y: np.ndarray,
        sr: int,
        frame_length: int = 1024,
        hop_length: int = 256,
        min_speech_sec: float = 0.2,
        min_silence_sec: float = 0.2,
        energy_multiplier: float = 1.1,
    ) -> List[Tuple[float, float]]:
        """
        Return list of (start_sec, end_sec) for detected speech segments.
        Uses RMS with adaptive threshold.
        """
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        median = np.median(rms)
        thr = max(median * energy_multiplier, 0.01)
        voiced = rms > thr

        # Merge frames into contiguous segments
        segments: List[Tuple[int, int]] = []
        start = None
        for i, flag in enumerate(voiced):
            if flag and start is None:
                start = i
            elif not flag and start is not None:
                segments.append((start, i))
                start = None
        if start is not None:
            segments.append((start, len(voiced)))

        # Convert to seconds and filter by min durations
        frame_sec = hop_length / sr
        merged: List[Tuple[float, float]] = []
        for s, e in segments:
            st = s * frame_sec
            en = max(st, e * frame_sec)
            if en - st >= min_speech_sec:
                if merged and st - merged[-1][1] < min_silence_sec:
                    # merge adjacent segments separated by short silence
                    prev_st, prev_en = merged[-1]
                    merged[-1] = (prev_st, en)
                else:
                    merged.append((st, en))
        # Fallback: simple amplitude thresholding if no segments found
        if not merged:
            abs_amp = np.abs(y)
            # Frame and threshold on mean abs amplitude
            try:
                frames = librosa.util.frame(abs_amp, frame_length=frame_length, hop_length=hop_length)
                frame_mean = frames.mean(axis=0)
            except Exception:
                frame_mean = np.array([abs_amp.mean()])
            thr2 = max(frame_mean.mean() * 0.5, 0.02)
            voiced2 = frame_mean > thr2
            segs2: List[Tuple[int, int]] = []
            start2: Optional[int] = None
            for i, flag in enumerate(voiced2):
                if flag and start2 is None:
                    start2 = i
                elif not flag and start2 is not None:
                    segs2.append((start2, i))
                    start2 = None
            if start2 is not None:
                segs2.append((start2, len(voiced2)))
            merged2: List[Tuple[float, float]] = []
            for s, e in segs2:
                st = s * frame_sec
                en = max(st, e * frame_sec)
                if en - st >= min_speech_sec:
                    if merged2 and st - merged2[-1][1] < min_silence_sec:
                        pst, pen = merged2[-1]
                        merged2[-1] = (pst, en)
                    else:
                        merged2.append((st, en))
            return merged2
        return merged

    def chunk(self, file_path: str) -> List[AudioChunk]:
        """Load audio, detect segments, write per-segment WAV files, return metadata."""
        y, sr = librosa.load(file_path, sr=self.target_sr, mono=True)
        segments = self._detect_segments(y, sr)

        chunks: List[AudioChunk] = []
        for (st, en) in segments:
            s_idx = int(st * sr)
            e_idx = int(en * sr)
            segment = y[s_idx:e_idx]
            if len(segment) == 0:
                continue
            cid = str(uuid.uuid4())
            out_name = f"chunk_{cid}.wav"
            out_path = self.output_dir / out_name
            sf.write(str(out_path), segment, sr)

            chunks.append(
                AudioChunk(
                    chunk_id=cid,
                    file_path=str(out_path),
                    start_time=float(st),
                    end_time=float(en),
                    duration=float(en - st),
                )
            )
        return chunks
