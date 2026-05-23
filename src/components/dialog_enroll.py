import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase

import time


@st.dialog("Enroll in Subject")
def enroll_dialog():
    st.write('Enter the subject code provided by your teacher to enroll')
    join_code = st.text_input('Subject Code', placeholder='Eg. CS101')

    if st.button('Enroll now', type='primary', width='stretch'):
        if join_code:
            res = supabase.table('subjects').select('subject_id, name, subject_code').eq('subject_code', join_code).execute() #.eq('subject_code', join_code) is used to filter the subjects based on the entered code
            if res.data:
                subject = res.data[0] # Assuming subject codes are unique, we take the first match
                student_id = st.session_state.student_data['student_id'] # Get the current student's ID from session state

                check = supabase.table('subject_students').select('*').eq('subject_id', subject['subject_id']).eq('student_id', student_id).execute() # Check if the student is already enrolled in the subject
                if check.data:
                    st.warning('You are already enrolled in this program') 
                else:
                    enroll_student_to_subject(student_id, subject['subject_id']) # Enroll the student in the subject
                    st.success('Succesfully enrolled!')
                    time.sleep(1)
                    st.rerun()
        else:
            st.warning('Please enter a subject code')