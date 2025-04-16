import os
import re
import shutil
from typing import List, Dict, Any, Optional
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
from langchain.docstore.document import Document
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate


class RAGEngine:
    """Retrieval Augmented Generation engine for railway knowledge management."""

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
        if self.use_in_memory:
            self.vectorstore = Chroma(embedding_function=self.embeddings)
        else:
            if self.reset_db and os.path.exists(self.persist_directory):
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
        """Load PDF or TXT documents, then extract per Pasal for PDF."""
        docs: List[Document] = []
        for root, _, files in os.walk(directory):
            for file in files:
                path = os.path.join(root, file)
                if file.endswith(".pdf"):
                    loader = PyPDFLoader(path)
                    raw_pages = loader.load()
                    full_text = "\n".join([p.page_content for p in raw_pages])
                    pasal_docs = self._split_by_pasal(full_text, file)
                    docs.extend(pasal_docs)
                elif file.endswith(".txt"):
                    loader = TextLoader(path, encoding="utf-8")
                    loaded = loader.load()
                    for doc in loaded:
                        doc.metadata["source_file"] = file
                        doc.metadata["page"] = "1"
                    docs.extend(loaded)
        return docs

    def _split_by_pasal(self, text: str, filename: str) -> List[Document]:
        """Pisahkan dokumen berdasarkan 'Pasal X' untuk legal documents."""
        pasal_blocks = re.split(r"(?=Pasal\s+\d+)", text, flags=re.IGNORECASE)
        docs = []
        for block in pasal_blocks:
            match = re.match(r"Pasal\s+(\d+)", block)
            if match:
                pasal_number = match.group(1)
                doc = Document(
                    page_content=block.strip(),
                    metadata={
                        "source_file": filename,
                        "page": f"Pasal {pasal_number}",
                        "pasal_number": pasal_number
                    }
                )
                docs.append(doc)
        return docs

    def process_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.text_splitter.split_documents(documents)
        for chunk in chunks:
            chunk.metadata["chunk"] = chunk.page_content[:100]
            if "page" not in chunk.metadata:
                chunk.metadata["page"] = "N/A"
        return chunks

    def index_documents(self, documents: List[Document]) -> None:
        self.vectorstore.add_documents(documents)
        if not self.use_in_memory:
            self.vectorstore.persist()

    def load_and_index_documents(self, directory: str) -> int:
        docs = self.load_documents(directory)
        chunks = self.process_documents(docs)
        self.index_documents(chunks)
        return len(chunks)

    def query(self, query: str) -> Dict[str, Any]:
        result = self.qa_chain({"query": query})
        formatted_sources = []
        for doc in result.get("source_documents", []):
            source_info = {
                "file": doc.metadata.get("source_file", "Unknown"),
                "page": doc.metadata.get("page", "N/A"),
                "pasal": doc.metadata.get("pasal_number", "-"),
                "chunk_preview": doc.metadata.get("chunk", "")[:100]
            }
            formatted_sources.append(source_info)
        result["formatted_sources"] = formatted_sources
        return result

    def get_source_info(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        sources = []
        for doc in result.get("source_documents", []):
            source = {
                "source_file": doc.metadata.get("source_file", "Unknown"),
                "page": doc.metadata.get("page", "N/A"),
                "pasal": doc.metadata.get("pasal_number", "-"),
                "chunk": doc.metadata.get("chunk", "")[:100]
            }
            sources.append(source)
        return sources

    def get_indexed_documents(self):
        return self.retriever.vectorstore.get()['documents']
