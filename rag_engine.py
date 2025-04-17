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
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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

    def _initialize_vectorstore(self):
        if self.reset_db and self.persist_directory and os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
            print(f"Database {self.persist_directory} direset")

        try:
            # Create the directory if it doesn't exist
            if self.persist_directory and not os.path.exists(self.persist_directory):
                os.makedirs(self.persist_directory)
                print(f"Created directory: {self.persist_directory}")
            
            # Initialize the vectorstore
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"Vectorstore initialized with persist_directory: {self.persist_directory}")
            
            # Try to check if documents exist
            try:
                collection = self.vectorstore._collection
                count = collection.count()
                print(f"Found {count} documents in vectorstore")
            except Exception as e:
                print(f"Could not get document count: {e}")
                
        except Exception as e:
            print(f"Error initializing vectorstore: {e}")
            raise

    def load_documents(self, path: str) -> List[Document]:
        """Load documents from a file or directory."""
        docs = []
        if os.path.isdir(path):
            # Process directory
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".meta.json"):  # Skip metadata files
                        continue
                    file_path = os.path.join(root, file)
                    loaded_docs = self._load_single_file(file_path)
                    docs.extend(loaded_docs)
        else:
            # Process single file
            loaded_docs = self._load_single_file(path)
            docs.extend(loaded_docs)
        
        print(f"Loaded {len(docs)} documents from {path}")
        return docs

    def _load_single_file(self, path: str) -> List[Document]:
        """Load a single file based on its extension."""
        if path.endswith(".pdf"):
            try:
                loader = PyPDFLoader(path)
                pages = loader.load()
                for i, page in enumerate(pages):
                    page.metadata["source_file"] = os.path.basename(path)
                    page.metadata["page"] = str(i + 1)
                print(f"Loaded PDF: {path} with {len(pages)} pages")
                return pages
            except Exception as e:
                print(f"Error loading PDF {path}: {e}")
                return []
                
        elif path.endswith(".txt"):
            try:
                loader = TextLoader(path, encoding="utf-8")
                text_docs = loader.load()
                for doc in text_docs:
                    doc.metadata["source_file"] = os.path.basename(path)
                    doc.metadata["page"] = "1"
                print(f"Loaded TXT: {path} with {len(text_docs)} documents")
                return text_docs
            except Exception as e:
                print(f"Error loading TXT {path}: {e}")
                return []
        else:
            print(f"Unsupported file format: {path}")
            return []

    def process_documents(self, documents: List[Document]) -> List[Document]:
        if not documents:
            print("No documents to process")
            return []
            
        chunks = self.text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk"] = chunk.page_content[:100]
            chunk.metadata["page"] = chunk.metadata.get("page", "N/A")
            chunk.metadata["chunk_id"] = f"{chunk.metadata.get('source_file', 'unknown')}_{i}"
            chunk.metadata["source_file"] = chunk.metadata.get("source_file", "unknown")
        
        if chunks:
            print(f"Sample chunk: {chunks[0].page_content[:50]}...")
        
        return chunks

    def index_documents(self, documents: List[Document]) -> None:
        if not documents:
            print("No documents to index")
            return
            
        print(f"Indexing {len(documents)} chunks")
        try:
            self.vectorstore.add_documents(documents)
            if not self.use_in_memory and self.persist_directory:
                self.vectorstore.persist()
                print("Vectorstore persisted to disk")
            print(f"Successfully indexed {len(documents)} chunks")
        except Exception as e:
            print(f"❌ Error during indexing: {e}")
            import traceback
            traceback.print_exc()

    def load_and_index_documents(self, directory: str) -> int:
        print(f"Loading documents from {directory}")
        docs = self.load_documents(directory)
        if not docs:
            print(f"No documents found in {directory}")
            return 0
            
        chunks = self.process_documents(docs)
        self.index_documents(chunks)
        print(f"Indexed {len(chunks)} chunks from {directory}")
        return len(chunks)

    def query(self, query: str, debug=False) -> Dict[str, Any]:
        if not query or len(query.strip()) == 0:
            print("❌ Pertanyaan kosong.")
            return {"result": "Pertanyaan kosong.", "formatted_sources": [], "debug": {"error": "empty_query"}}

        debug_info = {"query": query} if debug else {}
        
        try:
            # Check if collection has documents using the direct collection API
            try:
                collection = self.vectorstore._collection
                count = collection.count()
                if count == 0:
                    print("❌ Tidak ada dokumen di vectorstore.")
                    return {
                        "result": "Maaf, tidak ada dokumen yang tersedia untuk mencari jawaban. Silakan tambahkan dokumen terlebih dahulu.",
                        "formatted_sources": [],
                        "debug": {"error": "no_documents"}
                    }
                
                print(f"Found {count} documents in vectorstore for query")
                debug_info["document_count"] = count
                
            except Exception as e:
                print(f"❌ Error saat mengecek jumlah dokumen: {e}")
                # Continue anyway, let's try to query
            
            # Use the regular similarity search instead of direct vector manipulation
            docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=5)
            
            if not docs_and_scores:
                print("❌ Tidak ada dokumen yang relevan ditemukan.")
                return {
                    "result": "Maaf, tidak ditemukan dokumen yang relevan dengan pertanyaan Anda.",
                    "formatted_sources": [],
                    "debug": {"error": "no_relevant_docs"}
                }
            
            # Extract documents and scores
            documents = [doc for doc, _ in docs_and_scores]
            scores = [score for _, score in docs_and_scores]
            
            # Create context from documents
            context = "\n\n".join([doc.page_content for doc in documents])
            
            # Format prompt
            formatted_prompt = self.template.format(context=context, question=query)
            
            # Get answer from LLM
            print(f"Sending prompt to LLM with context from {len(documents)} documents")
            answer = self.llm.predict(formatted_prompt)
            
            # Format sources for return
            formatted_sources = [{
                "file": doc.metadata.get("source_file", "Unknown"),
                "page": doc.metadata.get("page", "N/A"),
                "chunk_id": doc.metadata.get("chunk_id", "-"),
                "chunk_preview": doc.page_content[:100] if doc.page_content else "",
                "score": round(float(score), 4)
            } for doc, score in docs_and_scores]
            
            return {
                "result": answer,
                "formatted_sources": formatted_sources,
                "debug": debug_info if debug else {}
            }
                
        except Exception as e:
            error_msg = f"❌ Error dalam proses query: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return {"result": error_msg, "formatted_sources": [], "debug": {"error": str(e)}}

    def list_indexed_files(self) -> Dict[str, int]:
        try:
            data = self.vectorstore.get()
            file_counts = {}
            for meta in data.get("metadatas", []):
                filename = meta.get("source_file")
                if filename:
                    file_counts[filename] = file_counts.get(filename, 0) + 1
            return dict(sorted(file_counts.items()))
        except Exception as e:
            print(f"Error listing indexed files: {e}")
            return {}

    def delete_document(self, filename: str):
        try:
            self.vectorstore.delete(filter={"source_file": filename})
            print(f"Deleted document: {filename}")
            if not self.use_in_memory and self.persist_directory:
                self.vectorstore.persist()
                print(f"Changes persisted after deleting: {filename}")
        except Exception as e:
            error_msg = f"Failed to remove from vectorstore: {e}"
            print(error_msg)
            raise RuntimeError(error_msg)