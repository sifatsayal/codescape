#!/usr/bin/env python3
"""
Codebase Visualizer - A visual exploration tool for understanding code structure.

This script scans a local repository, extracts file/folder structure and import
relationships, then generates an interactive D3.js visualization that opens
in your browser.

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


class CodebaseAnalyzer:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.files: Dict[str, dict] = {}
        self.folders: Dict[str, dict] = {}
        self.imports: Dict[str, List[str]] = defaultdict(list)
        self.file_count = 0
        
    def analyze(self) -> dict:
        """Analyze the codebase and return structured data."""
        print(f"📂 Scanning: {self.root}")
        self._scan_directory(self.root, depth=0)
        print(f"✅ Found {len(self.files)} files in {len(self.folders)} folders")
        
        print("🔍 Extracting imports...")
        self._extract_all_imports()
        
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
            if ext in ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.vue', '.svelte']:
                imports = self._extract_js_imports(content)
            elif ext == '.py':
                imports = self._extract_python_imports(content)
            elif ext == '.go':
                imports = self._extract_go_imports(content)
                
            info['imports'] = imports[:20]  # Limit imports shown
            self.imports[path] = imports
    
    def _extract_js_imports(self, content: str) -> List[str]:
        """Extract JavaScript/TypeScript imports."""
        imports = []
        
        # import ... from '...'
        pattern1 = r"import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+\w+|\w+))*\s+from\s+)?['\"]([^'\"]+)['\"]"
        # require('...')
        pattern2 = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        
        for match in re.finditer(pattern1, content):
            imports.append(match.group(1))
        for match in re.finditer(pattern2, content):
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
        
        # Add file nodes (only for top-level initially)
        for path, info in self.files.items():
            nodes.append({
                'id': path,
                'name': info['name'],
                'type': 'file',
                'path': path,
                'language': info['language'],
                'extension': info['extension'],
                'loc': info['loc'],
                'imports': info['imports'],
            })
            
            # Create links for local imports
            for imp in info['imports']:
                if imp.startswith('.'):
                    # Resolve relative import
                    target = self._resolve_import(path, imp)
                    if target and target in self.files:
                        links.append({
                            'source': path,
                            'target': target,
                            'type': 'import'
                        })
        
        return {
            'nodes': nodes,
            'links': links,
            'rootName': self.root.name,
            'stats': {
                'totalFiles': len(self.files),
                'totalFolders': len(self.folders),
                'codeFiles': sum(1 for f in self.files.values() if f.get('is_code')),
                'totalLoc': sum(f.get('loc', 0) for f in self.files.values()),
            }
        }
    
    def _resolve_import(self, from_file: str, import_path: str) -> Optional[str]:
        """Resolve a relative import to an actual file path."""
        from_dir = str(Path(from_file).parent)
        
        # Handle relative paths
        if import_path.startswith('./'):
            resolved = str(Path(from_dir) / import_path[2:])
        elif import_path.startswith('../'):
            resolved = str((Path(from_dir) / import_path).resolve().relative_to(self.root.resolve()))
        else:
            return None
            
        # Try common extensions
        for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx', '/index.js']:
            test_path = resolved + ext
            if test_path in self.files:
                return test_path
                
        return None


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
            right: 350px;
            bottom: 0;
        }
        
        #sidebar {
            position: fixed;
            top: 60px;
            right: 0;
            width: 350px;
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
        
        .meta-item {
            background: rgba(20, 20, 35, 0.6);
            padding: 10px 12px;
            border-radius: 8px;
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
            stroke-opacity: 0.3;
        }
        
        .link.import {
            stroke: #7c3aed;
            stroke-dasharray: 4,2;
        }
        
        .link.contains {
            stroke: #333;
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
        
        #help {
            position: fixed;
            bottom: 20px;
            right: 370px;
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
                <span>Folders:</span>
                <span class="stat-value">''' + str(data['stats']['totalFolders']) + '''</span>
            </div>
            <div class="stat">
                <span>LOC:</span>
                <span class="stat-value">''' + f"{data['stats']['totalLoc']:,}" + '''</span>
            </div>
        </div>
        <div class="breadcrumb" id="breadcrumb">
            <span class="breadcrumb-item" onclick="navigateTo('')">''' + data['rootName'] + '''</span>
        </div>
    </div>
    
    <div id="graph-container">
        <svg id="graph"></svg>
    </div>
    
    <div id="sidebar">
        <div class="placeholder">Click on a node to view details</div>
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
        <div class="legend-item">
            <div class="legend-circle" style="background: #3b82f6;"></div>
            <span>Other Code</span>
        </div>
    </div>
    
    <div id="help">
        <span class="help-key">Scroll</span> to zoom
        <span class="help-key">Drag</span> to pan
        <span class="help-key">Click</span> nodes to explore
    </div>

    <script>
        const graphData = ''' + json.dumps(data) + ''';
        
        // Build lookup maps
        const nodesById = new Map(graphData.nodes.map(n => [n.id, n]));
        
        let currentPath = '';
        let simulation = null;
        
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
        
        // Color scale for languages
        function getNodeColor(node) {
            if (node.type === 'folder') return '#7c3aed';
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
            return Math.min(20, 6 + Math.sqrt(node.loc || 1) * 0.3);
        }
        
        function navigateTo(path) {
            currentPath = path;
            updateBreadcrumb();
            renderGraph();
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
            
            // Get links between visible nodes
            const visibleLinks = graphData.links.filter(l => 
                visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target)
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
                .force('link', d3.forceLink(visibleLinks).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(d => getNodeSize(d) + 20));
            
            // Draw links
            const link = g.append('g')
                .selectAll('line')
                .data(visibleLinks)
                .join('line')
                .attr('class', d => `link ${d.type}`)
                .attr('stroke-width', 1.5);
            
            // Draw nodes
            const node = g.append('g')
                .selectAll('g')
                .data(visibleNodes)
                .join('g')
                .attr('class', 'node')
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended))
                .on('click', (event, d) => {
                    event.stopPropagation();
                    if (d.type === 'folder') {
                        navigateTo(d.path || d.id);
                    }
                    showDetails(d);
                });
            
            node.append('circle')
                .attr('r', d => getNodeSize(d))
                .attr('fill', d => getNodeColor(d))
                .attr('stroke', d => d3.color(getNodeColor(d)).darker(0.5));
            
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
            
            // File icon based on language
            node.filter(d => d.type === 'file')
                .append('text')
                .attr('dy', 4)
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('font-size', d => getNodeSize(d) * 0.8)
                .text(d => {
                    if (d.language?.includes('TypeScript')) return 'TS';
                    if (d.language?.includes('JavaScript')) return 'JS';
                    if (d.language === 'Python') return 'PY';
                    return '';
                });
            
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });
            
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
        
        function showDetails(node) {
            const sidebar = document.getElementById('sidebar');
            
            if (node.type === 'folder') {
                const children = (node.children || []).map(id => nodesById.get(id)).filter(Boolean);
                const folders = children.filter(c => c.type === 'folder');
                const files = children.filter(c => c.type === 'file');
                
                sidebar.innerHTML = `
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
                            ${files.slice(0, 20).map(f => `
                                <div class="folder-item" onclick="showDetails(nodesById.get('${f.path}'))">
                                    <span class="folder-icon">📄</span>
                                    <span class="item-name">${f.name}</span>
                                    <span class="item-meta">${f.loc || 0} LOC</span>
                                </div>
                            `).join('')}
                            ${files.length > 20 ? `<div class="folder-item" style="color:#666">...and ${files.length - 20} more files</div>` : ''}
                        </div>
                    </div>
                `;
            } else {
                const imports = node.imports || [];
                sidebar.innerHTML = `
                    <div class="sidebar-section">
                        <div class="sidebar-title">File</div>
                        <div class="file-info">
                            <div class="file-name">📄 ${node.name}</div>
                            <div class="file-path">${node.path}</div>
                            <div class="file-meta">
                                <div class="meta-item">
                                    <div class="meta-label">Language</div>
                                    <div class="meta-value">${node.language}</div>
                                </div>
                                <div class="meta-item">
                                    <div class="meta-label">Lines</div>
                                    <div class="meta-value">${node.loc?.toLocaleString() || 0}</div>
                                </div>
                            </div>
                            ${imports.length > 0 ? `
                                <div class="imports-list">
                                    <div class="imports-title">Imports (${imports.length})</div>
                                    ${imports.slice(0, 15).map(i => `<div class="import-item">${i}</div>`).join('')}
                                    ${imports.length > 15 ? `<div class="import-item" style="color:#666">...and ${imports.length - 15} more</div>` : ''}
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
    return 0


if __name__ == '__main__':
    exit(main())
