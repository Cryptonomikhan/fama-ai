import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from src.knowledge.factory import (
    initialize_embedder, 
    initialize_vector_db, 
    initialize_knowledge_base,
    initialize_chunking_strategy,
    EmbedderError,
    VectorDbError,
    KnowledgeSourceError,
    ChunkingStrategyError
)

# Mock classes and functions for testing
class MockEmbedder:
    def __init__(self, model=None, api_key=None, dimensions=None):
        self.model = model
        self.api_key = api_key
        self.dimensions = dimensions

class MockVectorDb:
    def __init__(self, embedder=None, **kwargs):
        self.embedder = embedder
        self.kwargs = kwargs

class MockKnowledgeBase:
    def __init__(self, vectordb=None, **kwargs):
        self.vectordb = vectordb
        self.kwargs = kwargs
        self.loaded = False
    
    def load(self):
        self.loaded = True
        return True

class MockChunkingStrategy:
    def __init__(self, chunk_size=None, overlap=None, **kwargs):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.kwargs = kwargs

# Fixtures
@pytest.fixture
def mock_environment():
    """Set up mock environment variables for testing"""
    original_environ = os.environ.copy()
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["COHERE_API_KEY"] = "test-cohere-key"
    yield
    os.environ.clear()
    os.environ.update(original_environ)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

# Tests for initialize_embedder
@patch("src.knowledge.factory.EMBEDDERS", {"openai": MockEmbedder, "cohere": MockEmbedder, "local": MockEmbedder})
def test_initialize_embedder_openai():
    """Test initializing an OpenAI embedder"""
    embedder = initialize_embedder(
        provider="openai",
        model="text-embedding-3-small",
        api_key="test-key"
    )
    
    assert embedder is not None
    assert embedder.model == "text-embedding-3-small"
    assert embedder.api_key == "test-key"

@patch("src.knowledge.factory.EMBEDDERS", {"openai": MockEmbedder, "cohere": MockEmbedder, "local": MockEmbedder})
def test_initialize_embedder_missing_api_key():
    """Test initializing an embedder with missing API key"""
    with pytest.raises(EmbedderError) as excinfo:
        initialize_embedder(
            provider="openai",
            model="text-embedding-3-small",
            api_key=None
        )
    
    assert "API key is required" in str(excinfo.value)

@patch("src.knowledge.factory.EMBEDDERS", {"openai": MockEmbedder, "cohere": MockEmbedder, "local": MockEmbedder})
def test_initialize_embedder_local_missing_dimensions():
    """Test initializing a local embedder without dimensions"""
    with pytest.raises(EmbedderError) as excinfo:
        initialize_embedder(
            provider="local",
            model="all-MiniLM-L6-v2",
            api_key=None,
            dimensions=None
        )
    
    assert "Dimensions parameter is required" in str(excinfo.value)

@patch("src.knowledge.factory.EMBEDDERS", {"openai": MockEmbedder, "cohere": MockEmbedder, "local": MockEmbedder})
def test_initialize_embedder_unsupported_provider():
    """Test initializing an embedder with an unsupported provider"""
    with pytest.raises(EmbedderError) as excinfo:
        initialize_embedder(
            provider="unsupported",
            model="text-embedding-3-small",
            api_key="test-key"
        )
    
    assert "Unsupported embedder provider" in str(excinfo.value)

# Tests for initialize_vector_db
@patch("src.knowledge.factory.initialize_lancedb", return_value=MockVectorDb())
def test_initialize_vector_db_lancedb(mock_init_lancedb):
    """Test initializing a LanceDB vector database"""
    embedder = MockEmbedder(model="text-embedding-3-small", api_key="test-key")
    
    vector_db = initialize_vector_db(
        vector_db_type="lancedb",
        embedder=embedder
    )
    
    assert vector_db is not None
    assert mock_init_lancedb.called

@patch("src.knowledge.factory.initialize_lancedb", side_effect=Exception("Test error"))
def test_initialize_vector_db_error(mock_init_lancedb):
    """Test error handling when initializing a vector database"""
    embedder = MockEmbedder(model="text-embedding-3-small", api_key="test-key")
    
    with pytest.raises(VectorDbError) as excinfo:
        initialize_vector_db(
            vector_db_type="lancedb",
            embedder=embedder
        )
    
    assert "Failed to initialize lancedb vector database" in str(excinfo.value)

def test_initialize_vector_db_unsupported():
    """Test initializing an unsupported vector database type"""
    embedder = MockEmbedder(model="text-embedding-3-small", api_key="test-key")
    
    with pytest.raises(VectorDbError) as excinfo:
        initialize_vector_db(
            vector_db_type="unsupported",
            embedder=embedder
        )
    
    assert "Unsupported vector database type" in str(excinfo.value)

# Tests for initialize_chunking_strategy
@patch("src.knowledge.factory.CHUNKING_STRATEGIES", {
    "fixed": MockChunkingStrategy,
    "agentic": MockChunkingStrategy,
    "semantic": MockChunkingStrategy,
    "recursive": MockChunkingStrategy,
    "document": MockChunkingStrategy
})
def test_initialize_chunking_strategy_fixed():
    """Test initializing a fixed chunking strategy"""
    chunking = initialize_chunking_strategy(
        strategy_name="fixed",
        chunk_size=5000,
        chunk_overlap=0
    )
    
    assert chunking is not None
    assert chunking.chunk_size == 5000
    assert chunking.overlap == 0

