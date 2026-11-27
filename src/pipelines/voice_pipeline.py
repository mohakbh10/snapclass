from dataclasses import dataclass
from enum import Enum
import io

from resemblyzer import VoiceEncoder, preprocess_wav
import librosa
import numpy as np
import streamlit as st


VOICE_EMBEDDING_SIZE = 256
MIN_AUDIO_SEGMENT_SECONDS = 0.5
VOICE_SIMILARITY_THRESHOLD = 0.65


class AudioAnalysisStatus(str, Enum):
    MATCHES_FOUND = "matches_found"
    NO_MATCHES = "no_matches"
    UNUSABLE_AUDIO = "unusable_audio"
    INVALID_PROFILES = "invalid_profiles"
    ANALYSIS_FAILED = "analysis_failed"


@dataclass
class AudioAnalysisResult:
    status: AudioAnalysisStatus
    matches: dict


@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()


def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()
        audio, _ = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception:
        st.error("Voice profile creation failed. Check the recording and try again.")
        return None


def identify_speaker(new_embedding, candidates_dict, threshold=VOICE_SIMILARITY_THRESHOLD):
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    new_embedding = np.asarray(new_embedding, dtype=float)
    if new_embedding.ndim != 1 or not new_embedding.size or not np.all(np.isfinite(new_embedding)):
        return None, 0.0

    best_sid = None
    best_score = -1.0
    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding is not None:
            try:
                stored_embedding = np.asarray(stored_embedding, dtype=float)
            except (TypeError, ValueError):
                continue
            if (stored_embedding.shape != new_embedding.shape
                    or not np.all(np.isfinite(stored_embedding))):
                continue
            denominator = np.linalg.norm(new_embedding) * np.linalg.norm(stored_embedding)
            if denominator == 0 or not np.isfinite(denominator):
                continue
            similarity = float(np.dot(new_embedding, stored_embedding) / denominator)
            if similarity > best_score:
                best_score = similarity
                best_sid = sid

    if best_score >= threshold:
        return best_sid, best_score
    return None, best_score


def _validated_profiles(candidates_dict):
    """Validate every required profile; None means the roster is unusable."""
    if not isinstance(candidates_dict, dict) or not candidates_dict:
        return None

    profiles = {}
    for speaker_id, embedding in candidates_dict.items():
        try:
            vector = np.asarray(embedding, dtype=float)
        except (TypeError, ValueError, OverflowError):
            return None
        norm = np.linalg.norm(vector)
        if (vector.shape != (VOICE_EMBEDDING_SIZE,)
                or not np.all(np.isfinite(vector))
                or not np.isfinite(norm) or norm == 0):
            return None
        profiles[speaker_id] = vector

    return profiles or None


def process_bulk_audio(
    audio_bytes,
    candidates_dict,
    threshold=VOICE_SIMILARITY_THRESHOLD,
):
    """Analyze a recording and return a distinct status for every outcome."""
    profiles = _validated_profiles(candidates_dict)
    if profiles is None:
        return AudioAnalysisResult(AudioAnalysisStatus.INVALID_PROFILES, {})
    if not audio_bytes:
        return AudioAnalysisResult(AudioAnalysisStatus.UNUSABLE_AUDIO, {})

    try:
        audio, sample_rate = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        if (audio.size == 0 or audio.ndim != 1
                or not np.all(np.isfinite(audio))):
            return AudioAnalysisResult(AudioAnalysisStatus.UNUSABLE_AUDIO, {})

        segments = librosa.effects.split(audio, top_db=30)
        minimum_samples = int(sample_rate * MIN_AUDIO_SEGMENT_SECONDS)
        usable_segments = [
            (start, end) for start, end in segments
            if end - start >= minimum_samples
        ]
        if not usable_segments:
            return AudioAnalysisResult(AudioAnalysisStatus.UNUSABLE_AUDIO, {})

        encoder = load_voice_encoder()
        identified_results = {}
        for start, end in usable_segments:
            wav = preprocess_wav(audio[start:end])
            embedding = np.asarray(encoder.embed_utterance(wav), dtype=float)
            embedding_norm = np.linalg.norm(embedding)
            if (embedding.shape != (VOICE_EMBEDDING_SIZE,)
                    or not np.all(np.isfinite(embedding))
                    or not np.isfinite(embedding_norm) or embedding_norm == 0):
                return AudioAnalysisResult(AudioAnalysisStatus.ANALYSIS_FAILED, {})

            speaker_id, score = identify_speaker(embedding, profiles, threshold)
            if speaker_id is not None:
                if (speaker_id not in identified_results
                        or score > identified_results[speaker_id]):
                    identified_results[speaker_id] = score

        status = (AudioAnalysisStatus.MATCHES_FOUND if identified_results
                  else AudioAnalysisStatus.NO_MATCHES)
        return AudioAnalysisResult(status, identified_results)
    except Exception:
        return AudioAnalysisResult(AudioAnalysisStatus.ANALYSIS_FAILED, {})
