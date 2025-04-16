import streamlit as st
from login_handler import login_page
from rag_engine import RAGEngine
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Beranda", layout="wide")
load_dotenv()

# Init session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

params = st.experimental_get_query_params()
if not st.session_state.logged_in or params.get("page") == ["login"]:
    # ❗ jangan lanjut render halaman, stop di sini
    st.experimental_set_query_params()
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)
    login_page()
    st.stop()

# Inisialisasi RAGEngine hanya sekali
if "rag_engine" not in st.session_state:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        st.error("OPENAI_API_KEY tidak ditemukan di .env")
        st.stop()
    st.session_state.rag_engine = RAGEngine(
        persist_directory="chroma_db",
        openai_api_key=openai_api_key
    )

if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = os.path.exists("chroma_db")

# Konten halaman utama
st.title("🏠 Beranda")
st.markdown("Selamat datang di Knowledge Management System Perkeretaapian PT Kereta Api Indonesia (Persero)")

with st.sidebar:
    st.markdown(f"**Akun:** `{st.session_state.get('username', '')}`")
    if st.button("Logout"):
        for key in ["logged_in", "username", "role", "rag_engine", "db_initialized"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params(page="login")
        st.rerun()
