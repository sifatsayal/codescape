#!/usr/bin/env python3
"""
Codebase Visualizer - A visual exploration tool for understanding code structure.

This script scans a local repository, extracts file/folder structure and import
relationships, computes dependency graph metrics (fan-in, fan-out, PageRank),
then generates an interactive D3.js visualization that opens in your browser.

Features:
- File-to-file import dependency graph for JS/TS (ESM + CommonJS)
- Architectural importance signals (fan-in, fan-out, PageRank)
- Selective edge rendering (only for selected node)
- Hotspots panel showing most depended-on files

Usage: python visualize_codebase.py [path_to_repo]
"""

import os
import re
import json
import webbrowser
import tempfile
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
import hashlib

# File extensions we care about
CODE_EXTENSIONS = {
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

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', '.next', '.turbo', 
    'dist', 'build', '.cache', 'coverage', '.nyc_output',
    'vendor', 'venv', '.venv', 'env', '.env',
}

# Max files to process (for performance)
MAX_FILES = 2000
MAX_DEPTH = 6

# PageRank parameters
PAGERANK_DAMPING = 0.85
PAGERANK_ITERATIONS = 20


class CodebaseAnalyzer:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.files: Dict[str, dict] = {}
        self.folders: Dict[str, dict] = {}
        self.imports: Dict[str, List[str]] = defaultdict(list)
        self.file_count = 0
        # Dependency graph: source -> list of targets (files this file imports)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        # Reverse dependency graph: target -> list of sources (files that import this file)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        # Metrics
        self.fan_in: Dict[str, int] = {}
        self.fan_out: Dict[str, int] = {}
        self.pagerank: Dict[str, float] = {}
        
    def analyze(self) -> dict:
        """Analyze the codebase and return structured data."""
        print(f"📂 Scanning: {self.root}")
        self._scan_directory(self.root, depth=0)
        print(f"✅ Found {len(self.files)} files in {len(self.folders)} folders")
        
        print("🔍 Extracting imports...")
        self._extract_all_imports()
        
        print("📊 Computing dependency metrics...")
        self._compute_dependency_graph()
        self._compute_metrics()
        
        return self._build_graph_data()
    
    def _scan_directory(self, path: Path, depth: int) -> Optional[dict]:
        """Recursively scan directory structure."""
        if depth > MAX_DEPTH or self.file_count > MAX_FILES:
            return None
            
        rel_path = str(path.relative_to(self.root))
        if rel_path == '.':
            rel_path = ''
            
        folder_info = {
            'name': path.name or self.root.name,
            'path': rel_path,
            'type': 'folder',
            'children': [],
            'file_count': 0,
            'code_files': 0,
        }
        
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return None
            
        for entry in entries:
            if entry.name.startswith('.') and entry.name not in ['.env.example']:
                continue
                
            if entry.is_dir():
                if entry.name in SKIP_DIRS:
                    continue
                child = self._scan_directory(entry, depth + 1)
                if child:
                    folder_info['children'].append(child['path'] or child['name'])
                    folder_info['file_count'] += child['file_count']
                    folder_info['code_files'] += child['code_files']
            else:
                if self.file_count > MAX_FILES:
                    continue
                    
                file_info = self._analyze_file(entry)
                if file_info:
                    folder_info['children'].append(file_info['path'])
                    folder_info['file_count'] += 1
                    if file_info.get('is_code'):
                        folder_info['code_files'] += 1
                    self.file_count += 1
        
        self.folders[rel_path] = folder_info
        return folder_info
    
    def _analyze_file(self, path: Path) -> Optional[dict]:
        """Extract file metadata."""
        rel_path = str(path.relative_to(self.root))
        ext = path.suffix.lower()
        
        file_info = {
            'name': path.name,
            'path': rel_path,
            'type': 'file',
            'extension': ext,
            'language': CODE_EXTENSIONS.get(ext, 'Other'),
            'is_code': ext in CODE_EXTENSIONS,
            'loc': 0,
            'imports': [],
        }
        
        # Count lines of code
        try:
            if ext in CODE_EXTENSIONS and path.stat().st_size < 500000:  # Skip huge files
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    file_info['loc'] = len(content.splitlines())
        except Exception:
            pass
            
        self.files[rel_path] = file_info
        return file_info
    
    def _extract_all_imports(self):
        """Extract imports from all code files."""
        for path, info in self.files.items():
            if not info.get('is_code'):
                continue
                
            ext = info['extension']
            full_path = self.root / path
            
            try:
                if full_path.stat().st_size > 200000:  # Skip large files
                    continue
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue
            
            imports = []
            if ext in ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.vue', '.svelte']:
                imports = self._extract_js_imports(content)
            elif ext == '.py':
                imports = self._extract_python_imports(content)
            elif ext == '.go':
                imports = self._extract_go_imports(content)
                
            info['imports'] = imports[:30]  # Limit imports shown
            self.imports[path] = imports
    
    def _extract_js_imports(self, content: str) -> List[str]:
        """Extract JavaScript/TypeScript imports (ESM and CommonJS)."""
        imports = []
        
        # ESM: import ... from '...'
        pattern1 = r"import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+\w+|\w+))*\s+from\s+)?['\"]([^'\"]+)['\"]"
        # ESM: export ... from '...'
        pattern2 = r"export\s+(?:\{[^}]*\}|\*)\s+from\s+['\"]([^'\"]+)['\"]"
        # CommonJS: require('...')
        pattern3 = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        # Dynamic import: import('...')
        pattern4 = r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        
        for pattern in [pattern1, pattern2, pattern3, pattern4]:
            for match in re.finditer(pattern, content):
                imports.append(match.group(1))
            
        return list(dict.fromkeys(imports))  # Remove duplicates, preserve order
    
    def _extract_python_imports(self, content: str) -> List[str]:
        """Extract Python imports."""
        imports = []
        
        # import x or from x import y
        pattern1 = r"^import\s+([\w.]+)"
        pattern2 = r"^from\s+([\w.]+)\s+import"
        
        for line in content.split('\n'):
            line = line.strip()
            match = re.match(pattern1, line) or re.match(pattern2, line)
            if match:
                imports.append(match.group(1))
                
        return list(dict.fromkeys(imports))
    
    def _extract_go_imports(self, content: str) -> List[str]:
        """Extract Go imports."""
        imports = []
        pattern = r'"([^"]+)"'
        
        # Find import block
        import_match = re.search(r'import\s*\((.*?)\)', content, re.DOTALL)
        if import_match:
            for match in re.finditer(pattern, import_match.group(1)):
                imports.append(match.group(1))
        else:
            # Single import
            single = re.search(r'import\s+"([^"]+)"', content)
            if single:
                imports.append(single.group(1))
                
        return imports
    
    def _compute_dependency_graph(self):
        """Build the file-to-file dependency graph from resolved imports."""
        for source_path, raw_imports in self.imports.items():
            for imp in raw_imports:
                target = self._resolve_import(source_path, imp)
                if target and target in self.files and target != source_path:
                    self.dependencies[source_path].add(target)
                    self.dependents[target].add(source_path)
    
    def _resolve_import(self, from_file: str, import_path: str) -> Optional[str]:
        """Resolve an import to an actual file path in the codebase."""
        from_dir = str(Path(from_file).parent)
        
        # Handle relative imports
        if import_path.startswith('./') or import_path.startswith('../'):
            if import_path.startswith('./'):
                resolved = str(Path(from_dir) / import_path[2:])
            else:
                try:
                    resolved = str((Path(from_dir) / import_path).resolve().relative_to(self.root.resolve()))
                except ValueError:
                    return None
            
            # Try common extensions and index files
            candidates = self._get_import_candidates(resolved)
            for candidate in candidates:
                if candidate in self.files:
                    return candidate
            return None
        
        # Handle non-relative imports (could be aliases or package imports)
        # Try to find as a path from common source directories
        source_dirs = ['src', 'lib', 'app', 'components', 'utils', 'packages', '']
        
        for src_dir in source_dirs:
            base = str(Path(src_dir) / import_path) if src_dir else import_path
            candidates = self._get_import_candidates(base)
            for candidate in candidates:
                if candidate in self.files:
                    return candidate
        
        # Try without the first path segment (common for aliases like @/...)
        if import_path.startswith('@'):
            # Handle @/ or @alias/ patterns
            parts = import_path.split('/', 1)
            if len(parts) > 1:
                alias_path = parts[1]
                for src_dir in source_dirs:
                    base = str(Path(src_dir) / alias_path) if src_dir else alias_path
                    candidates = self._get_import_candidates(base)
                    for candidate in candidates:
                        if candidate in self.files:
                            return candidate
        
        return None
    
    def _get_import_candidates(self, base_path: str) -> List[str]:
        """Generate possible file paths for an import."""
        # Normalize path separators
        base_path = base_path.replace('\\', '/')
        
        candidates = []
        extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.vue', '.svelte', '.json']
        
        # Direct file (with extension already)
        if any(base_path.endswith(ext) for ext in extensions):
            candidates.append(base_path)
        
        # Add extensions
        for ext in extensions:
            candidates.append(base_path + ext)
        
        # Index files
        for ext in extensions:
            candidates.append(f"{base_path}/index{ext}")
        
        return candidates
    
    def _compute_metrics(self):
        """Compute graph metrics: fan-in, fan-out, and PageRank."""
        # Fan-in (how many files depend on this file)
        # Fan-out (how many files this file depends on)
        for path in self.files:
            self.fan_in[path] = len(self.dependents.get(path, set()))
            self.fan_out[path] = len(self.dependencies.get(path, set()))
        
        # PageRank - iterative computation
        # Initialize all nodes with equal rank
        n = len(self.files)
        if n == 0:
            return
            
        rank = {path: 1.0 / n for path in self.files}
        
        for _ in range(PAGERANK_ITERATIONS):
            new_rank = {}
            for path in self.files:
                # Sum of rank from incoming edges (dependents)
                incoming_sum = 0.0
                for dep in self.dependents.get(path, set()):
                    out_degree = len(self.dependencies.get(dep, set()))
                    if out_degree > 0:
                        incoming_sum += rank.get(dep, 0) / out_degree
                
                new_rank[path] = (1 - PAGERANK_DAMPING) / n + PAGERANK_DAMPING * incoming_sum
            rank = new_rank
        
        self.pagerank = rank
    
    def _build_graph_data(self) -> dict:
        """Build data structure for D3 visualization."""
        nodes = []
        links = []
        
        # Add folder nodes
        for path, info in self.folders.items():
            node_id = path or 'root'
            nodes.append({
                'id': node_id,
                'name': info['name'],
                'type': 'folder',
                'path': path,
                'fileCount': info['file_count'],
                'codeFiles': info['code_files'],
                'children': info['children'],
            })
        
        # Add file nodes with metrics
        for path, info in self.files.items():
            fan_in = self.fan_in.get(path, 0)
            fan_out = self.fan_out.get(path, 0)
            pr = self.pagerank.get(path, 0)
            
            # Get resolved dependencies and dependents
            deps = list(self.dependencies.get(path, set()))
            depts = list(self.dependents.get(path, set()))
            
            nodes.append({
                'id': path,
                'name': info['name'],
                'type': 'file',
                'path': path,
                'language': info['language'],
                'extension': info['extension'],
                'loc': info['loc'],
                'imports': info['imports'],
                # New metrics
                'fanIn': fan_in,
                'fanOut': fan_out,
                'pagerank': round(pr * 10000, 2),  # Scale for readability
                'dependencies': deps[:20],  # Files this file imports (resolved)
                'dependents': depts[:20],   # Files that import this file
            })
            
            # Create links for all resolved dependencies
            for target in deps:
                links.append({
                    'source': path,
                    'target': target,
                    'type': 'import'
                })
        
        # Compute hotspots (top 10 most depended-on files)
        sorted_by_fan_in = sorted(
            [(p, self.fan_in.get(p, 0), self.pagerank.get(p, 0)) 
             for p in self.files if self.fan_in.get(p, 0) > 0],
            key=lambda x: (x[1], x[2]),
            reverse=True
        )[:15]
        
        hotspots = []
        for path, fan_in, pr in sorted_by_fan_in:
            info = self.files[path]
            # Generate a one-line explanation
            dependents_preview = list(self.dependents.get(path, set()))[:3]
            if len(dependents_preview) > 0:
                preview = ', '.join(Path(d).name for d in dependents_preview)
                if fan_in > 3:
                    preview += f' +{fan_in - 3} more'
                explanation = f"Used by: {preview}"
            else:
                explanation = "Core utility"
            
            hotspots.append({
                'path': path,
                'name': info['name'],
                'fanIn': fan_in,
                'pagerank': round(pr * 10000, 2),
                'explanation': explanation,
            })
        
        # Compute max values for normalization
        max_fan_in = max((self.fan_in.get(p, 0) for p in self.files), default=1) or 1
        max_fan_out = max((self.fan_out.get(p, 0) for p in self.files), default=1) or 1
        max_pagerank = max((self.pagerank.get(p, 0) for p in self.files), default=0.0001) or 0.0001
        
        return {
            'nodes': nodes,
            'links': links,
            'rootName': self.root.name,
            'hotspots': hotspots,
            'maxMetrics': {
                'fanIn': max_fan_in,
                'fanOut': max_fan_out,
                'pagerank': max_pagerank * 10000,
            },
            'stats': {
                'totalFiles': len(self.files),
                'totalFolders': len(self.folders),
                'codeFiles': sum(1 for f in self.files.values() if f.get('is_code')),
                'totalLoc': sum(f.get('loc', 0) for f in self.files.values()),
                'totalDependencies': sum(len(d) for d in self.dependencies.values()),
            }
        }


