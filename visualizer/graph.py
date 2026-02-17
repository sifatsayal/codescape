"""
Dependency graph builder and metrics computation.

Builds file-to-file dependency graphs and computes metrics like fan-in, fan-out, and PageRank.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict

from .config import VisualizerConfig


class DependencyGraph:
    """Builds dependency graph and computes metrics."""
    
    def __init__(self, config: VisualizerConfig, files: Dict, folders: Dict, imports: Dict):
        """
        Initialize graph builder.
        
        Args:
            config: VisualizerConfig instance
            files: Dictionary of file info (from scanner)
            folders: Dictionary of folder info (from scanner)
            imports: Dictionary mapping file paths to lists of raw imports
        """
        self.config = config
        self.root = config.repo_path
        self.files = files
        self.folders = folders
        self.imports = imports
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        self.fan_in: Dict[str, int] = {}
        self.fan_out: Dict[str, int] = {}
        self.pagerank: Dict[str, float] = {}
    
    def build(self) -> dict:
        """
        Build dependency graph and compute metrics.
        
        Returns:
            Graph data structure for visualization
        """
        print("📊 Computing dependency metrics...")
        self._compute_dependency_graph()
        self._compute_metrics()
        return self._build_graph_data()
    
    def _compute_dependency_graph(self):
        """Build the file-to-file dependency graph from resolved imports."""
        for source_path, raw_imports in self.imports.items():
            for imp in raw_imports:
                target = self._resolve_import(source_path, imp)
                if target and target in self.files and target != source_path:
                    self.dependencies[source_path].add(target)
                    self.dependents[target].add(source_path)
    
    def _resolve_import(self, from_file: str, import_path: str) -> Optional[str]:
        """
        Resolve an import to an actual file path in the codebase.
        
        Uses config.source_dirs instead of hardcoded list.
        """
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
        # Use config.source_dirs instead of hardcoded list
        for src_dir in self.config.source_dirs:
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
                for src_dir in self.config.source_dirs:
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
        
        for _ in range(self.config.pagerank_iterations):
            new_rank = {}
            for path in self.files:
                # Sum of rank from incoming edges (dependents)
                incoming_sum = 0.0
                for dep in self.dependents.get(path, set()):
                    out_degree = len(self.dependencies.get(dep, set()))
                    if out_degree > 0:
                        incoming_sum += rank.get(dep, 0) / out_degree
                
                new_rank[path] = (1 - self.config.pagerank_damping) / n + self.config.pagerank_damping * incoming_sum
            rank = new_rank
        
        self.pagerank = rank
    
    def _build_graph_data(self) -> dict:
        """Build data structure for D3 visualization."""
        nodes = []
        links = []
        
        def depth_from_path(path: str) -> int:
            """Depth = number of path segments (root = 0)."""
            return len([p for p in (path or '').split('/') if p])
        
        # Folder-level importance = sum of PageRank of all files in folder (recursively)
        folder_pagerank: Dict[str, float] = {}
        for folder_path in self.folders:
            total = 0.0
            for file_path in self.files:
                if folder_path == '' or file_path.startswith(folder_path + '/'):
                    total += self.pagerank.get(file_path, 0)
            folder_pagerank[folder_path] = total
        
        # Add folder nodes
        for path, info in self.folders.items():
            node_id = path or 'root'
            agg_pr = folder_pagerank.get(path, 0)
            nodes.append({
                'id': node_id,
                'name': info['name'],
                'type': 'folder',
                'path': path,
                'depth': depth_from_path(path),
                'fileCount': info['file_count'],
                'codeFiles': info['code_files'],
                'subfolderCount': info.get('subfolder_count', 0),
                'recursiveSubfolderCount': info.get('recursive_subfolder_count', 0),
                'directFileCount': info.get('direct_file_count', 0),
                'children': info['children'],
                'pagerank': round(agg_pr * 10000, 2),
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
                'depth': depth_from_path(path),
                'language': info['language'],
                'extension': info['extension'],
                'loc': info['loc'],
                'imports': info.get('imports', [])[:30],
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
        
        # Compute max values for normalization (files and folders use same PageRank scale)
        max_fan_in = max((self.fan_in.get(p, 0) for p in self.files), default=1) or 1
        max_fan_out = max((self.fan_out.get(p, 0) for p in self.files), default=1) or 1
        max_file_pr = max((self.pagerank.get(p, 0) for p in self.files), default=0)
        max_folder_pr = max(folder_pagerank.values(), default=0)
        max_pagerank = max(max_file_pr, max_folder_pr, 0.0001)
        
        max_depth = max((n.get('depth', 0) for n in nodes), default=0)
        
        return {
            'nodes': nodes,
            'links': links,
            'rootName': self.root.name,
            'hotspots': hotspots,
            'maxDepth': max_depth,
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
                'totalDependencies': len(links),
            },
        }
