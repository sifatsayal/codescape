"""
Configuration management for the codebase visualizer.

Handles loading and validation of visualizer configuration from files or defaults.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
import json


class VisualizerConfig:
    """Repo-agnostic visualizer configuration."""
    
    def __init__(
        self,
        repo_path: Path,
        code_extensions: Optional[Dict[str, str]] = None,
        skip_dirs: Optional[Set[str]] = None,
        source_dirs: Optional[List[str]] = None,
        max_files: int = 2000,
        max_depth: int = 6,
        pagerank_damping: float = 0.85,
        pagerank_iterations: int = 20,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize visualizer configuration.
        
        Args:
            repo_path: Path to the target repository
            code_extensions: Map of file extensions to language names
            skip_dirs: Set of directory names to skip during scanning
            source_dirs: List of source directories for import resolution
            max_files: Maximum number of files to process
            max_depth: Maximum directory depth to scan
            pagerank_damping: PageRank damping factor (0-1)
            pagerank_iterations: Number of PageRank iterations
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude
        """
        self.repo_path = Path(repo_path).resolve()
        self.code_extensions = code_extensions or self._default_code_extensions()
        self.skip_dirs = skip_dirs or self._default_skip_dirs()
        self.source_dirs = source_dirs or self._default_source_dirs()
        self.max_files = max_files
        self.max_depth = max_depth
        self.pagerank_damping = pagerank_damping
        self.pagerank_iterations = pagerank_iterations
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
    
    @classmethod
    def default(cls, repo_path: Path) -> 'VisualizerConfig':
        """Create config with sensible defaults."""
        return cls(repo_path=repo_path)
    
    @classmethod
    def from_file(cls, config_path: Path, repo_path: Optional[Path] = None) -> 'VisualizerConfig':
        """
        Load config from JSON file.
        
        Args:
            config_path: Path to .visualizer.json file
            repo_path: Override repo path (defaults to config file's parent)
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Use config file's directory as repo_path if not specified
        if repo_path is None:
            repo_path = config_path.parent
        
        return cls.from_dict(data, repo_path=repo_path)
    
    @classmethod
    def from_dict(cls, data: dict, repo_path: Path) -> 'VisualizerConfig':
        """Create config from dictionary."""
        return cls(
            repo_path=repo_path,
            code_extensions=data.get('codeExtensions'),
            skip_dirs=set(data.get('skipDirs', [])) if data.get('skipDirs') else None,
            source_dirs=data.get('sourceDirs'),
            max_files=data.get('maxFiles', 2000),
            max_depth=data.get('maxDepth', 6),
            pagerank_damping=data.get('pagerankDamping', 0.85),
            pagerank_iterations=data.get('pagerankIterations', 20),
            include_patterns=data.get('includePatterns', []),
            exclude_patterns=data.get('excludePatterns', []),
        )
    
    def find_config_file(self) -> Optional[Path]:
        """
        Look for .visualizer.json in repo or parent directories.
        
        Returns:
            Path to config file if found, None otherwise
        """
        current = self.repo_path
        while current != current.parent:
            config_file = current / '.visualizer.json'
            if config_file.exists():
                return config_file
            current = current.parent
        return None
    
    @classmethod
    def load_for_repo(cls, repo_path: Path) -> 'VisualizerConfig':
        """
        Load config for a repository, checking for .visualizer.json file.
        
        If .visualizer.json exists, loads it. Otherwise uses defaults.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            VisualizerConfig instance
        """
        repo_path = Path(repo_path).resolve()
        config = cls.default(repo_path)
        
        # Try to find and load config file
        config_file = config.find_config_file()
        if config_file:
            return cls.from_file(config_file, repo_path=repo_path)
        
        return config
    
    def _default_code_extensions(self) -> Dict[str, str]:
        """Default file extensions to analyze."""
        return {
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript React',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript React',
            '.mjs': 'JavaScript',
            '.cjs': 'JavaScript',
            '.py': 'Python',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.mdx': 'MDX',
            '.sql': 'SQL',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
        }
    
    def _default_skip_dirs(self) -> Set[str]:
        """Default directories to skip during scanning."""
        return {
            'node_modules', '.git', '__pycache__', '.next', '.turbo',
            'dist', 'build', '.cache', 'coverage', '.nyc_output',
            'vendor', 'venv', '.venv', 'env', '.env',
        }
    
    def _default_source_dirs(self) -> List[str]:
        """
        Default source directories for import resolution.
        
        These are common patterns across many repos. Can be overridden
        in config file for repo-specific structures.
        """
        return ['src', 'lib', 'app', 'components', 'utils', 'packages', '']
