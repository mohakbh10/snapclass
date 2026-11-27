import streamlit as st

import segno
import io
from urllib.parse import urlencode


APP_URL = "https://snapclass-bymohak.streamlit.app/"


def build_join_url(subject_code, app_url=APP_URL):
    """Build the root Streamlit URL understood by app.py."""
    return f"{app_url}?{urlencode({'join-code': str(subject_code)})}"

@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    join_url = build_join_url(subject_code)

    st.header ("Scan to Join")

    qr = segno.make(join_url)

    out = io.BytesIO()

    qr.save(out, kind='png', scale=10, border=1)

    col1,col2 = st.columns(2)
    with col1:
        st.markdown ("###Copy Link")
        st.code(join_url, language="text")
        st.code(subject_code, language="text")
        st.info('Copy this link to share on Whatsapp or Email')
    with col2:
        st.markdown ("###Scan to Join")
        st.image(out.getvalue(), caption='QRCODE for class joining')
