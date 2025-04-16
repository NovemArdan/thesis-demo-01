import streamlit as st
from datetime import datetime

# Cek login
if not st.session_state.get("logged_in"):
    st.experimental_set_query_params(page="login")
    st.rerun()

st.set_page_config(page_title="Chat dengan Dokumen", layout="wide")
st.title("Chatbot KMS")

# Tombol Logout
with st.sidebar:
    username = st.session_state.get("username", "Tidak diketahui")
    st.markdown(f"**Akun:** `{username}`")
    if st.button("Logout"):
        for key in ["logged_in", "username", "role", "messages", "rag_engine", "db_initialized"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params(page="login")
        st.rerun()

# Pastikan dokumen sudah diindeks
if not st.session_state.get("db_initialized"):
    st.warning("⚠️ Belum ada dokumen yang terindeks. Silakan upload dan proses dokumen terlebih dahulu.")
    st.stop()

# Simpan history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat input
query = st.chat_input("Tanyakan sesuatu berdasarkan dokumen...")

# Tampilkan chat history
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["message"])

# Proses input user
if query:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.chat_history.append({"role": "user", "message": query})

    with st.chat_message("assistant"):
        with st.spinner("🔍 Mencari jawaban dari dokumen..."):
            try:
                rag = st.session_state["rag_engine"]
                response = rag.query(query)
                answer = response["result"]
                sources = response.get("formatted_sources", [])

                st.markdown(answer)
                if sources:
                    with st.expander("📚 Sumber Dokumen"):
                        for s in sources:
                            st.markdown(f"📄 **{s['file']}**, {s.get('page', '')}, Pasal {s.get('pasal', '-')}")
                            st.code(s["chunk_preview"], language="markdown")
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {e}")
                answer = "Terjadi error saat menjawab pertanyaan."

    st.session_state.chat_history.append({"role": "assistant", "message": answer})
