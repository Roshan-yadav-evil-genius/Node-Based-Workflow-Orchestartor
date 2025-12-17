"""
Pages Routes Module
HTML page routes for the web interface.
"""

from flask import Blueprint, render_template, current_app

from ..scanner import count_nodes


pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    """
    Render the main page with all nodes grouped by category.
    """
    services = current_app.extensions['services']
    nodes = services.node_registry.get_all_nodes()
    
    # Calculate total count
    total_count = 0
    for folder_data in nodes.values():
        total_count += count_nodes(folder_data)
    
    return render_template('index.html', nodes=nodes, total_count=total_count)

