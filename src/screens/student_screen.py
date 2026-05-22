import time

import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embedding, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import get_all_students, create_student


def student_dashboard():
    st.header(f"Welcome, {st.session_state.student_data['name']}!", text_alignment='center')
    st.image("https://i.ibb.co/844D9Lrt/mascot-student.png", width=120, caption="Student Mascot")
    st.subheader("Your Attendance Record", text_alignment='center')

def student_screen():

    style_background_dashboard()
    style_base_layout()


    if "student_data" in st.session_state:
        student_dashboard()
        return
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')

    with c1:
        header_dashboard()

    with c2:
        if st.button(
            "Go back to Home",
            type='secondary',
            key='loginbackbtn',
            shortcut="control+backspace"
        ):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using FaceID', text_alignment='center')

    st.space()
    st.space()


    show_registration = False
    photo_source=st.camera_input("Position your face in the center")

    if photo_source:
        img=np.array(Image.open(photo_source))

        with st.spinner('AI is scanning...'):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.error("No face detected. Please try again.")
            elif num_faces > 1:
                st.error("Multiple faces detected. Please ensure only one face is visible.")
            else:
                if detected:
                    student_id = list (detected.keys())[0]
                    all_students = get_all_students()
                    student= next((s for s in all_students if s['student_id'] == student_id), None)

                    if student:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data= student
                        st.toast(f"Welcome back, {student['name']}!", icon="👋")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("Face not recognized. You might be a new student!")
                    show_registration = True
    if show_registration:
        with st.container():
            st.header('Register new Profile')
            new_name = st.text_input("Enter your name", placeholder="Your Name")

            st.subheader('Optional : Voice Enrollment')
            st.info("Enroll your voice only attedance")

            audio_data = None

            try:
                audio_data = st.audio_input("Record a short phrase like I am present, my name is Akash.")
            except Exception:
                st.error('Audio data failed')

            if st.button("Create Account", type='primary'):
                if new_name:
                    with st.spinner('Creating your profile...'):
                        # Here you would typically send the new_name and audio_data to your backend to create a new student profile
                        img = np.array(Image.open(photo_source))
                        encodings = get_face_embedding(img)    
                        if encodings:
                            face_emb = encodings[0].tolist()  # Convert numpy array to list for JSON serialization  

                            voice_emb = None
                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())     

                            response_data = create_student(new_name, face_embedding = face_emb, voice_embedding = voice_emb)  # This function should handle the backend API call to create a new student profile

                            if response_data:
                                train_classifier()  # Retrain the SVM model with the new student data
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data= response_data[0]  # Assuming the API returns the created student data in the response
                                st.toast(f"Profile created! Hi {new_name}!", icon="👋")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Couldnt capture your facial features for recognition. Please try again.")
                                
                else:
                    st.warning("Please enter your name to create an account.")


    footer_dashboard()