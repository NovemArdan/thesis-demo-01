import streamlit as st
import os

# Cek login
if not st.session_state.get("logged_in"):
    st.experimental_set_query_params(page="login")
    st.rerun()

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
else:
    file_list = os.listdir(docs_folder)
    if not file_list:
        st.info("📭 Folder kosong. Belum ada file.")
    else:
        for i, filename in enumerate(sorted(file_list), 1):
            file_path = os.path.join(docs_folder, filename)
            file_size_kb = os.path.getsize(file_path) / 1024  # in KB

            with open(file_path, "rb") as file_data:
                st.markdown(f"**{i}.** `{filename}`  \n💾 {file_size_kb:.2f} KB")
                st.download_button(
                    label="⬇️ Download",
                    data=file_data,
                    file_name=filename,
                    mime="application/octet-stream"
                )
            st.divider()
