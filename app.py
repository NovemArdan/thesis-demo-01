import streamlit as st
from login import login_page

# Set layout
st.set_page_config(page_title="Sistem RAG", layout="wide")

# Deteksi query param
params = st.experimental_get_query_params()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Kalau belum login ATAU sedang diarahkan ke login, tampilkan form login
if not st.session_state.logged_in or params.get("page") == ["login"]:
    st.experimental_set_query_params()  # hapus param agar bersih
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

    login_page()
    st.stop()
