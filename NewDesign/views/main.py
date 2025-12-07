"""
Flask Server for Node Engine POC
Provides a web interface to view all available nodes.
"""

from flask import Flask, render_template, jsonify
from .node_scanner import scan_nodes_folder, get_all_nodes_flat, get_node_count

app = Flask(__name__, template_folder='templates')


@app.route('/')
def index():
    """
    Render the main page with all nodes grouped by category.
    """
    nodes = scan_nodes_folder()
    total_count = sum(len(n) for n in nodes.values())
    return render_template('index.html', nodes=nodes, total_count=total_count)


@app.route('/api/nodes')
def api_nodes():
    """
    API endpoint to get all nodes as JSON.
    Returns nodes grouped by category.
    """
    nodes = scan_nodes_folder()
    return jsonify(nodes)


@app.route('/api/nodes/flat')
def api_nodes_flat():
    """
    API endpoint to get all nodes as a flat list.
    """
    nodes = get_all_nodes_flat()
    return jsonify(nodes)


@app.route('/api/nodes/count')
def api_nodes_count():
    """
    API endpoint to get total node count.
    """
    count = get_node_count()
    return jsonify({'count': count})


def run_server(host='0.0.0.0', port=5000, debug=True):
    """
    Run the Flask development server.
    """
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()

