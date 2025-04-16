import streamlit as st
import os

# Cek login
if not st.session_state.get("logged_in"):
    st.experimental_set_query_params(page="login")
    st.rerun()

# Cek role admin
if st.session_state.get("role") != "admin":
    st.error("❌ Halaman ini hanya dapat diakses oleh Admin.")
    st.stop()

st.title("📤 Upload Dokumen Perkeretaapian")

# Tombol Logout
with st.sidebar:
    username = st.session_state.get("username", "Tidak diketahui")
    st.markdown(f"**Akun:** `{username}`")
    if st.button("Logout"):
        for key in ["logged_in", "username", "role", "messages", "rag_engine", "db_initialized"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params(page="login")
        st.rerun()

# Upload dokumen
uploaded_files = st.file_uploader(
    "📁 Pilih dokumen PDF atau TXT untuk diunggah",
    type=["pdf", "txt"],
    accept_multiple_files=True
)

if uploaded_files:
    if not os.path.exists("railway_docs"):
        os.makedirs("railway_docs")

    for file in uploaded_files:
        with open(f"railway_docs/{file.name}", "wb") as f:
            f.write(file.getbuffer())
    st.success(f"{len(uploaded_files)} dokumen berhasil diunggah.")

# Tombol proses dokumen ke RAG
if st.button("🚀 Proses & Index Dokumen"):
    rag_engine = st.session_state.get("rag_engine")
    if rag_engine is None:
        st.error("❌ RAGEngine belum diinisialisasi.")
    else:
        with st.spinner("🔄 Memproses dokumen dan membangun indeks..."):
            try:
                chunks = rag_engine.load_and_index_documents("railway_docs")
                st.session_state.db_initialized = True
                st.success(f"✅ Berhasil mengindeks {chunks} potongan teks.")
            except Exception as e:
                st.error(f"❌ Gagal memproses dokumen: {str(e)}")
