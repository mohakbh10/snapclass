import streamlit as st

from src.pipelines.voice_pipeline import (
    AudioAnalysisStatus,
    process_bulk_audio,
)

import pandas as pd

from datetime import datetime


_ANALYSIS_FAILURE_MESSAGES = {
    AudioAnalysisStatus.UNUSABLE_AUDIO: (
        "No usable speech was detected. Record clearly audible speech lasting "
        "at least 0.5 seconds, then analyze again."
    ),
    AudioAnalysisStatus.INVALID_PROFILES: (
        "Voice attendance requires a valid voice profile for every enrolled "
        "student. This app cannot update existing profiles; use photo "
        "attendance or have the missing/invalid profile corrected in Supabase."
    ),
    AudioAnalysisStatus.ANALYSIS_FAILED: (
        "Audio analysis failed. Check the recording and try again."
    ),
}


def _apply_analysis_result(analysis_result, enrolled_students, subject_id):
    """Store a reviewable roster only when speech analysis completed."""
    if analysis_result.status not in {
        AudioAnalysisStatus.MATCHES_FOUND,
        AudioAnalysisStatus.NO_MATCHES,
    }:
        st.session_state['voice_attendance_results'] = None
        st.session_state['voice_attendance_no_match_review'] = None
        st.error(_ANALYSIS_FAILURE_MESSAGES[analysis_result.status])
        return False

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if analysis_result.status == AudioAnalysisStatus.NO_MATCHES:
        roster = pd.DataFrame([
            {
                "Name": node['students']['name'],
                "ID": node['students']['student_id'],
                "Attendance": "Needs review",
            }
            for node in enrolled_students
        ])
        st.session_state['voice_attendance_results'] = None
        st.session_state['voice_attendance_no_match_review'] = (
            roster, subject_id, timestamp
        )
        return True

    results, attendance_to_log = [], []
    for node in enrolled_students:
        student = node['students']
        student_id = student['student_id']
        score = analysis_result.matches.get(student_id)
        is_present = student_id in analysis_result.matches
        results.append({
            "Name": student['name'],
            "ID": student_id,
            "Source": score if is_present else "-",
            "Status": "✅ Present" if is_present else "❌ Absent",
        })
        attendance_to_log.append({
            'student_id': student_id,
            'subject_id': subject_id,
            'timestamp': timestamp,
            'is_present': is_present,
        })

    st.session_state['voice_attendance_results'] = (
        pd.DataFrame(results), attendance_to_log
    )
    return True


def _build_manual_attendance_logs(reviewed_roster, subject_id, timestamp):
    """Require an explicit attendance choice for every no-match roster row."""
    valid_choices = {"Present", "Absent"}
    if not set(reviewed_roster["Attendance"]).issubset(valid_choices):
        return None
    return [
        {
            "student_id": row["ID"],
            "subject_id": subject_id,
            "timestamp": timestamp,
            "is_present": row["Attendance"] == "Present",
        }
        for _, row in reviewed_roster.iterrows()
    ]


def _read_audio_input(audio_data):
    """Return recorded bytes, or None when the widget has no recording."""
    if audio_data is None:
        return None
    return audio_data.read()


@st.dialog('Voice Attendance')
def voice_attendance_dialog(selected_subject_id):
    from src.components.dialog_attendance_results import show_attendance_result
    from src.database.config import supabase

    st.write('Record audio of students saying I am present. Then AI will recognize the students')


    audio_data = None

    audio_data = st.audio_input("Record classroom audio")

    if st.button('Analyze Audio', width='stretch', type='primary'):
        # Discard any old proposal so a failed retry cannot leave stale save controls.
        st.session_state['voice_attendance_results'] = None
        st.session_state['voice_attendance_no_match_review'] = None
        audio_bytes = _read_audio_input(audio_data)
        if audio_bytes is None:
            st.warning('Record audio before analyzing attendance.')
            return
        with st.spinner('Processing Audio data'):
            enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id',selected_subject_id ).execute()
            enrolled_students = enrolled_res.data

            if not enrolled_students:
                st.warning('No students enrolled in this course')
                return
            if any(not node.get('students') for node in enrolled_students):
                st.error('Could not load all enrolled student profiles. Refresh and try again.')
                return
            candidates_dict = {
                node['students']['student_id']: node['students'].get('voice_embedding')
                for node in enrolled_students
            }

            analysis_result = process_bulk_audio(audio_bytes, candidates_dict)
            _apply_analysis_result(
                analysis_result, enrolled_students, selected_subject_id
            )

    pending_review = st.session_state.get('voice_attendance_no_match_review')
    if pending_review:
        roster, subject_id, timestamp = pending_review
        st.warning(
            "Speech was analyzed, but no enrolled speaker matched. Select "
            "Present or Absent for each student before preparing attendance."
        )
        reviewed_roster = st.data_editor(
            roster,
            hide_index=True,
            disabled=["Name", "ID"],
            column_config={
                "Attendance": st.column_config.SelectboxColumn(
                    "Attendance",
                    options=["Needs review", "Present", "Absent"],
                    required=True,
                )
            },
            key="voice_no_match_attendance_review",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button('Dismiss', width='stretch'):
                st.session_state['voice_attendance_no_match_review'] = None
                st.rerun()
        with col2:
            unresolved = not set(reviewed_roster["Attendance"]).issubset(
                {"Present", "Absent"}
            )
            if st.button(
                'Prepare Attendance',
                type='primary',
                width='stretch',
                disabled=unresolved,
            ):
                logs = _build_manual_attendance_logs(
                    reviewed_roster, subject_id, timestamp
                )
                display_roster = reviewed_roster.copy()
                display_roster["Source"] = "Teacher review"
                display_roster["Status"] = display_roster.pop("Attendance")
                st.session_state['voice_attendance_results'] = (
                    display_roster[["Name", "ID", "Source", "Status"]], logs
                )
                st.session_state['voice_attendance_no_match_review'] = None
                st.rerun()

    if st.session_state.get('voice_attendance_results'):
        st.divider()
        df_results, logs = st.session_state.voice_attendance_results
        show_attendance_result(df_results, logs)
