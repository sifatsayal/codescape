"""
Import parser module.

Extracts imports from various programming languages.
"""

import re
from typing import List
from pathlib import Path


class ImportParser:
    """Base class for language-specific import parsers."""
    
    def parse(self, content: str, file_path: Path) -> List[str]:
        """
        Parse imports from file content.
        
        Args:
            content: File content as string
            file_path: Path to the file (for context)
            
        Returns:
            List of import paths/names
        """
        raise NotImplementedError


class JSParser(ImportParser):
    """Parser for JavaScript/TypeScript imports (ESM and CommonJS)."""
    
    def parse(self, content: str, file_path: Path) -> List[str]:
        """Extract JavaScript/TypeScript imports."""
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


class PythonParser(ImportParser):
    """Parser for Python imports."""
    
    def parse(self, content: str, file_path: Path) -> List[str]:
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


class GoParser(ImportParser):
    """Parser for Go imports."""
    
    def parse(self, content: str, file_path: Path) -> List[str]:
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


def get_parser_for_file(file_path: Path, extension: str) -> ImportParser:
    """
    Get appropriate parser for a file based on its extension.
    
    Args:
        file_path: Path to the file
        extension: File extension (e.g., '.ts', '.py')
        
    Returns:
        ImportParser instance or None if no parser available
    """
    js_extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.vue', '.svelte']
    
    if extension in js_extensions:
        return JSParser()
    elif extension == '.py':
        return PythonParser()
    elif extension == '.go':
        return GoParser()
    
    return None


def extract_imports_from_files(files: dict, root: Path, config) -> dict:
    """
    Extract imports from all code files.
    
    Args:
        files: Dictionary of file info (from scanner)
        root: Root path of repository
        config: VisualizerConfig instance
        
    Returns:
        Dictionary mapping file paths to lists of imports
    """
    imports = {}
    
    for path, info in files.items():
        if not info.get('is_code'):
            continue
        
        ext = info['extension']
        full_path = root / path
        
        try:
            if full_path.stat().st_size > 200000:  # Skip large files
                continue
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        
        parser = get_parser_for_file(full_path, ext)
        if parser:
            parsed_imports = parser.parse(content, full_path)
            info['imports'] = parsed_imports[:30]  # Limit imports shown
            imports[path] = parsed_imports
    
    return imports
