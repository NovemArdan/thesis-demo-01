import os
import shutil
import json
from typing import List, Dict, Any, Optional
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.docstore.document import Document
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate


class RAGEngine:
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        use_in_memory: bool = False,
        openai_api_key: Optional[str] = None,
        reset_db: bool = False,
    ):
        self.use_in_memory = use_in_memory
        self.persist_directory = persist_directory if not use_in_memory else None
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.reset_db = reset_db

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=self.openai_api_key
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        self._initialize_vectorstore()

        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.2,
            openai_api_key=self.openai_api_key
        )

        self.template = """
        [INSTRUKSI]
        Anda adalah asisten knowledge management perkeretaapian Indonesia. Jawab pertanyaan pengguna berdasarkan konteks yang diberikan dengan akurat. Jika informasi tidak ada dalam konteks, katakan Anda tidak tahu.

        [KONTEKS]
        {context}

        [PERTANYAAN]
        {question}

        [JAWABAN]
        """
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self._initialize_qa_chain()

    def _initialize_vectorstore(self):
        if self.reset_db and self.persist_directory and os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)

        self.vectorstore = Chroma(
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def _initialize_qa_chain(self):
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": self.prompt},
            return_source_documents=True
        )

    def load_documents(self, directory: str) -> List[Document]:
        docs = []
        for root, _, files in os.walk(directory):
            for file in files:
                path = os.path.join(root, file)
                if file.endswith(".pdf"):
                    loader = PyPDFLoader(path)
                    pages = loader.load()
                    for i, page in enumerate(pages):
                        page.metadata["source_file"] = file
                        page.metadata["page"] = str(i + 1)
                    docs.extend(pages)
                elif file.endswith(".txt"):
                    loader = TextLoader(path, encoding="utf-8")
                    text_docs = loader.load()
                    for doc in text_docs:
                        doc.metadata["source_file"] = file
                        doc.metadata["page"] = "1"
                    docs.extend(text_docs)
        return docs

    def process_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.text_splitter.split_documents(documents)
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk"] = chunk.page_content[:100]
            chunk.metadata["page"] = chunk.metadata.get("page", "N/A")
            chunk.metadata["chunk_id"] = f"{chunk.metadata.get('source_file', 'unknown')}_{i}"
        return chunks

    def index_documents(self, documents: List[Document]) -> None:
        self.vectorstore.add_documents(documents)
        if not self.use_in_memory:
            self.vectorstore.persist()

    def load_and_index_documents(self, directory: str) -> int:
        docs = self.load_documents(directory)
        chunks = self.process_documents(docs)

        # Tambahkan metadata dari .meta.json jika ada
        for chunk in chunks:
            filename = chunk.metadata.get("source_file")
            meta_path = os.path.join(directory, filename + ".meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                chunk.metadata.update({
                    "upload_by": meta.get("upload_by", ""),
                    "upload_at": meta.get("upload_at", ""),
                    "jenis_dokumen": meta.get("jenis_dokumen", ""),
                    "deskripsi": meta.get("deskripsi", "")
                })

        self.index_documents(chunks)
        return len(chunks)

    def query(self, query: str) -> Dict[str, Any]:
        result = self.qa_chain({"query": query})
        formatted_sources = []
        for doc in result.get("source_documents", []):
            formatted_sources.append({
                "file": doc.metadata.get("source_file", "Unknown"),
                "page": doc.metadata.get("page", "N/A"),
                "chunk_id": doc.metadata.get("chunk_id", "-"),
                "chunk_preview": doc.metadata.get("chunk", "")[:100]
            })
        result["formatted_sources"] = formatted_sources
        return result

    def get_source_info(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        sources = []
        for doc in result.get("source_documents", []):
            sources.append({
                "source_file": doc.metadata.get("source_file", "Unknown"),
                "page": doc.metadata.get("page", "N/A"),
                "chunk_id": doc.metadata.get("chunk_id", "-"),
                "chunk": doc.metadata.get("chunk", "")[:100]
            })
        return sources

    def get_indexed_documents(self):
        return self.vectorstore.get()['documents']

    def list_indexed_files(self) -> List[str]:
        """Mengembalikan daftar nama file (source_file) yang telah diindeks ke vectorstore."""
        data = self.vectorstore.get()
        filenames = set()
        for meta in data.get("metadatas", []):
            if "source_file" in meta:
                filenames.add(meta["source_file"])
        return sorted(filenames)

    def delete_document(self, filename: str):
        try:
            self.vectorstore.delete(filter={"source_file": filename})
        except Exception as e:
            raise RuntimeError(f"Gagal menghapus dari vectorstore: {e}")
