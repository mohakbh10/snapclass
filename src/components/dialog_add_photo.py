import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
from PIL import Image
import time


@st.dialog("Capture or upload photos")
def add_photos_dialog():

    st.write('Add classroom photos to scan for attendance')

    if 'photo_tab' not in st.session_state:
        st.session_state.photo_tab = 'camera'

    t1, t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state.photo_tab == 'camera' else 'tertiary'
        if st.button('Camera', type=type_camera, width='stretch'):
            st.session_state.photo_tab = 'camera'



    with t2:
        type_upload = "primary" if st.session_state.photo_tab == 'upload' else 'tertiary'
        if st.button('Upload photos', type=type_upload, width='stretch'):
            st.session_state.photo_tab = 'upload'

    if st.session_state.photo_tab == 'camera':
        cam_photo = st.camera_input('Take Snapshot', key='dialog_cam')
        if cam_photo:
            if 'dialog_cam_last_bytes' not in st.session_state:
                st.session_state.dialog_cam_last_bytes = None
            photo_bytes = cam_photo.getvalue()
            if photo_bytes != st.session_state.dialog_cam_last_bytes:
                st.session_state.attendance_images.append(Image.open(cam_photo))
                st.session_state.dialog_cam_last_bytes = photo_bytes
                st.toast('Photo Captured')


    if st.session_state.photo_tab == 'upload':
        uploaded_files = st.file_uploader('choose image files', type=['jpg', 'png', 'jpeg'], accept_multiple_files=True, key='dialog_upload')

        if uploaded_files:
            if 'dialog_upload_last_names' not in st.session_state:
                st.session_state.dialog_upload_last_names = []
            uploaded_names = [f.name for f in uploaded_files]
            if uploaded_names != st.session_state.dialog_upload_last_names:
                for f in uploaded_files:
                    st.session_state.attendance_images.append(Image.open(f))
                st.session_state.dialog_upload_last_names = uploaded_names
                st.toast('Photo Uploaded Successfully')

    st.divider()
    if st.button('Done', type='primary', width='stretch'):
        st.rerun()

""""
what is happening? 
This code defines a dialog component in Streamlit that allows users to capture photos using their camera or upload photos from their device. The photos are stored in the session state under 'attendance_images'. The dialog has two tabs: one for the camera and one for uploading photos. When a photo is captured or uploaded, it is added to the session state and a toast notification is shown. The user can click 'Done' to close the dialog and return to the main interface. 
"""