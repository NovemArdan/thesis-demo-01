import streamlit as st
from datetime import datetime
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_precision,
    context_recall,
)
from ragas import evaluate

# Cek admin login
st.set_page_config(page_title="Evaluasi Chatbot", layout="wide")
st.title("📏 Evaluasi Jawaban Chatbot dengan RAGAS")

if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
    st.error("Halaman ini hanya dapat diakses oleh admin.")
    st.stop()

# Input manual
with st.form("form_evaluasi"):
    pertanyaan = st.text_area("❓ Pertanyaan", height=80)
    jawaban_harusnya = st.text_area("✅ Jawaban Seharusnya", height=80)
    konteks_harusnya = st.text_area("📚 Konteks yang Relevan", height=120)
    submit_manual = st.form_submit_button("Lakukan Chat dan Evaluasi")

# Proses Chat dan Evaluasi jika diklik
if submit_manual:
    rag = st.session_state.get("rag_engine")
    if not rag:
        st.error("RAG Engine tidak tersedia di session state.")
        st.stop()

    with st.spinner("🤖 Mengambil jawaban dari chatbot..."):
        result = rag.query(pertanyaan, debug=True)
        jawaban_model = result.get("result", "(Tidak ada jawaban)")
        sumber = result.get("formatted_sources", [])
        konteks_diambil = [s.get("chunk_preview", "") for s in sumber]

    # Tampilkan hasil
    st.subheader("💬 Jawaban dari Chatbot")
    st.write(jawaban_model)

    st.subheader("📖 Konteks yang Diambil")
    for i, ctx in enumerate(konteks_diambil):
        st.markdown(f"**{i+1}.** {ctx}")

    # Siapkan sample untuk evaluasi RAGAS
    sample = RetrievalSample(
        question=pertanyaan,
        answer=jawaban_model,
        contexts=konteks_diambil,
        ground_truths=[jawaban_harusnya]
    )

    # Evaluasi
    with st.spinner("🔍 Mengevaluasi dengan RAGAS..."):
        result: EvaluationResult = evaluate(
            [sample],
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
        )
        scores = result.to_pandas().iloc[0]

    st.subheader("📊 Skor Evaluasi (RAGAS)")
    col1, col2 = st.columns(2)
    col1.metric("✅ Faithfulness", f"{scores['faithfulness']:.3f}")
    col1.metric("✅ Answer Relevancy", f"{scores['answer_relevancy']:.3f}")
    col2.metric("📚 Context Precision", f"{scores['context_precision']:.3f}")
    col2.metric("📚 Context Recall", f"{scores['context_recall']:.3f}")

    # Optional: tampilkan dict full jika mau debug
    with st.expander("🔍 Lihat Detail JSON Output"):
        st.json(result.to_dict())
