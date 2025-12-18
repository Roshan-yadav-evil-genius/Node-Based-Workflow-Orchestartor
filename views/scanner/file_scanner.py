"""
File Scanner Module
Scans individual Python files for node class definitions.
"""

import ast
from pathlib import Path
from typing import Dict, List

from .metadata_extractor import MetadataExtractor


class FileScanner:
    """
    Scans Python files and extracts node metadata.
    
    Responsibilities:
    - Read and parse Python files
    - Use MetadataExtractor to extract class metadata
    - Handle file I/O errors gracefully
    """
    
    def __init__(self, extractor: MetadataExtractor):
        """
        Initialize FileScanner with a metadata extractor.
        
        Args:
            extractor: MetadataExtractor instance for extracting class metadata.
        """
        self._extractor = extractor
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """
        Scan a Python file and extract all node class metadata.
        
        Args:
            file_path: Path to the Python file to scan.
            
        Returns:
            List of node metadata dictionaries found in the file.
        """
        nodes = []
        
        try:
            source = self._read_file(file_path)
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metadata = self._extractor.extract_from_class(node)
                    if metadata:
                        metadata['file'] = file_path.name
                        metadata['file_path'] = str(file_path)
                        nodes.append(metadata)
        
        except (SyntaxError, FileNotFoundError, PermissionError) as e:
            print(f"Error scanning {file_path}: {e}")
        
        return nodes
    
    def _read_file(self, file_path: Path) -> str:
        """
        Read file contents with UTF-8 encoding.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

