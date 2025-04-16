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

# Upload dokumen
uploaded_file = st.file_uploader("📁 Pilih dokumen PDF atau TXT", type=["pdf", "txt"])

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
