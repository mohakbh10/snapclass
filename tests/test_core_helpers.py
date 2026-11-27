import unittest
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.components.dialog_share_subject import build_join_url
from src.components.dialog_voice_attendance import (
    _apply_analysis_result,
    _build_manual_attendance_logs,
    _read_audio_input,
)
from src.pipelines.voice_pipeline import (
    AudioAnalysisResult,
    AudioAnalysisStatus,
    VOICE_EMBEDDING_SIZE,
    identify_speaker,
    process_bulk_audio,
)


class JoinUrlTests(unittest.TestCase):
    def test_url_uses_root_route_and_router_parameter(self):
        url = build_join_url("CS 101/&A")
        parsed = urlparse(url)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "snapclass-bymohak.streamlit.app")
        self.assertEqual(parsed.path, "/")
        self.assertEqual(parse_qs(parsed.query), {"join-code": ["CS 101/&A"]})


class SpeakerMatchingTests(unittest.TestCase):
    def test_returns_best_candidate_above_threshold(self):
        speaker_id, score = identify_speaker(
            np.array([1.0, 0.0]),
            {7: [0.0, 1.0], 8: [2.0, 0.0]},
            threshold=0.65,
        )

        self.assertEqual(speaker_id, 8)
        self.assertAlmostEqual(score, 1.0)

    def test_rejects_low_similarity_and_malformed_candidates(self):
        speaker_id, score = identify_speaker(
            np.array([1.0, 0.0]),
            {0: [0.0, 1.0], 1: [1.0]},
            threshold=0.65,
        )

        self.assertIsNone(speaker_id)
        self.assertAlmostEqual(score, 0.0)

    def test_rejects_empty_or_non_finite_embeddings(self):
        self.assertEqual(identify_speaker(None, {1: [1.0, 0.0]}), (None, 0.0))
        self.assertEqual(
            identify_speaker(np.array([np.nan, 0.0]), {1: [1.0, 0.0]}),
            (None, 0.0),
        )


class BulkAudioAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.audio = np.ones(16000, dtype=float)
        self.profiles = {42: self._vector(0)}

    @staticmethod
    def _vector(index):
        vector = np.zeros(VOICE_EMBEDDING_SIZE, dtype=float)
        vector[index] = 1.0
        return vector

    def _analyze(self, segments, encoder_vector=None):
        segments = np.asarray(segments, dtype=int).reshape((-1, 2))

        class FakeEncoder:
            def embed_utterance(self, _wav):
                return encoder_vector

        with (
            patch(
                'src.pipelines.voice_pipeline.librosa.load',
                return_value=(self.audio, 16000),
            ),
            patch(
                'src.pipelines.voice_pipeline.librosa.effects.split',
                return_value=segments,
            ),
            patch(
                'src.pipelines.voice_pipeline.load_voice_encoder',
                return_value=FakeEncoder(),
            ),
            patch(
                'src.pipelines.voice_pipeline.preprocess_wav',
                side_effect=lambda samples: samples,
            ),
        ):
            return process_bulk_audio(b'valid audio bytes', self.profiles)

    def test_empty_audio_is_unusable(self):
        result = process_bulk_audio(b'', self.profiles)
        self.assertEqual(result.status, AudioAnalysisStatus.UNUSABLE_AUDIO)

    def test_audio_with_no_speech_segments_is_unusable(self):
        result = self._analyze([], self._vector(0))
        self.assertEqual(result.status, AudioAnalysisStatus.UNUSABLE_AUDIO)

    def test_only_short_segments_are_unusable(self):
        result = self._analyze([(0, 4000)], self._vector(0))
        self.assertEqual(result.status, AudioAnalysisStatus.UNUSABLE_AUDIO)

    def test_invalid_stored_profile_blocks_analysis(self):
        invalid_profiles = (
            [1.0, 0.0],
            [],
            np.full(VOICE_EMBEDDING_SIZE, np.nan),
            np.zeros(VOICE_EMBEDDING_SIZE),
            None,
        )
        with patch('src.pipelines.voice_pipeline.librosa.load') as load_audio:
            for profile in invalid_profiles:
                with self.subTest(profile=repr(profile)[:40]):
                    result = process_bulk_audio(
                        b'valid audio bytes', {42: profile}
                    )
                    self.assertEqual(
                        result.status, AudioAnalysisStatus.INVALID_PROFILES
                    )
        load_audio.assert_not_called()

    def test_valid_speech_with_no_matching_speaker_is_successful_no_match(self):
        result = self._analyze([(0, 16000)], self._vector(1))
        self.assertEqual(result.status, AudioAnalysisStatus.NO_MATCHES)
        self.assertEqual(result.matches, {})

    def test_valid_speech_with_matching_speaker_returns_match(self):
        result = self._analyze([(0, 16000)], self._vector(0))
        self.assertEqual(result.status, AudioAnalysisStatus.MATCHES_FOUND)
        self.assertIn(42, result.matches)

    def test_audio_decode_failure_is_explicit(self):
        with (
            patch(
                'src.pipelines.voice_pipeline.librosa.load',
                side_effect=ValueError('bad audio'),
            ),
            patch('src.pipelines.voice_pipeline.st.error'),
        ):
            result = process_bulk_audio(b'bad audio bytes', self.profiles)
        self.assertEqual(result.status, AudioAnalysisStatus.ANALYSIS_FAILED)

    def test_invalid_encoder_output_is_analysis_failure(self):
        result = self._analyze([(0, 16000)], np.array([1.0, 0.0]))
        self.assertEqual(result.status, AudioAnalysisStatus.ANALYSIS_FAILED)


