import streamlit as st
import os, json, hashlib
from datetime import datetime

st.set_page_config(page_title="Chatbot KMS", layout="wide")
st.title("💬 Chatbot KMS")

# Cek login
if not st.session_state.get("logged_in"):
    st.query_params.clear()
    st.stop()

username = st.session_state.get("username", "anon")
os.makedirs("chat_logs", exist_ok=True)

def get_message_id(index, role, content):
    return hashlib.md5(f"{index}-{role}-{content[:50]}".encode()).hexdigest()

def get_chat_log_filename():
    tanggal = datetime.now().strftime("%Y-%m-%d")
    return f"chat_logs/{username}_{tanggal}.json"

def simpan_chat_log():
    with open(get_chat_log_filename(), "w", encoding="utf-8") as f:
        json.dump(st.session_state.history, f, indent=2, ensure_ascii=False)

def save_feedback(index):
    msg = st.session_state.history[index]
    feedback_value = st.session_state.get(f"feedback_{index}")
    msg["feedback"] = "OK" if feedback_value == 1 else "NOT_OK"
    msg["feedback_timestamp"] = datetime.now().isoformat()
    simpan_chat_log()

# Inisialisasi histori
if "history" not in st.session_state:
    st.session_state.history = []

# Tampilkan histori dan feedback
for i, message in enumerate(st.session_state.history):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            feedback_val = message.get("feedback")
            st.session_state[f"feedback_{i}"] = 1 if feedback_val == "OK" else 0 if feedback_val == "NOT_OK" else None
            st.feedback(
                "thumbs",
                key=f"feedback_{i}",
                on_change=save_feedback,
                args=[i],
                disabled=feedback_val is not None
            )

# Tangani input baru
if prompt := st.chat_input("Tanyakan sesuatu berdasarkan dokumen..."):
    # Simpan pesan user
    user_msg = {
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat(),
        "msg_id": get_message_id(len(st.session_state.history), "user", prompt)
    }
    st.session_state.history.append(user_msg)

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("📚 Mencari jawaban dari dokumen..."):
            try:
                rag = st.session_state.get("rag_engine")
                if not rag:
                    raise ValueError("❌ RAG Engine belum tersedia")

                result = rag.query(prompt, debug=True)
                answer = result.get("result", "Maaf, tidak ada jawaban.")
                sources = result.get("formatted_sources", [])

                # Tambahan log ke terminal
                print("\n📄 Daftar Chunk & Skor Similarity:")
                for i, src in enumerate(sources):
                    file = src.get("file", "-")
                    page = src.get("page", "-")
                    score = round(src.get("score", 0), 4)
                    preview = src.get("chunk_preview", "").strip().replace("\n", " ")[:100]
                    print(f"{i+1}. [{score}] {file} (hal. {page}) → {preview}...")


                # Tampilkan jawaban
                st.write(answer)

                assistant_msg = {
                    "role": "assistant",
                    "content": answer,
                    "timestamp": datetime.now().isoformat(),
                    "msg_id": get_message_id(len(st.session_state.history), "assistant", answer),
                    "query": prompt,
                    "sources": sources,
                    "feedback": None,
                    "feedback_timestamp": None
                }
                st.session_state.history.append(assistant_msg)
                simpan_chat_log()
                st.rerun()


            except Exception as e:
                st.error(f"Terjadi error: {e}")
