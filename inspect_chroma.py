import argparse
from dotenv import load_dotenv
load_dotenv()

from rag_engine import RAGEngine

def list_documents(rag: RAGEngine):
    docs = rag.list_indexed_files()
    if docs:
        print(f"📚 {len(docs)} dokumen terindeks:")
        for i, d in enumerate(docs, 1):
            print(f"{i}. {d}")
    else:
        print("❌ Tidak ada dokumen yang terindeks.")

def delete_document(rag: RAGEngine, filename: str):
    try:
        rag.delete_document(filename)
        print(f"✅ Dokumen '{filename}' berhasil dihapus dari vectorstore.")
    except Exception as e:
        print(f"❌ Gagal menghapus dokumen: {e}")

def main():
    parser = argparse.ArgumentParser(description="CLI untuk mengelola Chroma vectorstore")
    parser.add_argument("--list", action="store_true", help="Lihat semua dokumen yang terindeks")
    parser.add_argument("--delete", type=str, help="Hapus dokumen dari vectorstore berdasarkan nama file")
    parser.add_argument("--reset", action="store_true", help="Reset chroma_db dan hapus semua isi")
    args = parser.parse_args()

    if args.reset:
        print("⚠️ Menghapus seluruh isi chroma_db...")
        rag = RAGEngine(reset_db=True)
        print("✅ chroma_db telah direset.")
        return

    # Inisialisasi tanpa reset
    rag = RAGEngine(reset_db=False)

    if args.list:
        list_documents(rag)

    if args.delete:
        delete_document(rag, args.delete)

if __name__ == "__main__":
    main()
