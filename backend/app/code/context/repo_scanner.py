"""
Repository Scanner - Scans repository and collects file metadata.

Inspired by CodeFuse-CGM's graph-based repository parsing.
Supports Python and TypeScript with configurable exclusion patterns.
"""

import os
import logging
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Default exclusion patterns
DEFAULT_EXCLUDE_PATTERNS = [
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".coverage",
    "*.egg-info",
    ".tox",
    ".eggs",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.bin",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.rar",
    "*.7z",
    "*.pdf",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.svg",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.eot",
    "*.mp3",
    "*.mp4",
    "*.avi",
    "*.mov",
    ".DS_Store",
    "Thumbs.db",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
]

# Supported code file extensions
CODE_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".sql": "sql",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
}

# Maximum file size to process (1MB)
MAX_FILE_SIZE = 1024 * 1024


@dataclass
class FileInfo:
    """Information about a scanned file."""
    path: str  # Relative path from repo root
    absolute_path: str
    language: str
    size_bytes: int
    line_count: int
    extension: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "absolute_path": self.absolute_path,
            "language": self.language,
            "size_bytes": self.size_bytes,
            "line_count": self.line_count,
            "extension": self.extension,
        }


@dataclass
class ScanResult:
    """Result of repository scan."""
    repo_path: str
    files: List[FileInfo] = field(default_factory=list)
    file_count: int = 0
    total_lines: int = 0
    total_bytes: int = 0
    languages: Dict[str, int] = field(default_factory=dict)  # language -> file count
    skipped_files: List[str] = field(default_factory=list)
    skipped_reasons: Dict[str, str] = field(default_factory=dict)
    scan_duration_ms: int = 0
    scanned_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_path": self.repo_path,
            "file_count": self.file_count,
            "total_lines": self.total_lines,
            "total_bytes": self.total_bytes,
            "languages": self.languages,
            "skipped_count": len(self.skipped_files),
            "scan_duration_ms": self.scan_duration_ms,
            "scanned_at": self.scanned_at,
            "files": [f.to_dict() for f in self.files],
        }


class RepoScanner:
    """
    Scans a repository and collects file metadata.
    
    Features:
    - Configurable include/exclude patterns
    - Language detection by extension
    - File size limits
    - Line counting
    """
    
    def __init__(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size: int = MAX_FILE_SIZE,
    ):
        """
        Initialize scanner.
        
        Args:
            include_patterns: Glob patterns for files to include (default: all code files)
            exclude_patterns: Glob patterns for files/dirs to exclude
            max_file_size: Maximum file size in bytes to process
        """
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = list(set(DEFAULT_EXCLUDE_PATTERNS + (exclude_patterns or [])))
        self.max_file_size = max_file_size
    
    def _should_exclude(self, path: str, is_dir: bool = False) -> bool:
        """Check if path should be excluded."""
        name = os.path.basename(path)
        
        for pattern in self.exclude_patterns:
            # Check directory name
            if is_dir and fnmatch.fnmatch(name, pattern):
                return True
            # Check file name
            if fnmatch.fnmatch(name, pattern):
                return True
            # Check full path
            if fnmatch.fnmatch(path, pattern):
                return True
            # Check if pattern is in path
            if pattern in path:
                return True
        
        return False
    
    def _should_include(self, path: str) -> bool:
        """Check if path should be included."""
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        
        # Must be a known code file type
        if ext not in CODE_EXTENSIONS:
            return False
        
        # Check include patterns
        for pattern in self.include_patterns:
            if pattern == "*":
                return True
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(path, pattern):
                return True
        
        return False
    
    def _get_language(self, path: str) -> str:
        """Get language from file extension."""
        ext = os.path.splitext(path)[1].lower()
        return CODE_EXTENSIONS.get(ext, "unknown")
    
    def _count_lines(self, file_path: str) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def scan(self, repo_path: str) -> ScanResult:
        """
        Scan a repository.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            ScanResult with file information
            
        Raises:
            ValueError: If repo_path doesn't exist
        """
        start_time = datetime.utcnow()
        
        # Validate path
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        result = ScanResult(
            repo_path=repo_path,
            scanned_at=start_time.isoformat(),
        )
        
        languages: Dict[str, int] = {}
        
        # Walk the directory tree
        for root, dirs, files in os.walk(repo_path):
            # Filter out excluded directories (in-place modification)
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d), is_dir=True)]
            
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Check exclusion
                if self._should_exclude(rel_path):
                    result.skipped_files.append(rel_path)
                    result.skipped_reasons[rel_path] = "excluded_pattern"
                    continue
                
                # Check inclusion
                if not self._should_include(rel_path):
                    continue
                
                # Check file size
                try:
                    size = os.path.getsize(file_path)
                except OSError:
                    result.skipped_files.append(rel_path)
                    result.skipped_reasons[rel_path] = "cannot_read"
                    continue
                
                if size > self.max_file_size:
                    result.skipped_files.append(rel_path)
                    result.skipped_reasons[rel_path] = f"too_large_{size}_bytes"
                    continue
                
                # Get file info
                language = self._get_language(filename)
                line_count = self._count_lines(file_path)
                ext = os.path.splitext(filename)[1].lower()
                
                file_info = FileInfo(
                    path=rel_path,
                    absolute_path=file_path,
                    language=language,
                    size_bytes=size,
                    line_count=line_count,
                    extension=ext,
                )
                
                result.files.append(file_info)
                result.total_lines += line_count
                result.total_bytes += size
                
                # Track language counts
                languages[language] = languages.get(language, 0) + 1
        
        result.file_count = len(result.files)
        result.languages = languages
        
        end_time = datetime.utcnow()
        result.scan_duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(
            f"Scanned {result.file_count} files in {result.scan_duration_ms}ms "
            f"({result.total_lines} lines, {len(result.skipped_files)} skipped)"
        )
        
        return result
