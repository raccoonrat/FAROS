"""
Code Retriever - Retrieves relevant code chunks based on query.

Inspired by CodeFuse-CGM's anchor node location and BFS expansion.
Uses BM25/TF-IDF for lexical matching (embeddings optional for future).
"""

import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

from .chunker import CodeChunk

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A search result with score."""
    chunk: CodeChunk
    score: float
    match_terms: List[str]  # Terms that matched
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "match_terms": self.match_terms,
        }


class CodeRetriever:
    """
    Retrieves relevant code chunks using BM25 scoring.
    
    Features:
    - BM25 ranking algorithm
    - Code-aware tokenization
    - Fuzzy matching for identifiers
    - Boost for function/class names
    """
    
    # BM25 parameters
    K1 = 1.5
    B = 0.75
    
    def __init__(self, chunks: List[CodeChunk]):
        """
        Initialize retriever with chunks.
        
        Args:
            chunks: List of CodeChunk objects to index
        """
        self.chunks = chunks
        self.chunk_map = {c.id: c for c in chunks}
        
        # Build inverted index
        self._build_index()
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for retrieval.
        
        Handles:
        - CamelCase splitting
        - snake_case splitting
        - Code symbols
        """
        # Convert to lowercase
        text = text.lower()
        
        # Split CamelCase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Split snake_case
        text = text.replace('_', ' ')
        
        # Remove special characters but keep alphanumeric
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Split and filter
        tokens = text.split()
        tokens = [t for t in tokens if len(t) >= 2]
        
        return tokens
    
    def _build_index(self):
        """Build inverted index for BM25."""
        self.doc_freqs: Dict[str, int] = Counter()  # term -> doc count
        self.doc_lengths: Dict[str, int] = {}  # chunk_id -> length
        self.doc_terms: Dict[str, Counter] = {}  # chunk_id -> term counts
        
        total_length = 0
        
        for chunk in self.chunks:
            # Combine content with name for better matching
            text = chunk.content
            if chunk.name:
                text = f"{chunk.name} {chunk.name} {text}"  # Boost name
            
            tokens = self._tokenize(text)
            term_counts = Counter(tokens)
            
            self.doc_terms[chunk.id] = term_counts
            self.doc_lengths[chunk.id] = len(tokens)
            total_length += len(tokens)
            
            # Update document frequencies
            for term in set(tokens):
                self.doc_freqs[term] += 1
        
        self.avg_doc_length = total_length / len(self.chunks) if self.chunks else 1
        self.num_docs = len(self.chunks)
        
        logger.info(f"Built index with {len(self.doc_freqs)} unique terms from {self.num_docs} chunks")
    
    def _bm25_score(self, query_terms: List[str], chunk_id: str) -> Tuple[float, List[str]]:
        """
        Calculate BM25 score for a chunk.
        
        Returns:
            Tuple of (score, matched_terms)
        """
        score = 0.0
        matched_terms = []
        
        doc_terms = self.doc_terms.get(chunk_id, Counter())
        doc_length = self.doc_lengths.get(chunk_id, 0)
        
        for term in query_terms:
            if term not in doc_terms:
                continue
            
            matched_terms.append(term)
            
            # Term frequency in document
            tf = doc_terms[term]
            
            # Document frequency
            df = self.doc_freqs.get(term, 0)
            
            # IDF component
            idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1)
            
            # BM25 score component
            numerator = tf * (self.K1 + 1)
            denominator = tf + self.K1 * (1 - self.B + self.B * doc_length / self.avg_doc_length)
            
            score += idf * numerator / denominator
        
        return score, matched_terms
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
        file_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            top_k: Maximum number of results
            min_score: Minimum score threshold
            file_filter: Optional file path pattern to filter
            language_filter: Optional language to filter
            
        Returns:
            List of SearchResult objects sorted by score
        """
        query_terms = self._tokenize(query)
        
        if not query_terms:
            logger.warning("Empty query after tokenization")
            return []
        
        results = []
        
        for chunk in self.chunks:
            # Apply filters
            if file_filter and file_filter not in chunk.file_path:
                continue
            if language_filter and chunk.language != language_filter:
                continue
            
            score, matched_terms = self._bm25_score(query_terms, chunk.id)
            
            if score > min_score and matched_terms:
                results.append(SearchResult(
                    chunk=chunk,
                    score=score,
                    match_terms=matched_terms,
                ))
        
        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Return top-k
        return results[:top_k]
    
    def search_by_name(
        self,
        name: str,
        chunk_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """
        Search for chunks by function/class name.
        
        Args:
            name: Name to search for
            chunk_type: Optional type filter ("function", "class")
            top_k: Maximum results
            
        Returns:
            List of SearchResult objects
        """
        results = []
        name_lower = name.lower()
        
        for chunk in self.chunks:
            if chunk_type and chunk.chunk_type != chunk_type:
                continue
            
            if chunk.name:
                chunk_name_lower = chunk.name.lower()
                
                # Exact match gets highest score
                if chunk_name_lower == name_lower:
                    score = 10.0
                # Prefix match
                elif chunk_name_lower.startswith(name_lower):
                    score = 5.0
                # Contains match
                elif name_lower in chunk_name_lower:
                    score = 2.0
                else:
                    continue
                
                results.append(SearchResult(
                    chunk=chunk,
                    score=score,
                    match_terms=[name],
                ))
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
    
    def get_related_chunks(
        self,
        chunk_id: str,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """
        Get chunks related to a given chunk (same file, similar content).
        
        Args:
            chunk_id: ID of the reference chunk
            top_k: Maximum results
            
        Returns:
            List of related SearchResult objects
        """
        if chunk_id not in self.chunk_map:
            return []
        
        ref_chunk = self.chunk_map[chunk_id]
        results = []
        
        for chunk in self.chunks:
            if chunk.id == chunk_id:
                continue
            
            score = 0.0
            
            # Same file gets high score
            if chunk.file_path == ref_chunk.file_path:
                score += 5.0
                
                # Adjacent chunks get bonus
                if abs(chunk.start_line - ref_chunk.end_line) <= 10:
                    score += 2.0
            
            # Same language
            if chunk.language == ref_chunk.language:
                score += 1.0
            
            # Similar type
            if chunk.chunk_type == ref_chunk.chunk_type:
                score += 0.5
            
            if score > 0:
                results.append(SearchResult(
                    chunk=chunk,
                    score=score,
                    match_terms=["related"],
                ))
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