def generate_html(data: dict) -> str:
    """Generate the interactive HTML visualization."""
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Explorer - ''' + data['rootName'] + '''</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Space Grotesk', sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
            color: #e0e0e0;
            overflow: hidden;
            height: 100vh;
        }
        
        #header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: rgba(15, 15, 25, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(100, 100, 150, 0.2);
            display: flex;
            align-items: center;
            padding: 0 24px;
            z-index: 100;
            gap: 24px;
        }
        
        #header h1 {
            font-size: 18px;
            font-weight: 600;
            background: linear-gradient(90deg, #00d4aa, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: #888;
        }
        
        .stat {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .stat-value {
            color: #00d4aa;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .controls {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .control-group {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: #888;
        }
        
        .control-group select {
            background: rgba(30, 30, 50, 0.8);
            border: 1px solid rgba(100, 100, 150, 0.3);
            border-radius: 6px;
            padding: 6px 10px;
            color: #e0e0e0;
            font-size: 12px;
            cursor: pointer;
        }
        
        .control-group select:focus {
            outline: none;
            border-color: #7c3aed;
        }
        
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: auto;
            font-size: 13px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .breadcrumb-item {
            color: #7c3aed;
            cursor: pointer;
            transition: color 0.2s;
        }
        
        .breadcrumb-item:hover {
            color: #a78bfa;
        }
        
        .breadcrumb-sep {
            color: #444;
        }
        
        #graph-container {
            position: fixed;
            top: 60px;
            left: 0;
            right: 380px;
            bottom: 0;
        }
        
        #sidebar {
            position: fixed;
            top: 60px;
            right: 0;
            width: 380px;
            bottom: 0;
            background: rgba(15, 15, 25, 0.95);
            border-left: 1px solid rgba(100, 100, 150, 0.2);
            overflow-y: auto;
            padding: 20px;
        }
        
        .sidebar-section {
            margin-bottom: 24px;
        }
        
        .sidebar-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #666;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .sidebar-title .badge {
            background: rgba(124, 58, 237, 0.3);
            color: #a78bfa;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
        }
        
        .file-info {
            background: rgba(30, 30, 50, 0.5);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(100, 100, 150, 0.15);
        }
        
        .file-name {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            word-break: break-all;
        }
        
        .file-path {
            font-size: 12px;
            color: #666;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 16px;
            word-break: break-all;
        }
        
        .file-meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .file-meta.four-col {
            grid-template-columns: 1fr 1fr 1fr 1fr;
        }
        
        .meta-item {
            background: rgba(20, 20, 35, 0.6);
            padding: 10px 12px;
            border-radius: 8px;
        }
        
        .meta-item.highlight {
            background: rgba(124, 58, 237, 0.15);
            border: 1px solid rgba(124, 58, 237, 0.3);
        }
        
        .meta-label {
            font-size: 10px;
            text-transform: uppercase;
            color: #555;
            margin-bottom: 4px;
        }
        
        .meta-value {
            font-size: 14px;
            font-weight: 500;
            color: #00d4aa;
        }
        
        .meta-value.purple {
            color: #a78bfa;
        }
        
        .meta-value.orange {
            color: #f59e0b;
        }
        
        .deps-section {
            margin-top: 16px;
        }
        
        .deps-title {
            font-size: 12px;
            color: #888;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .deps-title .count {
            color: #00d4aa;
            font-weight: 600;
        }
        
        .dep-item {
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            padding: 8px 12px;
            background: rgba(20, 20, 35, 0.4);
            border-radius: 6px;
            margin-bottom: 4px;
            color: #888;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .dep-item:hover {
            background: rgba(124, 58, 237, 0.2);
            color: #e0e0e0;
        }
        
        .dep-item .arrow {
            font-size: 10px;
            color: #555;
        }
        
        .dep-item.inbound .arrow {
            color: #00d4aa;
        }
        
        .dep-item.outbound .arrow {
            color: #f59e0b;
        }
        
        .dep-item .name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .imports-list {
            margin-top: 16px;
        }
        
        .imports-title {
            font-size: 12px;
            color: #888;
            margin-bottom: 8px;
        }
        
        .import-item {
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            padding: 6px 10px;
            background: rgba(124, 58, 237, 0.1);
            border-radius: 6px;
            margin-bottom: 4px;
            color: #a78bfa;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .folder-contents {
            margin-top: 16px;
        }
        
        .folder-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: rgba(20, 20, 35, 0.4);
            border-radius: 8px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 13px;
        }
        
        .folder-item:hover {
            background: rgba(124, 58, 237, 0.2);
        }
        
        .folder-icon {
            font-size: 14px;
        }
        
        .item-name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .item-meta {
            font-size: 11px;
            color: #555;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .hotspot-item {
            padding: 12px;
            background: rgba(20, 20, 35, 0.4);
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        
        .hotspot-item:hover {
            background: rgba(124, 58, 237, 0.15);
        }
        
        .hotspot-item.rank-1 { border-left-color: #fbbf24; }
        .hotspot-item.rank-2 { border-left-color: #94a3b8; }
        .hotspot-item.rank-3 { border-left-color: #b45309; }
        
        .hotspot-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        
        .hotspot-rank {
            font-size: 11px;
            font-weight: 600;
            color: #555;
            width: 20px;
        }
        
        .hotspot-name {
            font-size: 13px;
            font-weight: 500;
            color: #e0e0e0;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .hotspot-metric {
            font-size: 11px;
            color: #00d4aa;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .hotspot-path {
            font-size: 11px;
            color: #555;
            font-family: 'JetBrains Mono', monospace;
            margin-left: 28px;
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .hotspot-explanation {
            font-size: 11px;
            color: #888;
            margin-left: 28px;
        }
        
        svg {
            width: 100%;
            height: 100%;
        }
        
        .node {
            cursor: pointer;
        }
        
        .node circle {
            stroke-width: 2px;
            transition: all 0.2s;
        }
        
        .node.selected circle {
            stroke-width: 4px;
            filter: brightness(1.3) drop-shadow(0 0 8px currentColor);
        }
        
        .node:hover circle {
            filter: brightness(1.3);
        }
        
        .node text {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            fill: #999;
            pointer-events: none;
        }
        
        .link {
            fill: none;
            stroke-opacity: 0;
            transition: stroke-opacity 0.3s;
        }
        
        .link.visible {
            stroke-opacity: 0.6;
        }
        
        .link.import {
            stroke: #7c3aed;
        }
        
        .link.inbound {
            stroke: #00d4aa;
            stroke-width: 2px;
        }
        
        .link.outbound {
            stroke: #f59e0b;
            stroke-width: 2px;
        }
        
        .link-arrow {
            fill: #7c3aed;
        }
        
        #legend {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(15, 15, 25, 0.95);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid rgba(100, 100, 150, 0.2);
            font-size: 12px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }
        
        .legend-circle {
            width: 14px;
            height: 14px;
            border-radius: 50%;
        }
        
        .legend-line {
            width: 24px;
            height: 3px;
            border-radius: 2px;
        }
        
        #help {
            position: fixed;
            bottom: 20px;
            right: 400px;
            background: rgba(15, 15, 25, 0.95);
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid rgba(100, 100, 150, 0.2);
            font-size: 11px;
            color: #666;
        }
        
        .help-key {
            display: inline-block;
            background: rgba(100, 100, 150, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            margin: 0 4px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .placeholder {
            color: #444;
            font-style: italic;
            padding: 40px;
            text-align: center;
        }
        
        .empty-state {
            color: #555;
            font-size: 12px;
            padding: 12px;
            text-align: center;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>⬡ Codebase Explorer</h1>
        <div class="stats">
            <div class="stat">
                <span>Files:</span>
                <span class="stat-value">''' + str(data['stats']['totalFiles']) + '''</span>
            </div>
            <div class="stat">
                <span>Deps:</span>
                <span class="stat-value">''' + str(data['stats']['totalDependencies']) + '''</span>
            </div>
            <div class="stat">
                <span>LOC:</span>
                <span class="stat-value">''' + f"{data['stats']['totalLoc']:,}" + '''</span>
            </div>
        </div>
        <div class="controls">
            <div class="control-group">
                <label>Size by:</label>
                <select id="sizeMode">
                    <option value="loc">Lines of Code</option>
                    <option value="fanIn" selected>Fan-In (dependents)</option>
                    <option value="fanOut">Fan-Out (dependencies)</option>
                    <option value="pagerank">PageRank</option>
                </select>
            </div>
            <div class="control-group">
                <label>Color by:</label>
                <select id="colorMode">
                    <option value="language" selected>Language</option>
                    <option value="fanIn">Fan-In (importance)</option>
                    <option value="fanOut">Fan-Out (coupling)</option>
                </select>
            </div>
        </div>
        <div class="breadcrumb" id="breadcrumb">
            <span class="breadcrumb-item" onclick="navigateTo('')">''' + data['rootName'] + '''</span>
        </div>
    </div>
    
    <div id="graph-container">
        <svg id="graph">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#7c3aed" opacity="0.6"/>
                </marker>
                <marker id="arrowhead-inbound" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#00d4aa"/>
                </marker>
                <marker id="arrowhead-outbound" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#f59e0b"/>
                </marker>
            </defs>
        </svg>
    </div>
    
    <div id="sidebar">
        <div class="sidebar-section">
            <div class="sidebar-title">🔥 Hotspots <span class="badge">Most Depended</span></div>
            <div id="hotspots-list">
                ''' + ''.join([f'''
                <div class="hotspot-item rank-{i+1 if i < 3 else ''}" onclick="focusFile('{h['path']}')">
                    <div class="hotspot-header">
                        <span class="hotspot-rank">#{i+1}</span>
                        <span class="hotspot-name">{h['name']}</span>
                        <span class="hotspot-metric">⬅ {h['fanIn']}</span>
                    </div>
                    <div class="hotspot-path">{h['path']}</div>
                    <div class="hotspot-explanation">{h['explanation']}</div>
                </div>
                ''' for i, h in enumerate(data['hotspots'][:10])]) + '''
            </div>
        </div>
        <div id="details-panel">
            <div class="placeholder">Click on a node to view details</div>
        </div>
    </div>
    
    <div id="legend">
        <div class="legend-item">
            <div class="legend-circle" style="background: #7c3aed;"></div>
            <span>Folder</span>
        </div>
        <div class="legend-item">
            <div class="legend-circle" style="background: #00d4aa;"></div>
            <span>TypeScript/JavaScript</span>
        </div>
        <div class="legend-item">
            <div class="legend-circle" style="background: #f59e0b;"></div>
            <span>Python</span>
        </div>
        <div class="legend-item" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(100,100,150,0.2);">
            <div class="legend-line" style="background: #00d4aa;"></div>
            <span>Inbound (depends on selected)</span>
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background: #f59e0b;"></div>
            <span>Outbound (selected imports)</span>
        </div>
    </div>
    
    <div id="help">
        <span class="help-key">Scroll</span> zoom
        <span class="help-key">Drag</span> pan
        <span class="help-key">Click</span> select & show deps
    </div>

    <script>
        const graphData = ''' + json.dumps(data) + ''';
        
        // Build lookup maps
        const nodesById = new Map(graphData.nodes.map(n => [n.id, n]));
        const linksMap = new Map(); // source -> target -> link
        graphData.links.forEach(l => {
            if (!linksMap.has(l.source)) linksMap.set(l.source, new Map());
            linksMap.get(l.source).set(l.target, l);
        });
        
        let currentPath = '';
        let selectedNode = null;
        let simulation = null;
        let sizeMode = 'fanIn';
        let colorMode = 'language';
        
        const maxMetrics = graphData.maxMetrics;
        
        const width = document.getElementById('graph-container').clientWidth;
        const height = document.getElementById('graph-container').clientHeight;
        
        const svg = d3.select('#graph')
            .attr('viewBox', [0, 0, width, height]);
            
        const g = svg.append('g');
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });
            
        svg.call(zoom);
        
        // Click on background to deselect
        svg.on('click', () => {
            selectedNode = null;
            updateSelection();
        });
        
        // Control listeners
        document.getElementById('sizeMode').addEventListener('change', (e) => {
            sizeMode = e.target.value;
            renderGraph();
        });
        
        document.getElementById('colorMode').addEventListener('change', (e) => {
            colorMode = e.target.value;
            renderGraph();
        });
        
        // Color scales
        const fanInColorScale = d3.scaleSequential(d3.interpolateGreens)
            .domain([0, Math.log(maxMetrics.fanIn + 1)]);
        const fanOutColorScale = d3.scaleSequential(d3.interpolateOranges)
            .domain([0, Math.log(maxMetrics.fanOut + 1)]);
        
        function getNodeColor(node) {
            if (node.type === 'folder') return '#7c3aed';
            
            if (colorMode === 'fanIn' && node.fanIn !== undefined) {
                const intensity = Math.log(node.fanIn + 1) / Math.log(maxMetrics.fanIn + 1);
                return d3.interpolateRgb('#1a3a1a', '#00ff88')(Math.min(1, intensity * 1.5));
            }
            if (colorMode === 'fanOut' && node.fanOut !== undefined) {
                const intensity = Math.log(node.fanOut + 1) / Math.log(maxMetrics.fanOut + 1);
                return d3.interpolateRgb('#3a2a1a', '#ffaa00')(Math.min(1, intensity * 1.5));
            }
            
            // Default: by language
            const lang = node.language || '';
            if (lang.includes('TypeScript') || lang.includes('JavaScript')) return '#00d4aa';
            if (lang === 'Python') return '#f59e0b';
            if (lang === 'Go') return '#00add8';
            if (lang === 'Rust') return '#ff6b35';
            if (lang === 'CSS' || lang === 'SCSS') return '#e91e8c';
            if (lang === 'JSON' || lang === 'YAML' || lang === 'TOML') return '#6b7280';
            return '#3b82f6';
        }
        
        function getNodeSize(node) {
            if (node.type === 'folder') {
                return Math.min(30, 12 + Math.sqrt(node.fileCount || 1) * 3);
            }
            
            let value = 1;
            let maxValue = 1;
            
            if (sizeMode === 'fanIn') {
                value = node.fanIn || 0;
                maxValue = maxMetrics.fanIn;
            } else if (sizeMode === 'fanOut') {
                value = node.fanOut || 0;
                maxValue = maxMetrics.fanOut;
            } else if (sizeMode === 'pagerank') {
                value = node.pagerank || 0;
                maxValue = maxMetrics.pagerank;
            } else {
                value = node.loc || 1;
                maxValue = 1000;
            }
            
            // Scale: min 6, max 24 for files
            const normalized = Math.sqrt(value) / Math.sqrt(maxValue || 1);
            return Math.max(6, Math.min(24, 6 + normalized * 18));
        }
        
        function navigateTo(path) {
            currentPath = path;
            selectedNode = null;
            updateBreadcrumb();
            renderGraph();
            updateDetailsPanel();
        }
        
        function focusFile(path) {
            // Navigate to the file's parent folder and select it
            const parts = path.split('/');
            parts.pop(); // Remove filename
            const parentPath = parts.join('/');
            
            currentPath = parentPath;
            selectedNode = nodesById.get(path);
            updateBreadcrumb();
            renderGraph();
            updateDetailsPanel();
            updateSelection();
        }
        
        function updateBreadcrumb() {
            const parts = currentPath ? currentPath.split('/') : [];
            let html = `<span class="breadcrumb-item" onclick="navigateTo('')">${graphData.rootName}</span>`;
            
            let accumulated = '';
            for (const part of parts) {
                accumulated += (accumulated ? '/' : '') + part;
                const p = accumulated;
                html += `<span class="breadcrumb-sep">/</span>`;
                html += `<span class="breadcrumb-item" onclick="navigateTo('${p}')">${part}</span>`;
            }
            
            document.getElementById('breadcrumb').innerHTML = html;
        }
        
        function renderGraph() {
            g.selectAll('*').remove();
            
            // Get current folder
            const currentFolder = nodesById.get(currentPath || 'root');
            if (!currentFolder || !currentFolder.children) return;
            
            // Get visible nodes (children of current folder)
            const visibleNodeIds = new Set(currentFolder.children);
            const visibleNodes = graphData.nodes.filter(n => visibleNodeIds.has(n.id) || visibleNodeIds.has(n.path));
            
            // Get ALL links for visible nodes (we'll show/hide based on selection)
            const visibleLinks = graphData.links.filter(l => 
                (visibleNodeIds.has(l.source) || visibleNodeIds.has(l.source?.id)) &&
                (visibleNodeIds.has(l.target) || visibleNodeIds.has(l.target?.id))
            );
            
            if (visibleNodes.length === 0) {
                g.append('text')
                    .attr('x', width / 2)
                    .attr('y', height / 2)
                    .attr('text-anchor', 'middle')
                    .attr('fill', '#666')
                    .text('Empty folder');
                return;
            }
            
            // Create force simulation
            simulation = d3.forceSimulation(visibleNodes)
                .force('link', d3.forceLink(visibleLinks).id(d => d.id).distance(120).strength(0.3))
                .force('charge', d3.forceManyBody().strength(-400))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(d => getNodeSize(d) + 25));
            
            // Draw links (initially hidden, shown based on selection)
            const link = g.append('g')
                .attr('class', 'links')
                .selectAll('line')
                .data(visibleLinks)
                .join('line')
                .attr('class', d => `link ${d.type}`)
                .attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)');
            
            // Draw nodes
            const node = g.append('g')
                .attr('class', 'nodes')
                .selectAll('g')
                .data(visibleNodes)
                .join('g')
                .attr('class', d => `node ${d.id === selectedNode?.id ? 'selected' : ''}`)
                .attr('data-id', d => d.id)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended))
                .on('click', (event, d) => {
                    event.stopPropagation();
                    if (d.type === 'folder') {
                        navigateTo(d.path || d.id);
                    }
                    selectedNode = d;
                    updateSelection();
                    showDetails(d);
                });
            
            node.append('circle')
                .attr('r', d => getNodeSize(d))
                .attr('fill', d => getNodeColor(d))
                .attr('stroke', d => d3.color(getNodeColor(d))?.darker(0.5) || '#333');
            
            node.append('text')
                .attr('dy', d => getNodeSize(d) + 14)
                .attr('text-anchor', 'middle')
                .text(d => d.name.length > 20 ? d.name.slice(0, 18) + '...' : d.name);
            
            // Folder icon
            node.filter(d => d.type === 'folder')
                .append('text')
                .attr('dy', 4)
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('font-size', d => getNodeSize(d) * 0.7)
                .text('📁');
            
            // File icon/label based on metrics
            node.filter(d => d.type === 'file')
                .append('text')
                .attr('dy', 4)
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('font-size', d => Math.max(8, getNodeSize(d) * 0.6))
                .text(d => {
                    if (sizeMode === 'fanIn' && d.fanIn > 0) return d.fanIn;
                    if (sizeMode === 'fanOut' && d.fanOut > 0) return d.fanOut;
                    if (d.language?.includes('TypeScript')) return 'TS';
                    if (d.language?.includes('JavaScript')) return 'JS';
                    if (d.language === 'Python') return 'PY';
                    return '';
                });
            
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => {
                        // Shorten line to not overlap with target node
                        const dx = d.target.x - d.source.x;
                        const dy = d.target.y - d.source.y;
                        const dist = Math.sqrt(dx*dx + dy*dy);
                        const targetR = getNodeSize(d.target);
                        return d.target.x - (dx/dist) * (targetR + 5);
                    })
                    .attr('y2', d => {
                        const dx = d.target.x - d.source.x;
                        const dy = d.target.y - d.source.y;
                        const dist = Math.sqrt(dx*dx + dy*dy);
                        const targetR = getNodeSize(d.target);
                        return d.target.y - (dy/dist) * (targetR + 5);
                    });
                
                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });
            
            // Restore selection visual state
            updateSelection();
            
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
        }
        
        function updateSelection() {
            // Update node selection class
            g.selectAll('.node')
                .classed('selected', d => selectedNode && d.id === selectedNode.id);
            
            // Update link visibility - only show links connected to selected node
            g.selectAll('.link')
                .classed('visible', d => {
                    if (!selectedNode) return false;
                    const sourceId = d.source.id || d.source;
                    const targetId = d.target.id || d.target;
                    return sourceId === selectedNode.id || targetId === selectedNode.id;
                })
                .classed('inbound', d => {
                    if (!selectedNode) return false;
                    const targetId = d.target.id || d.target;
                    return targetId === selectedNode.id;
                })
                .classed('outbound', d => {
                    if (!selectedNode) return false;
                    const sourceId = d.source.id || d.source;
                    return sourceId === selectedNode.id;
                })
                .attr('marker-end', d => {
                    if (!selectedNode) return 'url(#arrowhead)';
                    const sourceId = d.source.id || d.source;
                    const targetId = d.target.id || d.target;
                    if (targetId === selectedNode.id) return 'url(#arrowhead-inbound)';
                    if (sourceId === selectedNode.id) return 'url(#arrowhead-outbound)';
                    return 'url(#arrowhead)';
                });
        }
        
        function updateDetailsPanel() {
            if (!selectedNode) {
                document.getElementById('details-panel').innerHTML = 
                    '<div class="placeholder">Click on a node to view details</div>';
            }
        }
        
        function showDetails(node) {
            const panel = document.getElementById('details-panel');
            
            if (node.type === 'folder') {
                const children = (node.children || []).map(id => nodesById.get(id)).filter(Boolean);
                const folders = children.filter(c => c.type === 'folder');
                const files = children.filter(c => c.type === 'file');
                
                panel.innerHTML = `
                    <div class="sidebar-section">
                        <div class="sidebar-title">Folder</div>
                        <div class="file-info">
                            <div class="file-name">📁 ${node.name}</div>
                            <div class="file-path">${node.path || '/'}</div>
                            <div class="file-meta">
                                <div class="meta-item">
                                    <div class="meta-label">Files</div>
                                    <div class="meta-value">${node.fileCount || 0}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Code Files</div>
                                    <div class="meta-value">${node.codeFiles || 0}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="sidebar-section">
                        <div class="sidebar-title">Contents (${children.length})</div>
                        <div class="folder-contents">
                            ${folders.map(f => `
                                <div class="folder-item" onclick="navigateTo('${f.path || f.id}'); showDetails(nodesById.get('${f.path || f.id}'))">
                                    <span class="folder-icon">📁</span>
                                    <span class="item-name">${f.name}</span>
                                    <span class="item-meta">${f.fileCount || 0}</span>
                                </div>
                            `).join('')}
                            ${files.slice(0, 15).map(f => `
                                <div class="folder-item" onclick="selectedNode = nodesById.get('${f.path}'); updateSelection(); showDetails(nodesById.get('${f.path}'))">
                                    <span class="folder-icon">📄</span>
                                    <span class="item-name">${f.name}</span>
                                    <span class="item-meta">${f.fanIn || 0}⬅ ${f.fanOut || 0}➡</span>
                                </div>
                            `).join('')}
                            ${files.length > 15 ? `<div class="folder-item" style="color:#666">...and ${files.length - 15} more files</div>` : ''}
                        </div>
                    </div>
                `;
            } else {
                const dependents = node.dependents || [];
                const dependencies = node.dependencies || [];
                const imports = node.imports || [];
                
                panel.innerHTML = `
                    <div class="sidebar-section">
                        <div class="sidebar-title">File Details</div>
                        <div class="file-info">
                            <div class="file-name">📄 ${node.name}</div>
                            <div class="file-path">${node.path}</div>
                            <div class="file-meta four-col">
                                <div class="meta-item">
                                    <div class="meta-label">Language</div>
                                    <div class="meta-value">${node.language}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Lines</div>
                                    <div class="meta-value">${node.loc?.toLocaleString() || 0}</div>
                                </div>
                                <div class="meta-item highlight">
                                    <div class="meta-label">Fan-In</div>
                                    <div class="meta-value purple">${node.fanIn || 0}</div>
                                </div>
                                <div class="meta-item highlight">
                                    <div class="meta-label">Fan-Out</div>
                                    <div class="meta-value orange">${node.fanOut || 0}</div>
                                </div>
                            </div>
                            
                            ${dependents.length > 0 ? `
                                <div class="deps-section">
                                    <div class="deps-title">
                                        <span style="color:#00d4aa">⬅</span>
                                        Files that import this (<span class="count">${dependents.length}</span>)
                                    </div>
                                    ${dependents.slice(0, 8).map(d => `
                                        <div class="dep-item inbound" onclick="focusFile('${d}')">
                                            <span class="arrow">⬅</span>
                                            <span class="name" title="${d}">${d.split('/').pop()}</span>
                                        </div>
                                    `).join('')}
                                    ${dependents.length > 8 ? `<div class="empty-state">+${dependents.length - 8} more</div>` : ''}
                                </div>
                            ` : ''}
                            
                            ${dependencies.length > 0 ? `
                                <div class="deps-section">
                                    <div class="deps-title">
                                        <span style="color:#f59e0b">➡</span>
                                        Files this imports (<span class="count">${dependencies.length}</span>)
                                    </div>
                                    ${dependencies.slice(0, 8).map(d => `
                                        <div class="dep-item outbound" onclick="focusFile('${d}')">
                                            <span class="arrow">➡</span>
                                            <span class="name" title="${d}">${d.split('/').pop()}</span>
                                        </div>
                                    `).join('')}
                                    ${dependencies.length > 8 ? `<div class="empty-state">+${dependencies.length - 8} more</div>` : ''}
                                </div>
                            ` : ''}
                            
                            ${imports.length > 0 && dependencies.length === 0 ? `
                                <div class="imports-list">
                                    <div class="imports-title">Raw Imports (${imports.length})</div>
                                    ${imports.slice(0, 10).map(i => `<div class="import-item">${i}</div>`).join('')}
                                    ${imports.length > 10 ? `<div class="import-item" style="color:#666">...and ${imports.length - 10} more</div>` : ''}
                                </div>
                            ` : ''}
                            
                            ${dependents.length === 0 && dependencies.length === 0 ? `
                                <div class="empty-state" style="margin-top: 16px;">
                                    No resolved dependencies in this view.<br>
                                    <span style="font-size: 10px; color: #444;">
                                        (External packages or unresolved paths)
                                    </span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }
        }
        
        // Initial render
        renderGraph();
    </script>
