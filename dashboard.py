import os
import streamlit as st
from dotenv import load_dotenv
from rag_engine import RAGEngine

def dashboard_main():
    # Cek login
    if not st.session_state.get("logged_in"):
        st.warning("Silakan login terlebih dahulu.")
        st.stop()

    load_dotenv()
    st.set_page_config(page_title="Knowledge Management Perkeretaapian", layout="wide")
    st.title(f"Sistem Knowledge Management - Selamat datang, {st.session_state['username']}")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False
    if "rag_engine" not in st.session_state:
        st.session_state.rag_engine = None

    @st.cache_resource
    def get_rag_engine():
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("OPENAI_API_KEY belum diset.")
            st.stop()
        engine = RAGEngine(persist_directory="./chroma_db", openai_api_key=openai_api_key)
        if os.path.exists("./chroma_db"):
            st.session_state.db_initialized = True
        return engine

    rag_engine = get_rag_engine()
    st.session_state.rag_engine = rag_engine

    with st.sidebar:
        st.header("Navigasi")
        st.write(f"Login sebagai: `{st.session_state['role']}`")

        # Tombol Logout
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()  # Kembali ke halaman login

        if st.session_state["role"] == "admin":
            st.subheader("Upload Dokumen")
            uploaded_files = st.file_uploader("Upload dokumen perkeretaapian", type=["pdf", "txt"], accept_multiple_files=True)
            if uploaded_files:
                if not os.path.exists("railway_docs"):
                    os.makedirs("railway_docs")
                for file in uploaded_files:
                    with open(f"railway_docs/{file.name}", "wb") as f:
                        f.write(file.getbuffer())
                if st.button("Proses Dokumen"):
                    with st.spinner("Memproses dokumen..."):
                        try:
                            chunks = rag_engine.load_and_index_documents("railway_docs")
                            st.session_state.db_initialized = True
                            st.success(f"{chunks} chunks berhasil diindeks.")
                        except Exception as e:
                            st.error(str(e))

    # Sisa kode untuk chat dan evaluasi tetap bisa kamu letakkan di sini
