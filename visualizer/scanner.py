"""
Repository scanner module.

Scans a target repository and extracts file/folder structure.
"""

from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict

from .config import VisualizerConfig


class RepoScanner:
    """Scans a target repository and extracts structure."""
    
    def __init__(self, config: VisualizerConfig):
        """
        Initialize scanner with configuration.
        
        Args:
            config: VisualizerConfig instance
        """
        self.config = config
        self.root = config.repo_path
        self.files: Dict[str, dict] = {}
        self.folders: Dict[str, dict] = {}
        self.file_count = 0
    
    def scan(self) -> Dict[str, Dict]:
        """
        Scan the repository and return file/folder structure.
        
        Returns:
            Dictionary with 'files' and 'folders' keys
        """
        print(f"📂 Scanning: {self.root}")
        self._scan_directory(self.root, depth=0)
        print(f"✅ Found {len(self.files)} files in {len(self.folders)} folders")
        
        return {
            'files': self.files,
            'folders': self.folders,
        }
    
    def _scan_directory(self, path: Path, depth: int) -> Optional[dict]:
        """Recursively scan directory structure."""
        if depth > self.config.max_depth or self.file_count > self.config.max_files:
            return None
            
        rel_path = str(path.relative_to(self.root)).replace('\\', '/')
        if rel_path == '.':
            rel_path = ''

        folder_info = {
            'name': path.name or self.root.name,
            'path': rel_path,
            'type': 'folder',
            'children': [],
            'file_count': 0,
            'code_files': 0,
            'subfolder_count': 0,
            'direct_file_count': 0,
        }
        
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return None
            
        for entry in entries:
            if entry.name.startswith('.') and entry.name not in ['.env.example']:
                continue
                
            if entry.is_dir():
                if entry.name in self.config.skip_dirs:
                    continue
                child = self._scan_directory(entry, depth + 1)
                if child:
                    folder_info['children'].append(child['path'] or child['name'])
                    folder_info['file_count'] += child['file_count']
                    folder_info['code_files'] += child['code_files']
                    folder_info['subfolder_count'] += 1
            else:
                if self.file_count > self.config.max_files:
                    continue
                    
                file_info = self._analyze_file(entry)
                if file_info:
                    folder_info['children'].append(file_info['path'])
                    folder_info['file_count'] += 1
                    folder_info['direct_file_count'] += 1
                    if file_info.get('is_code'):
                        folder_info['code_files'] += 1
                    self.file_count += 1

        # Recursive subfolder count = direct + sum of children's recursive counts
        folder_info['recursive_subfolder_count'] = folder_info['subfolder_count']
        for child_path in folder_info['children']:
            if child_path in self.folders:
                folder_info['recursive_subfolder_count'] += self.folders[child_path].get('recursive_subfolder_count', 0)

        self.folders[rel_path] = folder_info
        return folder_info
    
    def _analyze_file(self, path: Path) -> Optional[dict]:
        """Extract file metadata."""
        rel_path = str(path.relative_to(self.root)).replace('\\', '/')
        ext = path.suffix.lower()
        
        file_info = {
            'name': path.name,
            'path': rel_path,
            'type': 'file',
            'extension': ext,
            'language': self.config.code_extensions.get(ext, 'Other'),
            'is_code': ext in self.config.code_extensions,
            'loc': 0,
            'imports': [],
        }
        
        # Count lines of code
        try:
            if ext in self.config.code_extensions and path.stat().st_size < 500000:  # Skip huge files
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    file_info['loc'] = len(content.splitlines())
        except Exception:
            pass
            
        self.files[rel_path] = file_info
        return file_info