@patch("src.knowledge.factory.CHUNKING_STRATEGIES", {
    "fixed": MockChunkingStrategy,
    "agentic": MockChunkingStrategy,
    "semantic": MockChunkingStrategy,
    "recursive": MockChunkingStrategy,
    "document": MockChunkingStrategy
})
def test_initialize_chunking_strategy_semantic_missing_embedder():
    """Test initializing a semantic chunking strategy without an embedder"""
    with pytest.raises(ChunkingStrategyError) as excinfo:
        initialize_chunking_strategy(
            strategy_name="semantic",
            chunk_size=5000,
            chunk_overlap=0,
            similarity_threshold=0.5,
            embedder=None
        )
    
    assert "Embedder is required for semantic chunking" in str(excinfo.value)

@patch("src.knowledge.factory.CHUNKING_STRATEGIES", {
    "fixed": MockChunkingStrategy,
    "agentic": MockChunkingStrategy,
    "semantic": MockChunkingStrategy,
    "recursive": MockChunkingStrategy,
    "document": MockChunkingStrategy
})
def test_initialize_chunking_strategy_unsupported():
    """Test initializing an unsupported chunking strategy"""
    with pytest.raises(ChunkingStrategyError) as excinfo:
        initialize_chunking_strategy(
            strategy_name="unsupported",
            chunk_size=5000,
            chunk_overlap=0
        )
    
    assert "Unknown chunking strategy" in str(excinfo.value)

# Tests for initialize_knowledge_base
@patch("src.knowledge.factory.initialize_embedder")
@patch("src.knowledge.factory.initialize_vector_db")
@patch("src.knowledge.factory.initialize_chunking_strategy")
@patch("src.knowledge.factory.KNOWLEDGE_SOURCES", {"text": MockKnowledgeBase})
def test_initialize_knowledge_base_text(
    mock_init_chunking, mock_init_vector_db, mock_init_embedder
):
    """Test initializing a knowledge base with text"""
    mock_embedder = MockEmbedder(model="text-embedding-3-small", api_key="test-key")
    mock_vector_db = MockVectorDb(embedder=mock_embedder)
    mock_chunking = MockChunkingStrategy(chunk_size=5000, overlap=0)
    
    mock_init_embedder.return_value = mock_embedder
    mock_init_vector_db.return_value = mock_vector_db
    mock_init_chunking.return_value = mock_chunking
    
    kb = initialize_knowledge_base(
        knowledge_text="Test knowledge text",
        vector_db_type="lancedb",
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        provider_api_key="test-key",
        knowledge_source_type="text"
    )
    
    assert kb is not None
    assert mock_init_embedder.called
    assert mock_init_vector_db.called
    assert mock_init_chunking.called

@patch("src.knowledge.factory.initialize_embedder")
@patch("src.knowledge.factory.initialize_vector_db")
def test_initialize_knowledge_base_no_sources(mock_init_vector_db, mock_init_embedder):
    """Test initializing a knowledge base with no sources"""
    kb = initialize_knowledge_base(
        knowledge_urls=None,
        knowledge_text=None,
        vector_db_type="lancedb",
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        provider_api_key="test-key"
    )
    
    assert kb is None
    assert not mock_init_embedder.called
    assert not mock_init_vector_db.called

@patch("src.knowledge.factory.initialize_embedder", side_effect=EmbedderError("Test error"))
def test_initialize_knowledge_base_embedder_error(mock_init_embedder):
    """Test error handling when initializing an embedder in knowledge base creation"""
    with pytest.raises(EmbedderError) as excinfo:
        initialize_knowledge_base(
            knowledge_text="Test knowledge text",
            vector_db_type="lancedb",
            embedder_provider="openai",
            embedder_model="text-embedding-3-small",
            provider_api_key="test-key"
        )
    
    assert "Test error" in str(excinfo.value)
    assert mock_init_embedder.called

@patch("src.knowledge.factory.initialize_embedder")
@patch("src.knowledge.factory.initialize_vector_db", side_effect=VectorDbError("Test error"))
def test_initialize_knowledge_base_vector_db_error(mock_init_vector_db, mock_init_embedder):
    """Test error handling when initializing a vector database in knowledge base creation"""
    mock_embedder = MockEmbedder(model="text-embedding-3-small", api_key="test-key")
    mock_init_embedder.return_value = mock_embedder
    
    with pytest.raises(VectorDbError) as excinfo:
        initialize_knowledge_base(
            knowledge_text="Test knowledge text",
            vector_db_type="lancedb",
            embedder_provider="openai",
            embedder_model="text-embedding-3-small",
            provider_api_key="test-key"
        )
    
    assert "Test error" in str(excinfo.value)
    assert mock_init_embedder.called
    assert mock_init_vector_db.called

@patch("src.knowledge.factory.initialize_embedder")
@patch("src.knowledge.factory.initialize_vector_db")
@patch("src.knowledge.factory.initialize_chunking_strategy", side_effect=ChunkingStrategyError("Test error"))
def test_initialize_knowledge_base_chunking_error(
    mock_init_chunking, mock_init_vector_db, mock_init_embedder
):
    """Test error handling when initializing a chunking strategy in knowledge base creation"""
    mock_embedder = MockEmbedder(model="text-embedding-3-small", api_key="test-key")
    mock_vector_db = MockVectorDb(embedder=mock_embedder)
    
    mock_init_embedder.return_value = mock_embedder
    mock_init_vector_db.return_value = mock_vector_db
    
    with pytest.raises(ChunkingStrategyError) as excinfo:
        initialize_knowledge_base(
            knowledge_text="Test knowledge text",
            vector_db_type="lancedb",
            embedder_provider="openai",
            embedder_model="text-embedding-3-small",
            provider_api_key="test-key"
        )
    
    assert "Test error" in str(excinfo.value)
    assert mock_init_embedder.called
    assert mock_init_vector_db.called
    assert mock_init_chunking.called 