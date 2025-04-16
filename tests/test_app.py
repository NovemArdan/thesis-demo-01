import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after path setup
from rag_engine import RAGEngine

class TestApp:
    """Basic tests for app functionality without running the actual Streamlit app."""
    
    @patch("rag_engine.ChatOpenAI")
    @patch("rag_engine.OpenAIEmbeddings")
    @patch("rag_engine.Chroma")
    def test_app_initialization(self, mock_chroma, mock_embeddings, mock_chat_openai):
        """Test app initialization components."""
        # Setup mocks
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore
        mock_vectorstore.as_retriever.return_value = MagicMock()
        
        # Initialize RAG engine
        engine = RAGEngine(use_in_memory=True)
        
        # Check if components are initialized
        assert mock_embeddings.called
        assert mock_chroma.called
        assert mock_chat_openai.called
        assert engine.qa_chain is not None
    
    @patch("rag_engine.ChatOpenAI")
    @patch("rag_engine.OpenAIEmbeddings")
    @patch("rag_engine.Chroma")
    def test_document_processing_flow(self, mock_chroma, mock_embeddings, mock_chat_openai):
        """Test the document processing flow."""
        # Setup mocks
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore
        
        # Initialize RAG engine
        engine = RAGEngine(use_in_memory=True)
        
        # Create a temporary test document
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(f"{temp_dir}/test.txt", "w") as f:
                f.write("This is a test document for railway knowledge management.")
            
            # Process documents
            num_chunks = engine.load_and_index_documents(temp_dir)
            
            # Check if documents were processed
            assert num_chunks > 0
            assert mock_vectorstore.add_documents.called