class VoiceAttendanceDialogTests(unittest.TestCase):
    def test_missing_audio_input_returns_safely_without_reading(self):
        self.assertIsNone(_read_audio_input(None))

    def test_analysis_failure_clears_old_review_and_prevents_save_controls(self):
        state = {
            'voice_attendance_results': ('old review', 'old logs'),
            'voice_attendance_no_match_review': ('old roster', 5, 'old timestamp'),
        }
        failure = AudioAnalysisResult(AudioAnalysisStatus.ANALYSIS_FAILED, {})

        with (
            patch(
                'src.components.dialog_voice_attendance.st.session_state',
                state,
            ),
            patch('src.components.dialog_voice_attendance.st.error') as show_error,
        ):
            accepted = _apply_analysis_result(failure, [], 5)

        self.assertFalse(accepted)
        self.assertIsNone(state['voice_attendance_results'])
        self.assertIsNone(state['voice_attendance_no_match_review'])
        show_error.assert_called_once()

    def test_successful_no_match_still_creates_teacher_review(self):
        state = {}
        no_match = AudioAnalysisResult(AudioAnalysisStatus.NO_MATCHES, {})
        roster = [{'students': {'student_id': 42, 'name': 'A Student'}}]

        with patch(
            'src.components.dialog_voice_attendance.st.session_state',
            state,
        ):
            accepted = _apply_analysis_result(no_match, roster, 5)

        self.assertTrue(accepted)
        self.assertIsNone(state['voice_attendance_results'])
        review, subject_id, _ = state['voice_attendance_no_match_review']
        self.assertEqual(review.loc[0, 'Attendance'], 'Needs review')
        self.assertEqual(subject_id, 5)

    def test_no_match_attendance_requires_explicit_teacher_choices(self):
        pending_roster = pd.DataFrame([
            {'Name': 'A Student', 'ID': 42, 'Attendance': 'Needs review'}
        ])
        self.assertIsNone(_build_manual_attendance_logs(pending_roster, 5, 'ts'))

        pending_roster.loc[0, 'Attendance'] = 'Present'
        logs = _build_manual_attendance_logs(pending_roster, 5, 'ts')
        self.assertEqual(logs, [{
            'student_id': 42,
            'subject_id': 5,
            'timestamp': 'ts',
            'is_present': True,
        }])


if __name__ == "__main__":
    unittest.main()
