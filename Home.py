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

# Validasi API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("OPENAI_API_KEY tidak ditemukan di .env")
    st.stop()

# Coba validasi API key sebelum inisialisasi lengkap
try:
    from langchain.embeddings.openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=openai_api_key
    )
    # Test dengan embedding sederhana
    test_embed = embeddings.embed_query("test")
    if not test_embed or len(test_embed) == 0:
        st.error("API key valid tetapi respons embedding tidak valid")
        st.stop()
except Exception as e:
    st.error(f"API key tidak valid atau terjadi kesalahan: {e}")
    st.stop()

# Inisialisasi RAGEngine hanya sekali
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = RAGEngine(
        persist_directory="chroma_db",
        openai_api_key=openai_api_key
    )

# Verifikasi database
if "db_initialized" not in st.session_state:
    if os.path.exists("chroma_db"):
        # Verifikasi database berisi data
        try:
            rag = st.session_state.get("rag_engine")
            docs = rag.vectorstore.get()
            document_count = len(docs.get("documents", []))
            st.session_state.db_initialized = document_count > 0
            if document_count > 0:
                st.success(f"Database loaded with {document_count} document chunks")
            else:
                st.warning("Database exists but contains no documents. Please upload documents.")
        except Exception as e:
            st.error(f"Error checking database: {e}")
            st.session_state.db_initialized = False
    else:
        st.session_state.db_initialized = False

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