"""
Node Scanner Module
Scans the Nodes folder and extracts metadata from Python node files using AST.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional


# Known base node types
NODE_BASE_TYPES = {
    'BlockingNode', 'NonBlockingNode', 'ProducerNode', 'LogicalNode', 
    'BaseNode', 'QueueNode', 'QueueReader'
}


def extract_identifier_from_method(node: ast.FunctionDef) -> Optional[str]:
    """
    Extract the return value from an identifier() classmethod.
    """
    for stmt in node.body:
        if isinstance(stmt, ast.Return) and stmt.value:
            if isinstance(stmt.value, ast.Constant):
                return stmt.value.value
    return None


def extract_class_metadata(class_node: ast.ClassDef) -> Optional[Dict]:
    """
    Extract metadata from a class definition.
    Returns dict with name, identifier, and base type.
    """
    # Get base class names
    base_names = []
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            base_names.append(base.id)
        elif isinstance(base, ast.Attribute):
            base_names.append(base.attr)
    
    # Check if this class inherits from a known node type
    node_type = None
    for base in base_names:
        if base in NODE_BASE_TYPES:
            node_type = base
            break
    
    if not node_type:
        return None
    
    # Look for identifier() method
    identifier = None
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef) and item.name == 'identifier':
            identifier = extract_identifier_from_method(item)
            break
    
    return {
        'name': class_node.name,
        'identifier': identifier or class_node.name.lower(),
        'type': node_type
    }


def scan_python_file(file_path: Path) -> List[Dict]:
    """
    Scan a Python file and extract all node class metadata.
    """
    nodes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                metadata = extract_class_metadata(node)
                if metadata:
                    metadata['file'] = file_path.name
                    metadata['file_path'] = str(file_path)
                    nodes.append(metadata)
    
    except (SyntaxError, FileNotFoundError, PermissionError) as e:
        print(f"Error scanning {file_path}: {e}")
    
    return nodes


def scan_nodes_folder(nodes_path: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    Scan the Nodes folder and return all nodes grouped by category.
    
    Returns:
        Dict with category names as keys and lists of node metadata as values.
    """
    if nodes_path is None:
        # Default path relative to this file
        base_dir = Path(__file__).parent.parent
        nodes_path = base_dir / 'Node' / 'Nodes'
    else:
        nodes_path = Path(nodes_path)
    
    if not nodes_path.exists():
        return {}
    
    grouped_nodes = {}
    
    # Iterate through subdirectories (categories)
    for category_dir in nodes_path.iterdir():
        if not category_dir.is_dir():
            continue
        
        category_name = category_dir.name
        
        # Skip __pycache__ and other hidden directories
        if category_name.startswith('_') or category_name.startswith('.'):
            continue
        
        category_nodes = []
        
        # Scan all Python files in this category
        for py_file in category_dir.glob('*.py'):
            # Skip __init__.py
            if py_file.name == '__init__.py':
                continue
            
            nodes = scan_python_file(py_file)
            category_nodes.extend(nodes)
        
        if category_nodes:
            grouped_nodes[category_name] = category_nodes
    
    return grouped_nodes


def get_all_nodes_flat() -> List[Dict]:
    """
    Get all nodes as a flat list with category included.
    """
    grouped = scan_nodes_folder()
    flat_list = []
    
    for category, nodes in grouped.items():
        for node in nodes:
            node_copy = node.copy()
            node_copy['category'] = category
            flat_list.append(node_copy)
    
    return flat_list


def get_node_count() -> int:
    """
    Get total count of all nodes.
    """
    grouped = scan_nodes_folder()
    return sum(len(nodes) for nodes in grouped.values())


if __name__ == '__main__':
    # Test the scanner
    import json
    nodes = scan_nodes_folder()
    print(json.dumps(nodes, indent=2))
