import streamlit as st
import os
import json
from datetime import datetime

# Cek login
if not st.session_state.get("logged_in"):
    st.experimental_set_query_params(page="login")
    st.rerun()

# Cek role admin
if st.session_state.get("role") != "admin":
    st.error("❌ Halaman ini hanya dapat diakses oleh Admin.")
    st.stop()

st.title("📤 Upload Dokumen Perkeretaapian")

# Sidebar Logout
with st.sidebar:
    username = st.session_state.get("username", "Tidak diketahui")
    st.markdown(f"**Akun:** `{username}`")
    if st.button("Logout"):
        for key in ["logged_in", "username", "role", "messages", "rag_engine", "db_initialized"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params(page="login")
        st.rerun()

# Database Management Section
st.subheader("🔄 Database Management")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Re-indeks Semua Dokumen"):
        with st.spinner("Mengindeks ulang semua dokumen..."):
            try:
                from rag_engine import RAGEngine
                import os
                
                # Reset database dengan instance baru
                openai_api_key = os.getenv("OPENAI_API_KEY")
                rag_engine = RAGEngine(
                    persist_directory="chroma_db",
                    openai_api_key=openai_api_key,
                    reset_db=True  # Reset database sebelum indexing
                )
                st.session_state.rag_engine = rag_engine
                
                # Reindex all documents
                if os.path.exists("railway_docs"):
                    num_chunks = rag_engine.load_and_index_documents("railway_docs")
                    st.session_state.db_initialized = num_chunks > 0
                    st.success(f"📚 {num_chunks} chunks berhasil diindeks!")
                else:
                    st.error("❌ Folder 'railway_docs' tidak ditemukan!")
            except Exception as e:
                st.error(f"❌ Gagal re-indeks: {e}")

with col2:
    if st.button("🔍 Cek Status Database"):
        try:
            rag_engine = st.session_state.get("rag_engine")
            if not rag_engine:
                st.error("Engine tidak ditemukan di session.")
            else:
                file_counts = rag_engine.list_indexed_files()
                total_chunks = sum(file_counts.values())
                st.success(f"Database berisi {total_chunks} chunks dari {len(file_counts)} dokumen")
                
                # Tampilkan daftar dokumen
                if file_counts:
                    for file, count in file_counts.items():
                        st.write(f"- {file}: {count} chunks")
                else:
                    st.warning("Tidak ada dokumen terindeks.")
        except Exception as e:
            st.error(f"❌ Gagal cek status: {e}")

# Upload dokumen
st.subheader("📁 Upload Dokumen Baru")
uploaded_file = st.file_uploader("Pilih dokumen PDF atau TXT", type=["pdf", "txt"])

if uploaded_file:
    st.subheader("📄 Form Metadata Dokumen")

    # Gunakan nama asli, tapi bisa ubah
    file_ext = uploaded_file.name.split(".")[-1]
    default_name = ".".join(uploaded_file.name.split(".")[:-1])
    final_name = st.text_input("Nama File (tanpa ekstensi)", value=default_name)

    jenis_dokumen = st.selectbox("Jenis Dokumen", ["Umum", "Rahasia", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"])
    deskripsi = st.text_area("Deskripsi Dokumen", placeholder="Masukkan deskripsi dokumen...")

    if st.button("✅ Simpan Dokumen dan Metadata"):
        # Siapkan folder
        if not os.path.exists("railway_docs"):
            os.makedirs("railway_docs")

        # Simpan file dan metadata
        final_filename = f"{final_name}.{file_ext}"
        filepath = os.path.join("railway_docs", final_filename)

        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())

        metadata = {
            "filename": final_filename,
            "upload_by": st.session_state.get("username", ""),
            "upload_at": datetime.now().isoformat(),
            "jenis_dokumen": jenis_dokumen,
            "deskripsi": deskripsi
        }
        with open(filepath + ".meta.json", "w") as f:
            json.dump(metadata, f, indent=2)

        st.success(f"✅ Dokumen `{final_filename}` berhasil diunggah dan metadata disimpan.")

        # Proses dokumen ke vectorstore
        with st.spinner("🔍 Memproses dan menyimpan ke vectorstore..."):
            try:
                rag_engine = st.session_state.get("rag_engine")
                if not rag_engine:
                    st.error("Engine tidak ditemukan di session.")
                else:
                    # Indeks hanya file baru
                    single_docs = rag_engine.load_documents(filepath)
                    chunks = rag_engine.process_documents(single_docs)
                    rag_engine.index_documents(chunks)
                    st.session_state.db_initialized = True
                    st.success(f"📚 Dokumen berhasil diproses dan disimpan ke vectorstore dalam {len(chunks)} chunk.")
            except Exception as e:
                st.error(f"❌ Gagal indexing dokumen ke vectorstore: {e}")

# Daftar dokumen yang ada
st.subheader("📚 Dokumen Terindeks")
if os.path.exists("railway_docs"):
    files = [f for f in os.listdir("railway_docs") if f.endswith('.pdf') or f.endswith('.txt')]
    if files:
        for file in files:
            meta_path = os.path.join("railway_docs", file + ".meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                    st.markdown(f"""
                    **{file}**  
                    - Jenis: {metadata.get('jenis_dokumen', 'N/A')}
                    - Deskripsi: {metadata.get('deskripsi', 'N/A')}
                    - Diupload oleh: {metadata.get('upload_by', 'N/A')}
                    - Tanggal: {metadata.get('upload_at', 'N/A')}
                    """)
                except:
                    st.write(f"- {file}")
            else:
                st.write(f"- {file}")
    else:
        st.info("Belum ada dokumen yang diunggah.")
else:
    st.info("Folder dokumen belum dibuat.")