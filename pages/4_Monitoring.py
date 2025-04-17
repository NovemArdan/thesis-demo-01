import streamlit as st
import os
import json
from collections import Counter

st.set_page_config(page_title="Monitoring Sistem", layout="wide")
st.title("📊 Monitoring Sistem Chatbot KMS")

# Cek login dan role admin
if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
    st.error("Halaman ini hanya dapat diakses oleh admin.")
    st.stop()

# Folder log
LOG_FOLDER = "chat_logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

# Statistik awal
jumlah_pertanyaan = 0
jumlah_jawaban = 0
jumlah_dokumen = 0
jumlah_chunk = 0
feedback_counter = Counter()

# Ambil data dari chat_logs
for filename in os.listdir(LOG_FOLDER):
    if filename.endswith(".json"):
        filepath = os.path.join(LOG_FOLDER, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item.get("role") == "user":
                        jumlah_pertanyaan += 1
                    elif item.get("role") == "assistant":
                        jumlah_jawaban += 1
                        if item.get("feedback"):
                            feedback_counter[item.get("feedback")] += 1
        except Exception as e:
            st.warning(f"Gagal membaca {filename}: {e}")

# Ambil jumlah dokumen & chunk dari rag
rag = st.session_state.get("rag_engine")
if rag:
    try:
        vs_data = rag.vectorstore.get()
        all_chunks = vs_data.get("documents", [])
        all_metadatas = vs_data.get("metadatas", [])

        # Jumlah dokumen unik berdasarkan field metadata
        dokumen_unik = set()
        for meta in all_metadatas:
            file_name = meta.get("source") or meta.get("file") or meta.get("filename")
            if file_name:
                dokumen_unik.add(file_name)

        jumlah_dokumen = len(dokumen_unik)
        jumlah_chunk = len(all_chunks)
    except:
        jumlah_dokumen = 0
        jumlah_chunk = 0

# Tampilkan metrik utama
col1, col2, col3, col4 = st.columns(4)
col1.metric("📨 Jumlah Pertanyaan", jumlah_pertanyaan)
col2.metric("📚 Dokumen Terindeks", jumlah_dokumen)
col3.metric("📄 Jumlah Chunk", jumlah_chunk)
col4.metric("🧠 Jawaban Diberikan", jumlah_jawaban)

# Visualisasi distribusi feedback
st.subheader("Distribusi Feedback")
feedback_data = {
    "👍 Positif": feedback_counter.get("OK", 0),
    "👎 Negatif": feedback_counter.get("NOT_OK", 0)
}
st.bar_chart(feedback_data)

# Opsional: Tampilkan daftar nama dokumen
with st.expander("📂 Daftar Nama Dokumen"):
    if jumlah_dokumen > 0:
        for doc in sorted(dokumen_unik):
            st.markdown(f"- `{doc}`")
    else:
        st.info("Belum ada dokumen yang terindeks.")
