import unittest

from src.session_state import clear_attendance_state, clear_user_state


class SessionStateTests(unittest.TestCase):
    def test_user_logout_clears_auth_and_attendance_data_only(self):
        state = {
            'student_data': {'student_id': 10},
            'teacher_data': {'teacher_id': 20},
            'is_logged_in': True,
            'user_role': 'teacher',
            'teacher_login_type': 'register',
            'current_teacher_tab': 'attendance_records',
            'attendance_images': ['old image'],
            'attendance_subject_id': 3,
            'voice_attendance_results': ('old result', 'old logs'),
            'voice_attendance_no_match_review': ('old roster', 3, 'old time'),
            'dialog_cam_last_bytes': b'old image bytes',
            'dialog_upload_last_names': ['old.png'],
            'login_type': 'teacher',
            'theme': 'dark',
        }

        clear_user_state(state)

        self.assertEqual(state, {'login_type': 'teacher', 'theme': 'dark'})

    def test_subject_change_clears_pending_attendance_state(self):
        state = {
            'attendance_images': ['photo from previous subject'],
            'attendance_subject_id': 3,
            'voice_attendance_results': ('old result', 'old logs'),
            'voice_attendance_no_match_review': ('old roster', 3, 'old time'),
            'teacher_data': {'teacher_id': 20},
        }

        clear_attendance_state(state)

        self.assertEqual(state, {'teacher_data': {'teacher_id': 20}})


if __name__ == '__main__':
    unittest.main()
