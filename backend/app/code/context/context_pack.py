"""
Context Packer - Packs retrieved chunks into prompt-ready context.

Inspired by CodeFuse-CGM's subgraph serialization.
Handles deduplication, ordering, and token budget management.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .chunker import CodeChunk
from .retriever import SearchResult

logger = logging.getLogger(__name__)

# Default token budget for context
DEFAULT_TOKEN_BUDGET = 8000


@dataclass
class ContextPack:
    """A packed context ready for prompting."""
    chunks: List[CodeChunk]
    total_tokens: int
    file_count: int
    chunk_count: int
    truncated: bool  # Whether some chunks were dropped due to budget
    citations: List[Dict[str, Any]]  # File references for attribution
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "total_tokens": self.total_tokens,
            "file_count": self.file_count,
            "chunk_count": self.chunk_count,
            "truncated": self.truncated,
            "citations": self.citations,
        }
    
    def to_prompt_string(self, include_line_numbers: bool = True) -> str:
        """
        Convert to a string suitable for LLM prompts.
        
        Args:
            include_line_numbers: Whether to include line number annotations
            
        Returns:
            Formatted string with all chunks
        """
        parts = []
        
        for chunk in self.chunks:
            header = f"### File: {chunk.file_path}"
            if chunk.name:
                header += f" | {chunk.chunk_type}: {chunk.name}"
            if include_line_numbers:
                header += f" (lines {chunk.start_line}-{chunk.end_line})"
            
            parts.append(header)
            parts.append(f"```{chunk.language}")
            parts.append(chunk.content)
            parts.append("```")
            parts.append("")
        
        return "\n".join(parts)


class ContextPacker:
    """
    Packs chunks into prompt-ready context with budget management.
    
    Features:
    - Token budget enforcement
    - Deduplication
    - Priority-based selection
    - Citation generation
    """
    
    def __init__(self, token_budget: int = DEFAULT_TOKEN_BUDGET):
        """
        Initialize packer.
        
        Args:
            token_budget: Maximum tokens to include
        """
        self.token_budget = token_budget
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation."""
        return len(text) // 4
    
    def pack_search_results(
        self,
        results: List[SearchResult],
        max_chunks: Optional[int] = None,
    ) -> ContextPack:
        """
        Pack search results into context.
        
        Args:
            results: Search results sorted by relevance
            max_chunks: Optional maximum number of chunks
            
        Returns:
            ContextPack with selected chunks
        """
        chunks = [r.chunk for r in results]
        return self.pack_chunks(chunks, max_chunks)
    
    def pack_chunks(
        self,
        chunks: List[CodeChunk],
        max_chunks: Optional[int] = None,
    ) -> ContextPack:
        """
        Pack chunks into context with budget management.
        
        Args:
            chunks: Chunks to pack (assumed pre-sorted by priority)
            max_chunks: Optional maximum number of chunks
            
        Returns:
            ContextPack with selected chunks
        """
        selected_chunks = []
        seen_ids = set()
        total_tokens = 0
        truncated = False
        files = set()
        
        for chunk in chunks:
            # Deduplication
            if chunk.id in seen_ids:
                continue
            
            # Check max chunks
            if max_chunks and len(selected_chunks) >= max_chunks:
                truncated = True
                break
            
            # Estimate tokens for this chunk (including formatting overhead)
            chunk_tokens = chunk.tokens_estimate + 50  # Header overhead
            
            # Check budget
            if total_tokens + chunk_tokens > self.token_budget:
                truncated = True
                continue  # Try smaller chunks
            
            selected_chunks.append(chunk)
            seen_ids.add(chunk.id)
            total_tokens += chunk_tokens
            files.add(chunk.file_path)
        
        # Generate citations
        citations = self._generate_citations(selected_chunks)
        
        return ContextPack(
            chunks=selected_chunks,
            total_tokens=total_tokens,
            file_count=len(files),
            chunk_count=len(selected_chunks),
            truncated=truncated,
            citations=citations,
        )
    
    def _generate_citations(self, chunks: List[CodeChunk]) -> List[Dict[str, Any]]:
        """Generate citation list for attribution."""
        file_chunks: Dict[str, List[CodeChunk]] = {}
        
        for chunk in chunks:
            if chunk.file_path not in file_chunks:
                file_chunks[chunk.file_path] = []
            file_chunks[chunk.file_path].append(chunk)
        
        citations = []
        for file_path, file_chunk_list in file_chunks.items():
            # Get line ranges
            lines = []
            for c in file_chunk_list:
                lines.append((c.start_line, c.end_line))
            
            # Merge overlapping ranges
            lines.sort()
            merged = []
            for start, end in lines:
                if merged and start <= merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            
            citations.append({
                "file": file_path,
                "language": file_chunk_list[0].language,
                "line_ranges": merged,
                "chunk_count": len(file_chunk_list),
            })
        
        return citations
    
    def pack_for_generation(
        self,
        query_chunks: List[CodeChunk],
        related_chunks: List[CodeChunk],
        priority_files: Optional[List[str]] = None,
    ) -> ContextPack:
        """
        Pack context for code generation with priority ordering.
        
        Args:
            query_chunks: Chunks directly matching the query (highest priority)
            related_chunks: Related chunks (lower priority)
            priority_files: Files to prioritize
            
        Returns:
            ContextPack optimized for generation
        """
        # Score and sort chunks
        scored_chunks = []
        
        for chunk in query_chunks:
            score = 100.0  # Base score for query matches
            if priority_files and chunk.file_path in priority_files:
                score += 50.0
            scored_chunks.append((score, chunk))
        
        for chunk in related_chunks:
            score = 50.0  # Base score for related
            if priority_files and chunk.file_path in priority_files:
                score += 25.0
            # Avoid duplicates
            if chunk.id not in {c.id for _, c in scored_chunks}:
                scored_chunks.append((score, chunk))
        
        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Pack with budget
        return self.pack_chunks([c for _, c in scored_chunks])
