import streamlit as st
from login import login_page

st.set_page_config(page_title="Sistem RAG", layout="wide")

# Cek login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Deteksi jika sedang logout via query param
params = st.experimental_get_query_params()
if not st.session_state.logged_in or params.get("page") == ["login"]:
    # Reset query param & sembunyikan sidebar
    st.experimental_set_query_params()
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

    login_page()
    st.stop()
