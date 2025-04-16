import os
import pytest
import tempfile
from langchain.docstore.document import Document
from rag_engine import RAGEngine

# Skip tests if no OpenAI API key
if not os.environ.get("OPENAI_API_KEY"):
    pytest.skip("No OpenAI API key found", allow_module_level=True)

class TestRAGEngine:
    
    @pytest.fixture
    def rag_engine(self):
        """Create RAG engine for testing."""
        return RAGEngine(use_in_memory=True)
    
    @pytest.fixture
    def test_documents(self):
        """Create test documents."""
        return [
            Document(
                page_content="Kereta api adalah sarana transportasi berupa kendaraan dengan tenaga gerak yang berjalan di rel.",
                metadata={"source": "test_doc_1.txt"}
            ),
            Document(
                page_content="Pemeliharaan rel kereta api harus dilakukan secara berkala untuk memastikan keamanan perjalanan.",
                metadata={"source": "test_doc_2.txt"}
            ),
            Document(
                page_content="Sinyal kereta api adalah perangkat yang digunakan untuk mengatur lalu lintas perjalanan kereta api.",
                metadata={"source": "test_doc_3.txt"}
            )
        ]
    
    def test_init(self, rag_engine):
        """Test initialization of RAG engine."""
        assert rag_engine is not None
    
    def test_process_documents(self, rag_engine, test_documents):
        """Test document processing."""
        chunks = rag_engine.process_documents(test_documents)
        assert len(chunks) == len(test_documents)  # No splitting for small documents
    
    def test_index_documents(self, rag_engine, test_documents):
        """Test document indexing."""
        rag_engine.index_documents(test_documents)
        # Hard to test directly, but shouldn't throw errors
    
    def test_load_documents(self, rag_engine):
        """Test document loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test document
            with open(f"{temp_dir}/test.txt", "w") as f:
                f.write("This is a test document for railway knowledge management.")
            
            # Load documents
            documents = rag_engine.load_documents(temp_dir)
            assert len(documents) == 1
    
    def test_query_empty_db(self, rag_engine):
        """Test querying with empty vector database."""
        result = rag_engine.query("Apa itu kereta api?")
        assert "result" in result