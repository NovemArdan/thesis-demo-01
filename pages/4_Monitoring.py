import streamlit as st
import os
import json
from collections import Counter
from langchain.docstore.document import Document

st.set_page_config(page_title="Monitoring Sistem", layout="wide")
st.title("\U0001F4CA Monitoring Sistem Chatbot KMS")

# Cek login dan role admin
if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
    st.error("Halaman ini hanya dapat diakses oleh admin.")
    st.stop()

LOG_FOLDER = "chat_logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

jumlah_pertanyaan = 0
jumlah_jawaban = 0
jumlah_dokumen = 0
jumlah_chunk = 0
feedback_counter = Counter()
chat_negatif = []

# Ambil data dari log
for filename in os.listdir(LOG_FOLDER):
    if filename.endswith(".json"):
        filepath = os.path.join(LOG_FOLDER, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for i, item in enumerate(data):
                    if item.get("role") == "user":
                        jumlah_pertanyaan += 1
                    elif item.get("role") == "assistant":
                        jumlah_jawaban += 1
                        if item.get("feedback"):
                            feedback_counter[item.get("feedback")] += 1
                            if item.get("feedback") == "NOT_OK":
                                previous = data[i - 1] if i > 0 and data[i - 1]["role"] == "user" else {"content": "(tidak ditemukan)"}
                                chat_negatif.append({
                                    "file": filename,
                                    "timestamp": item.get("timestamp", "-"),
                                    "pertanyaan": previous["content"],
                                    "jawaban": item.get("content"),
                                    "sources": item.get("sources", [])
                                })
        except Exception as e:
            st.warning(f"Gagal membaca {filename}: {e}")

# Ambil jumlah dokumen dari RAG
rag = st.session_state.get("rag_engine")
if rag:
    try:
        vs_data = rag.vectorstore.get()
        all_chunks = vs_data.get("documents", [])
        all_metadatas = vs_data.get("metadatas", [])
        dokumen_unik = {meta.get("source") or meta.get("file") or meta.get("filename") for meta in all_metadatas if meta}
        jumlah_dokumen = len(dokumen_unik)
        jumlah_chunk = len(all_chunks)
    except:
        jumlah_dokumen = 0
        jumlah_chunk = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("\U0001F4E8 Jumlah Pertanyaan", jumlah_pertanyaan)
col2.metric("\U0001F4DA Dokumen Terindeks", jumlah_dokumen)
col3.metric("\U0001F4C4 Jumlah Chunk", jumlah_chunk)
col4.metric("\U0001F9E0 Jawaban Diberikan", jumlah_jawaban)

st.subheader("Distribusi Feedback")
feedback_data = {
    "\U0001F44D Positif": feedback_counter.get("OK", 0),
    "\U0001F44E Negatif": feedback_counter.get("NOT_OK", 0)
}
clicked = st.radio("Klik untuk melihat detail:", list(feedback_data.keys()), horizontal=True, label_visibility="collapsed")
st.bar_chart(feedback_data)

if clicked == "\U0001F44E Negatif" and chat_negatif:
    st.markdown("### ❌ Daftar Chat dengan Feedback Negatif")
    for i, chat in enumerate(chat_negatif, 1):
        with st.expander(f"❌ Feedback Negatif #{i} – {chat['timestamp']} – file: `{chat['file']}`"):
            st.markdown(f"**❓ Pertanyaan**:\n{chat['pertanyaan']}")
            st.markdown(f"**💬 Jawaban**:\n{chat['jawaban']}")
            for j, source in enumerate(chat.get("sources", [])):
                chunk_id = source.get("chunk_id", f"chunk_{j}")
                st.markdown(f"\n📄 **Chunk {j+1}:**")
                st.markdown(f"- **File**: `{source.get('file', '-')}`")
                st.markdown(f"- **Halaman**: `{source.get('page', '-')}`")
                st.markdown(f"- **Chunk ID**: `{chunk_id}`")
                st.markdown(f"- **Skor**: `{source.get('score', '-')}`")

                # Ambil isi lengkap chunk dari vectorstore
                chunk_full_text = ""
                try:
                    all_data = rag.vectorstore.get()
                    for content, meta in zip(all_data["documents"], all_data["metadatas"]):
                        if meta.get("chunk_id") == chunk_id:
                            chunk_full_text = content
                            break
                except Exception as e:
                    st.warning(f"Gagal mengambil isi chunk lengkap: {e}")

                default_text = chunk_full_text or source.get("chunk_preview", "")
                revised = st.text_area(f"✏️ Revisi Chunk {j+1}", value=default_text, key=f"revisi_{chunk_id}_{i}_{j}")

                if st.button(f"💾 Simpan Revisi Chunk {j+1}", key=f"simpan_{chunk_id}_{i}_{j}"):
                    try:
                        doc = Document(
                            page_content=revised,
                            metadata={
                                "chunk_id": chunk_id,
                                "source_file": source.get("file", "unknown"),
                                "page": source.get("page", "N/A"),
                                "chunk": revised[:100]
                            }
                        )
                        # rag.vectorstore.delete(filter={"chunk_id": chunk_id})

                        # Cari dan hapus berdasarkan chunk_id
                        all_data = rag.vectorstore.get()
                        delete_ids = []
                        for idx, meta in enumerate(all_data["metadatas"]):
                            if meta.get("chunk_id") == chunk_id:
                                delete_ids.append(all_data["ids"][idx])
                        if delete_ids:
                            rag.vectorstore.delete(ids=delete_ids)


                        rag.vectorstore.add_documents([doc])
                        rag.vectorstore.persist()
                        st.success("✅ Chunk berhasil diperbarui.")
                    except Exception as e:
                        st.error(f"❌ Gagal memperbarui chunk: {e}")

elif clicked == "\U0001F44E Negatif":
    st.info("Tidak ada jawaban yang mendapat feedback negatif.")

# Tampilkan daftar dokumen
with st.expander("\U0001F4C2 Daftar Nama Dokumen"):
    if jumlah_dokumen > 0:
        for doc in sorted(dokumen_unik):
            st.markdown(f"- `{doc}`")
    else:
        st.info("Belum ada dokumen yang terindeks.")