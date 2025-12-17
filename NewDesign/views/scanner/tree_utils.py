"""
Tree Utilities Module
Pure functions for operating on the folder/node tree structure.
"""

from typing import Dict, List


def count_nodes(folder_data: Dict) -> int:
    """
    Recursively count all nodes in a folder structure.
    
    Args:
        folder_data: Dict with 'nodes' list and 'subfolders' dict.
        
    Returns:
        Total count of nodes including all nested subfolders.
    """
    count = len(folder_data['nodes'])
    
    for subfolder_data in folder_data['subfolders'].values():
        count += count_nodes(subfolder_data)
    
    return count


def prune_empty_folders(folder_data: Dict) -> Dict:
    """
    Recursively remove subfolders that contain no nodes.
    
    Args:
        folder_data: Dict with 'nodes' list and 'subfolders' dict.
        
    Returns:
        New dict with empty subfolders pruned.
    """
    pruned_subfolders = {}
    
    for subfolder_name, subfolder_data in folder_data['subfolders'].items():
        # First, recursively prune the subfolder
        pruned_subfolder = prune_empty_folders(subfolder_data)
        
        # Only keep if it has nodes (directly or in nested subfolders)
        if count_nodes(pruned_subfolder) > 0:
            pruned_subfolders[subfolder_name] = pruned_subfolder
    
    return {
        'nodes': folder_data['nodes'],
        'subfolders': pruned_subfolders
    }


def flatten_nodes(folder_data: Dict, category_path: str = '') -> List[Dict]:
    """
    Flatten a hierarchical folder structure into a flat list of nodes.
    
    Args:
        folder_data: Dict with 'nodes' list and 'subfolders' dict.
        category_path: Current path in the hierarchy (for categorization).
        
    Returns:
        Flat list of node metadata with 'category' field added.
    """
    flat_list = []
    
    # Add nodes from current folder
    for node in folder_data['nodes']:
        node_copy = node.copy()
        node_copy['category'] = category_path
        flat_list.append(node_copy)
    
    # Recursively process subfolders
    for subfolder_name, subfolder_data in folder_data['subfolders'].items():
        subfolder_path = f"{category_path}/{subfolder_name}" if category_path else subfolder_name
        flat_list.extend(flatten_nodes(subfolder_data, subfolder_path))
    
    return flat_list

