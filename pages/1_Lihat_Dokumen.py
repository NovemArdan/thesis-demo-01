import streamlit as st
import os
import json

# # Cek login
# if not st.session_state.get("logged_in"):
#     st.experimental_set_query_params(page="login")
#     st.rerun()

# Cek login dengan struktur yang aman dari rekursi
if not st.session_state.get("logged_in"):
    st.warning("Anda harus login terlebih dahulu")
    st.stop()  # Gunakan st.stop() alih-alih st.rerun()

st.title("📄 Daftar Dokumen yang Diupload")

# Tombol Logout
with st.sidebar:
    username = st.session_state.get("username", "Tidak diketahui")
    st.markdown(f"**Akun:** `{username}`")
    if st.button("Logout"):
        for key in ["logged_in", "username", "role", "messages", "rag_engine", "db_initialized"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params(page="login")
        st.rerun()

# Folder dokumen
docs_folder = "railway_docs"
if not os.path.exists(docs_folder):
    st.warning("📭 Belum ada dokumen yang diupload.")
    st.stop()

all_files = sorted([f for f in os.listdir(docs_folder) if not f.endswith(".meta.json")])
if not all_files:
    st.info("📭 Folder kosong. Belum ada file.")
    st.stop()

# ============================
# 🔍 FILTER UI
# ============================
st.subheader("🔎 Filter Dokumen")

# Kolom pencarian
search_query = st.text_input("Cari nama/deskripsi dokumen:")

# Dropdown jenis dokumen
jenis_opsi = ["Semua", "Umum", "Rahasia", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
filter_jenis = st.selectbox("Filter berdasarkan jenis dokumen:", jenis_opsi)

# ============================
# 🔍 FILTERING FILE LIST
# ============================
filtered_files = []

for filename in all_files:
    file_path = os.path.join(docs_folder, filename)
    meta_path = file_path + ".meta.json"
    metadata = {}

    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            metadata = json.load(f)

    # Cek search (pada nama file & deskripsi)
    match_search = search_query.lower() in filename.lower() or search_query.lower() in metadata.get("deskripsi", "").lower()

    # Cek jenis dokumen
    match_jenis = filter_jenis == "Semua" or metadata.get("jenis_dokumen") == filter_jenis

    if match_search and match_jenis:
        filtered_files.append((filename, metadata))

# ============================
# ⬇️ TAMPILKAN FILE YANG LOLOS FILTER
# ============================

if not filtered_files:
    st.info("Tidak ada dokumen yang cocok dengan filter.")
else:
    for i, (filename, metadata) in enumerate(filtered_files, 1):
        file_path = os.path.join(docs_folder, filename)
        file_size_kb = os.path.getsize(file_path) / 1024

        st.markdown(f"### {i}. `{filename}`")
        st.markdown(f"💾 Ukuran: **{file_size_kb:.2f} KB**")
        st.markdown(f"🕒 Tanggal Upload: `{metadata.get('upload_at', '-')}`")
        st.markdown(f"👤 Diunggah oleh: `{metadata.get('upload_by', '-')}`")
        st.markdown(f"📂 Jenis Dokumen: `{metadata.get('jenis_dokumen', '-')}`")
        st.markdown(f"📝 Deskripsi:\n{metadata.get('deskripsi', '-')}")

        with open(file_path, "rb") as f:
            st.download_button("⬇️ Download File", data=f, file_name=filename)

        # Edit Metadata (khusus admin)
        if st.session_state.get("role") == "admin":
            with st.expander("✏️ Edit Metadata"):
                jenis_opsi_only = jenis_opsi[1:]  # buang "Semua"
                jenis_idx = jenis_opsi_only.index(metadata.get("jenis_dokumen", "Umum")) if metadata.get("jenis_dokumen", "Umum") in jenis_opsi_only else 0
                new_jenis = st.selectbox("Jenis Dokumen", jenis_opsi_only, index=jenis_idx, key=f"jenis_{filename}")
                new_deskripsi = st.text_area("Deskripsi", metadata.get("deskripsi", ""), key=f"desc_{filename}")
                if st.button(f"💾 Simpan Metadata - {filename}", key=f"simpan_{filename}"):
                    metadata["jenis_dokumen"] = new_jenis
                    metadata["deskripsi"] = new_deskripsi
                    with open(meta_path, "w") as f:
                        json.dump(metadata, f, indent=2)
                    st.success("Metadata berhasil diperbarui.")
                    st.rerun()
            with st.expander("🗑️ Hapus Dokumen"):
                confirm = st.checkbox(f"Saya yakin ingin menghapus dokumen `{filename}`", key=f"confirm_{filename}")
                if confirm:
                    if st.button(f"❌ Hapus Permanen - {filename}", key=f"delete_{filename}"):
                        try:
                            os.remove(file_path)
                            if os.path.exists(meta_path):
                                os.remove(meta_path)

                            # Hapus dari vectorstore
                            rag_engine = st.session_state.get("rag_engine")
                            if rag_engine:
                                rag_engine.delete_document(filename)

                            st.success(f"✅ Dokumen `{filename}` berhasil dihapus beserta data vector-nya.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Gagal menghapus dokumen: {e}")

        st.divider()