</body>
</html>'''
    
    return html


def main():
    parser = argparse.ArgumentParser(description='Visualize codebase structure')
    parser.add_argument('path', nargs='?', default='.', help='Path to repository')
    args = parser.parse_args()
    
    repo_path = Path(args.path).resolve()
    if not repo_path.exists():
        print(f"Error: Path '{repo_path}' does not exist")
        return 1
        
    print("🔮 Codebase Visualizer")
    print("=" * 40)
    
    analyzer = CodebaseAnalyzer(str(repo_path))
    data = analyzer.analyze()
    
    print(f"📈 Computed metrics for {len(analyzer.fan_in)} files")
    print(f"   Total dependencies: {data['stats']['totalDependencies']}")
    if data['hotspots']:
        print(f"   Top hotspot: {data['hotspots'][0]['name']} (fan-in: {data['hotspots'][0]['fanIn']})")
    
    print("🎨 Generating visualization...")
    html = generate_html(data)
    
    # Write to temp file and open
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        temp_path = f.name
    
    print(f"📊 Opening visualization in browser...")
    print(f"   (File: {temp_path})")
    webbrowser.open(f'file://{temp_path}')
    
    print("\n✨ Done! Explore your codebase visually.")
    print("   - Click nodes to see dependency edges")
    print("   - Check Hotspots panel for most important files")
    print("   - Use Size/Color controls to visualize metrics")
    return 0


if __name__ == '__main__':
    exit(main())
