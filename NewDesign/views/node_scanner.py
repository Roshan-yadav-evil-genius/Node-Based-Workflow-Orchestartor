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


def extract_string_from_return(node: ast.FunctionDef) -> Optional[str]:
    """
    Extract the string return value from a method.
    """
    for stmt in node.body:
        if isinstance(stmt, ast.Return) and stmt.value:
            if isinstance(stmt.value, ast.Constant):
                return stmt.value.value
    return None


def extract_form_class_name(class_node: ast.ClassDef) -> Optional[str]:
    """
    Extract form class name from get_form() method.
    Looks for: return FormClassName()
    """
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef) and item.name == 'get_form':
            for stmt in item.body:
                if isinstance(stmt, ast.Return) and stmt.value:
                    # Handle: return FormClass()
                    if isinstance(stmt.value, ast.Call):
                        if isinstance(stmt.value.func, ast.Name):
                            return stmt.value.func.id
    return None


def extract_property_string(class_node: ast.ClassDef, prop_name: str) -> Optional[str]:
    """
    Extract a string value from a property definition.
    Handles both @property decorated methods and simple return statements.
    """
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef) and item.name == prop_name:
            # Check if it's a property (has @property decorator)
            for decorator in item.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == 'property':
                    return extract_string_from_return(item)
    return None


def extract_class_metadata(class_node: ast.ClassDef) -> Optional[Dict]:
    """
    Extract metadata from a class definition.
    Returns dict with name, identifier, base type, form info, and properties.
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
            identifier = extract_string_from_return(item)
            break
    
    # Extract form class name
    form_class = extract_form_class_name(class_node)
    
    # Extract label and description properties
    label = extract_property_string(class_node, 'label')
    description = extract_property_string(class_node, 'description')
    
    return {
        'name': class_node.name,
        'identifier': identifier or class_node.name.lower(),
        'type': node_type,
        'has_form': form_class is not None,
        'form_class': form_class,
        'label': label,
        'description': description
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


def scan_directory_recursive(directory: Path) -> Dict:
    """
    Recursively scan a directory and build a hierarchical tree structure.
    Scans all folders no matter how deep they are nested.
    
    Returns:
        Dict with 'nodes' (list of node metadata) and 'subfolders' (dict of subdirectories).
    """
    result = {
        'nodes': [],
        'subfolders': {}
    }
    
    # Scan Python files directly in this directory
    for item in directory.iterdir():
        if item.is_file() and item.suffix == '.py':
            # Skip __init__.py
            if item.name == '__init__.py':
                continue
            
            nodes = scan_python_file(item)
            result['nodes'].extend(nodes)
    
    # Recursively scan ALL subdirectories (no matter how deep)
    for subdir in directory.iterdir():
        if not subdir.is_dir():
            continue
        
        subdir_name = subdir.name
        
        # Skip __pycache__ and other hidden directories
        if subdir_name.startswith('_') or subdir_name.startswith('.'):
            continue
        
        # Always include subfolder - scan recursively no matter how deep
        subfolder_result = scan_directory_recursive(subdir)
        result['subfolders'][subdir_name] = subfolder_result
    
    return result


def scan_nodes_folder(nodes_path: Optional[str] = None) -> Dict[str, Dict]:
    """
    Scan the Nodes folder and return all nodes in a hierarchical tree structure.
    
    Returns:
        Dict with category names as keys and nested structure as values.
        Each value contains 'nodes' (list) and 'subfolders' (dict).
        
    Example:
        {
            "Playwright": {
                "nodes": [],
                "subfolders": {
                    "Freelancer": {
                        "nodes": [{"name": "Bidder", ...}],
                        "subfolders": {}
                    }
                }
            }
        }
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
    
    # Iterate through top-level subdirectories (categories)
    for category_dir in nodes_path.iterdir():
        if not category_dir.is_dir():
            continue
        
        category_name = category_dir.name
        
        # Skip __pycache__ and other hidden directories
        if category_name.startswith('_') or category_name.startswith('.'):
            continue
        
        # Always include all categories - scan recursively no matter how deep
        category_result = scan_directory_recursive(category_dir)
        grouped_nodes[category_name] = category_result
    
    # Prune empty subfolders from each category
    pruned_nodes = {}
    for category_name, category_data in grouped_nodes.items():
        pruned = prune_empty_folders(category_data)
        if _count_nodes_recursive(pruned) > 0:
            pruned_nodes[category_name] = pruned
    
    return pruned_nodes


def _collect_nodes_recursive(folder_data: Dict, category_path: str, flat_list: List[Dict]):
    """
    Helper function to recursively collect nodes from hierarchical structure.
    """
    # Add nodes from current folder
    for node in folder_data['nodes']:
        node_copy = node.copy()
        node_copy['category'] = category_path
        flat_list.append(node_copy)
    
    # Recursively process subfolders
    for subfolder_name, subfolder_data in folder_data['subfolders'].items():
        subfolder_path = f"{category_path}/{subfolder_name}"
        _collect_nodes_recursive(subfolder_data, subfolder_path, flat_list)


def get_all_nodes_flat() -> List[Dict]:
    """
    Get all nodes as a flat list with category path included.
    """
    grouped = scan_nodes_folder()
    flat_list = []
    
    for category, folder_data in grouped.items():
        _collect_nodes_recursive(folder_data, category, flat_list)
    
    return flat_list


def _count_nodes_recursive(folder_data: Dict) -> int:
    """
    Helper function to recursively count nodes from hierarchical structure.
    """
    count = len(folder_data['nodes'])
    for subfolder_data in folder_data['subfolders'].values():
        count += _count_nodes_recursive(subfolder_data)
    return count


def prune_empty_folders(folder_data: Dict) -> Dict:
    """
    Recursively remove subfolders that contain no nodes.
    Returns a new dict with empty subfolders pruned.
    """
    pruned_subfolders = {}
    
    for subfolder_name, subfolder_data in folder_data['subfolders'].items():
        # First, recursively prune the subfolder
        pruned_subfolder = prune_empty_folders(subfolder_data)
        
        # Only keep if it has nodes (directly or in nested subfolders)
        if _count_nodes_recursive(pruned_subfolder) > 0:
            pruned_subfolders[subfolder_name] = pruned_subfolder
    
    return {
        'nodes': folder_data['nodes'],
        'subfolders': pruned_subfolders
    }


def get_node_count() -> int:
    """
    Get total count of all nodes.
    """
    grouped = scan_nodes_folder()
    total = 0
    for folder_data in grouped.values():
        total += _count_nodes_recursive(folder_data)
    return total


if __name__ == '__main__':
    # Test the scanner
    import json
    nodes = scan_nodes_folder()
    print(json.dumps(nodes, indent=2))
