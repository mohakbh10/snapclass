ATTENDANCE_STATE_KEYS = (
    "attendance_images",
    "attendance_subject_id",
    "voice_attendance_results",
    "voice_attendance_no_match_review",
    "photo_tab",
    "dialog_cam_last_bytes",
    "dialog_upload_last_names",
)

USER_STATE_KEYS = (
    "student_data",
    "teacher_data",
    "is_logged_in",
    "user_role",
    "teacher_login_type",
    "current_teacher_tab",
)


def clear_voice_attendance_state(session_state):
    session_state.pop("voice_attendance_results", None)
    session_state.pop("voice_attendance_no_match_review", None)


def clear_attendance_state(session_state):
    for key in ATTENDANCE_STATE_KEYS:
        session_state.pop(key, None)


def clear_user_state(session_state):
    for key in USER_STATE_KEYS:
        session_state.pop(key, None)
    clear_attendance_state(session_state)
