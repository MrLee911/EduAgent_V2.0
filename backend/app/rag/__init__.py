# RAG 模块汇总导出
# 对应文档：S2, 05 §3.2

from .parsers import parse_file, PARSER_MAP
from .chunker import chunk_documents, CHUNK_CONFIG
from .embeddings import get_embedding_model, embed_query, embed_documents, get_embedding_dimension
from .vector_store import (
    get_chroma_client,
    get_collection_name,
    get_or_create_collection,
    delete_collection,
    delete_chunks_by_ids,
    COLLECTION_PREFIX,
)
from .indexer import index_chunks
from .retriever import Retriever
from .query_rewriter import rewrite_query
from .reranker import rerank_with_bge, RERANK_THRESHOLD
from .post_processor import (
    format_knowledge_for_prompt,
    format_sources_for_db,
    format_results_for_tool,
    MAX_SOURCES,
    MAX_SOURCE_CHARS,
    MAX_TOTAL_TOKENS,
)
from .degradation import execute_with_degradation, DegradationLevel

__all__ = [
    # Parsers
    "parse_file",
    "PARSER_MAP",
    # Chunker
    "chunk_documents",
    "CHUNK_CONFIG",
    # Embeddings
    "get_embedding_model",
    "embed_query",
    "embed_documents",
    "get_embedding_dimension",
    # Vector Store
    "get_chroma_client",
    "get_collection_name",
    "get_or_create_collection",
    "delete_collection",
    "delete_chunks_by_ids",
    "COLLECTION_PREFIX",
    # Indexer
    "index_chunks",
    # Retriever
    "Retriever",
    # Query Rewriter
    "rewrite_query",
    # Reranker
    "rerank_with_bge",
    "RERANK_THRESHOLD",
    # Post Processor
    "format_knowledge_for_prompt",
    "format_sources_for_db",
    "format_results_for_tool",
    "MAX_SOURCES",
    "MAX_SOURCE_CHARS",
    "MAX_TOTAL_TOKENS",
    # Degradation
    "execute_with_degradation",
    "DegradationLevel",
]
