# context_refiner.py

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage

def refine_question_with_history(history: list, new_question: str, model_name="gpt-3.5-turbo", temperature=0.2) -> str:
    """
    Mengubah pertanyaan pengguna menjadi pertanyaan lengkap berdasarkan konteks chat sebelumnya.
    
    Args:
        history (list): Riwayat chat berupa list of dict (role, content).
        new_question (str): Pertanyaan terbaru dari pengguna.
        model_name (str): Nama model LLM yang digunakan.
        temperature (float): Temperatur kreativitas LLM.

    Returns:
        str: Pertanyaan yang telah diperjelas konteksnya.
    """
    messages = []

    # Gunakan hanya 3 interaksi terakhir (6 pesan: 3 user + 3 assistant)
    for msg in history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=f"""
Berikut ini adalah bagian akhir dari percakapan. Pengguna baru saja bertanya: '{new_question}'.
Tolong ubah pertanyaan ini menjadi versi lengkap yang lebih jelas berdasarkan konteks sebelumnya.
Jangan tambahkan penjelasan tambahan. Jika pertanyaan baru oleh pengguna di luar konteks percakapan sebelumnya, maka kembalikan ulang pertanyaan pengguna. Hanya berikan satu kalimat pertanyaan lengkap saja sebagai output.
"""))

    llm = ChatOpenAI(model_name=model_name, temperature=temperature)
    response = llm(messages)
    return response.content.strip()
