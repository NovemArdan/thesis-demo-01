import streamlit as st
from datetime import datetime
import hashlib
from sklearn.metrics import precision_score, recall_score, f1_score

st.set_page_config(page_title="Evaluasi Chatbot", layout="wide")
st.title("🧪 Evaluasi Manual Jawaban Chatbot")

# Cek akses admin
if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
    st.error("Halaman ini hanya dapat diakses oleh admin.")
    st.stop()

# Form input evaluasi manual
with st.form("eval_form"):
    st.subheader("1. Data Uji")
    test_question = st.text_input("Pertanyaan")
    expected_context = st.text_area("Konten Seharusnya (berisi informasi relevan)")
    expected_answer = st.text_area("Jawaban Seharusnya")

    submitted = st.form_submit_button("🔍 Evaluasi Jawaban Chatbot")

if submitted:
    with st.spinner("Mengeksekusi query ke RAG engine..."):
        try:
            rag = st.session_state.get("rag_engine")
            if not rag:
                raise ValueError("RAG Engine tidak tersedia")

            result = rag.query(test_question, debug=True)
            generated_context = "\n".join([s.get("chunk_preview", "") for s in result.get("formatted_sources", [])])
            generated_answer = result.get("result", "Tidak ada jawaban.")

            # Tampilkan hasil aktual dari sistem
            st.subheader("2. Hasil Sistem")
            st.markdown("**Konten yang Digunakan:**")
            st.code(generated_context)

            st.markdown("**Jawaban yang Dihasilkan:**")
            st.write(generated_answer)

            # Evaluasi sederhana: Precision/Recall/F1 berdasarkan token overlap (manual)
            from sklearn.feature_extraction.text import CountVectorizer
            from sklearn.metrics import f1_score
            import numpy as np

            def text_to_binary_vector(text, vocabulary):
                vec = CountVectorizer(vocabulary=vocabulary, binary=True)
                return vec.fit_transform([text]).toarray()[0]

            vocab = list(set(expected_answer.lower().split() + generated_answer.lower().split()))
            y_true = text_to_binary_vector(expected_answer, vocab)
            y_pred = text_to_binary_vector(generated_answer, vocab)

            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            st.subheader("3. Evaluasi")
            st.metric("🎯 Precision", f"{precision:.2f}")
            st.metric("🔁 Recall", f"{recall:.2f}")
            st.metric("🏅 F1-Score", f"{f1:.2f}")

            # Simpan ke log evaluasi (opsional, bisa dimodifikasi jika ingin ke file)
            st.session_state.last_evaluation = {
                "timestamp": datetime.now().isoformat(),
                "question": test_question,
                "expected_context": expected_context,
                "expected_answer": expected_answer,
                "generated_context": generated_context,
                "generated_answer": generated_answer,
                "precision": precision,
                "recall": recall,
                "f1": f1
            }

        except Exception as e:
            st.error(f"Terjadi kesalahan saat evaluasi: {e}")
