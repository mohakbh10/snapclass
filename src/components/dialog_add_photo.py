import streamlit as st
from PIL import Image


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
