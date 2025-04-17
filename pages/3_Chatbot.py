import streamlit as st
from datetime import datetime
import os
import json


# Import your RAG engine from the appropriate module
# from rag_engine import RAGEngine  # Uncomment and adjust the import path

st.set_page_config(page_title="Chat dengan Dokumen", layout="wide")
st.title("💬 Chatbot KMS")

# Initialize RAG engine if not in session state
if "rag_engine" not in st.session_state:
    # Uncomment and use the actual import path for your RAGEngine
    # from rag_engine import RAGEngine
    # st.session_state.rag_engine = RAGEngine(
    #     persist_directory="./chroma_db",
    #     reset_db=False
    # )
    pass  # Remove this line when you uncomment the above

# Cek login
if not st.session_state.get("logged_in"):
    st.experimental_set_query_params(page="login")
    st.stop()

def simpan_chat_ke_file(entry, username):
    import json
    os.makedirs("chat_logs", exist_ok=True)
    tanggal = datetime.now().strftime("%Y-%m-%d")
    filename = f"chat_logs/{username}_{tanggal}.json"

    history = []
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                content = f.read().strip()
                if content:
                    history = json.loads(content)
        except Exception as e:
            print(f"❌ Gagal membaca file JSON lama: {e}")
            history = []

    history.append(entry)

    with open(filename, "w") as f:
        json.dump(history, f, indent=2)


# Tombol Logout
with st.sidebar:
    username = st.session_state.get("username", "Tidak diketahui")
    st.markdown(f"**Akun:** `{username}`")
    if st.button("Logout"):
        for key in ["logged_in", "username", "role", "messages", "rag_engine", "db_initialized", "chat_history", "last_sources"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params(page="login")
        st.stop()

# Verifikasi status database sebelum menampilkan chat
rag = st.session_state.get("rag_engine")
db_initialized = st.session_state.get("db_initialized", False)

# Debug info
with st.sidebar:
    if st.checkbox("Tampilkan Debug Info"):
        st.write("Debug Information:")
        st.write(f"- DB Initialized: {db_initialized}")
        
        if rag:
            try:
                docs = rag.vectorstore.get()
                doc_count = len(docs.get("documents", []))
                st.write(f"- Jumlah dokumen di DB: {doc_count}")
                
                file_counts = rag.list_indexed_files()
                if file_counts:
                    st.write("Dokumen terindeks:")
                    for file, count in file_counts.items():
                        st.write(f"  - {file}: {count} chunks")
                else:
                    st.write("Tidak ada dokumen terindeks")
            except Exception as e:
                st.write(f"Error saat mengambil info: {str(e)}")
        else:
            st.write("- RAG Engine belum diinisialisasi")

# Cek dokumen
if not db_initialized:
    st.warning("⚠️ Belum ada dokumen yang terindeks. Silakan upload dan proses dokumen terlebih dahulu.")
    
    if st.button("🔄 Cek ulang status database"):
        if rag:
            try:
                docs = rag.vectorstore.get()
                doc_count = len(docs.get("documents", []))
                if doc_count > 0:
                    st.session_state.db_initialized = True
                    st.success(f"✅ Database berisi {doc_count} chunks!")
                    st.rerun()
                else:
                    st.error("Database kosong. Silakan upload dan indeks dokumen.")
            except Exception as e:
                st.error(f"Error: {e}")
    st.stop()

# Simpan chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Simpan sumber terakhir agar bisa dipakai di luar spinner
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

# Tampilkan chat sebelumnya
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["message"])

# Input pengguna
query = st.chat_input("Tanyakan sesuatu berdasarkan dokumen...")

if query:
    timestamp = datetime.now().isoformat()
    username = st.session_state.get("username", "anon")

    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.chat_history.append({"role": "user", "message": query})

    with st.chat_message("assistant"):
        with st.spinner("🔍 Mencari jawaban dari dokumen..."):
            try:
                rag = st.session_state.get("rag_engine")
                if not rag:
                    raise ValueError("RAG Engine tidak tersedia")

                response = rag.query(query, debug=True)
                answer_text = response.get("result", "Maaf, tidak dapat memberikan jawaban.")
                st.markdown(answer_text)

                # Tampilkan dan simpan sumber jika ada
                formatted_sources = response.get("formatted_sources", [])
                st.session_state.last_sources = formatted_sources

                if formatted_sources:
                    with st.expander("Sumber Referensi"):
                        for i, src in enumerate(formatted_sources):
                            st.markdown(f"**{i+1}. {src['file']}** (Halaman {src['page']}) - Skor: {src['score']}")
                            st.text(src['chunk_preview'] + "...")
                            st.divider()

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "message": answer_text
                })

                # ⏺️ Simpan log ke file
                simpan_chat_ke_file({
                    "timestamp": timestamp,
                    "username": username,
                    "query": query,
                    "response": answer_text,
                    "sources": formatted_sources
                }, username)

            except Exception as e:
                error_msg = f"Terjadi kesalahan: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "message": f"❌ {error_msg}"
                })
                simpan_chat_ke_file({
                    "timestamp": timestamp,
                    "username": username,
                    "query": query,
                    "response": f"❌ {error_msg}",
                    "sources": []
                }, username)

