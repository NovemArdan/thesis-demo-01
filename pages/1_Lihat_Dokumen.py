import streamlit as st
import os
import json

# Cek login
if not st.session_state.get("logged_in"):
    st.warning("Anda harus login terlebih dahulu")
    st.stop()

st.title("📄 Manajemen Dokumen")

# Tombol Logout
with st.sidebar:
    username = st.session_state.get("username", "Tidak diketahui")
    st.markdown(f"**Akun:** `{username}`")
    if st.button("Logout"):
        for key in ["logged_in", "username", "role", "rag_engine", "db_initialized", "history", "chat_history", "selected_file"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params(page="login")
        st.rerun()

# Folder dokumen
docs_folder = "railway_docs"
if not os.path.exists(docs_folder):
    st.warning("📭 Belum ada dokumen yang diupload.")
    st.stop()

# Ambil semua file
all_files = sorted([f for f in os.listdir(docs_folder) if not f.endswith(".meta.json")])
if not all_files:
    st.info("📭 Folder kosong. Belum ada file.")
    st.stop()

# ===============================
# 🔀 Mode: Lihat Detail atau Daftar
# ===============================
selected_file = st.session_state.get("selected_file")

if selected_file:
    # ============================
    # 📄 TAMPILKAN DETAIL DOKUMEN
    # ============================

    file_path = os.path.join(docs_folder, selected_file)
    meta_path = file_path + ".meta.json"
    metadata = {}

    if not os.path.exists(file_path):
        st.error("❌ File tidak ditemukan.")
        st.session_state.pop("selected_file", None)
        st.stop()

    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            metadata = json.load(f)

    st.button("⬅️ Lihat Daftar Dokumen", on_click=lambda: st.session_state.pop("selected_file", None))
    st.subheader(f"📄 Detail: `{selected_file}`")

    file_size_kb = os.path.getsize(file_path) / 1024
    st.markdown(f"💾 Ukuran: **{file_size_kb:.2f} KB**")
    st.markdown(f"🕒 Tanggal Upload: `{metadata.get('upload_at', '-')}`")
    st.markdown(f"👤 Diunggah oleh: `{metadata.get('upload_by', '-')}`")
    st.markdown(f"📂 Jenis Dokumen: `{metadata.get('jenis_dokumen', '-')}`")
    st.markdown(f"📝 Deskripsi:\n{metadata.get('deskripsi', '-')}")

    with open(file_path, "rb") as f:
        st.download_button("⬇️ Download File", data=f, file_name=selected_file)

    # Admin-only edit
    if st.session_state.get("role") == "admin":
        st.markdown("---")
        st.subheader("✏️ Edit Metadata")

        jenis_opsi = ["Umum", "Rahasia", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
        jenis_idx = jenis_opsi.index(metadata.get("jenis_dokumen", "Umum")) if metadata.get("jenis_dokumen", "Umum") in jenis_opsi else 0
        new_jenis = st.selectbox("Jenis Dokumen", jenis_opsi, index=jenis_idx)
        new_deskripsi = st.text_area("Deskripsi", metadata.get("deskripsi", ""))

        if st.button("💾 Simpan Perubahan Metadata"):
            metadata["jenis_dokumen"] = new_jenis
            metadata["deskripsi"] = new_deskripsi
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)
            st.success("✅ Metadata diperbarui.")
            st.rerun()

        st.subheader("🗑️ Hapus Dokumen")
        confirm = st.checkbox("Saya yakin ingin menghapus dokumen ini")
        if confirm and st.button("❌ Hapus Permanen"):
            try:
                os.remove(file_path)
                if os.path.exists(meta_path):
                    os.remove(meta_path)

                rag_engine = st.session_state.get("rag_engine")
                if rag_engine:
                    rag_engine.delete_document(selected_file)

                st.success("✅ Dokumen berhasil dihapus.")
                st.session_state.pop("selected_file", None)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal menghapus dokumen: {e}")

else:
    # ============================
    # 📋 TAMPILKAN DAFTAR DOKUMEN
    # ============================
    st.subheader("🔎 Filter Dokumen")

    search_query = st.text_input("Cari nama/deskripsi dokumen:")
    jenis_opsi = ["Semua", "Umum", "Rahasia", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
    filter_jenis = st.selectbox("Filter berdasarkan jenis dokumen:", jenis_opsi)

    filtered_files = []

    for filename in all_files:
        file_path = os.path.join(docs_folder, filename)
        meta_path = file_path + ".meta.json"
        metadata = {}

        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metadata = json.load(f)

        match_search = search_query.lower() in filename.lower() or search_query.lower() in metadata.get("deskripsi", "").lower()
        match_jenis = filter_jenis == "Semua" or metadata.get("jenis_dokumen") == filter_jenis

        if match_search and match_jenis:
            filtered_files.append((filename, metadata))

    if not filtered_files:
        st.info("Tidak ada dokumen yang cocok dengan filter.")
    else:
        st.subheader("📄 Daftar Dokumen")
        for i, (filename, metadata) in enumerate(filtered_files, 1):
            if st.button(f"📂 {filename}", key=f"select_{filename}"):
                st.session_state.selected_file = filename
                st.rerun()
