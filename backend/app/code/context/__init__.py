"""
Context module - Repository scanning, chunking, and retrieval.

Inspired by CodeFuse-CGM's graph-based context extraction.
"""

from .repo_scanner import RepoScanner, ScanResult
from .chunker import CodeChunker, CodeChunk
from .retriever import CodeRetriever, SearchResult
from .context_pack import ContextPacker, ContextPack

__all__ = [
    "RepoScanner", "ScanResult",
    "CodeChunker", "CodeChunk", 
    "CodeRetriever", "SearchResult",
    "ContextPacker", "ContextPack",
]
