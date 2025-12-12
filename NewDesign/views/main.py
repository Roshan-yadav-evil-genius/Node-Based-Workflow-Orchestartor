"""
Flask Server for Node Engine POC
Provides a web interface to view all available nodes.
"""

import importlib.util
import sys
import asyncio
import traceback
from flask import Flask, render_template, jsonify, request
from .node_scanner import scan_nodes_folder, get_all_nodes_flat, get_node_count

app = Flask(__name__, template_folder='templates')


def find_node_by_identifier(identifier: str):
    """
    Find a node by its identifier from the flat list.
    Returns the node metadata dict or None if not found.
    """
    nodes = get_all_nodes_flat()
    for node in nodes:
        if node.get('identifier') == identifier:
            return node
    return None


def load_form_from_node(node_metadata: dict):
    """
    Dynamically load a node module and get its form instance.
    Returns the serialized form JSON or None if no form.
    """
    file_path = node_metadata.get('file_path')
    node_class_name = node_metadata.get('name')
    
    if not file_path or not node_class_name:
        return None
    
    try:
        from pathlib import Path
        
        # Get the project root (NewDesign folder)
        project_root = Path(__file__).parent.parent
        
        # Convert file path to module path
        # e.g., "Node/Nodes/Delay/StaticDelayNode.py" -> "Node.Nodes.Delay.StaticDelayNode"
        file_path_obj = Path(file_path)
        relative_path = file_path_obj.relative_to(project_root)
        module_path = str(relative_path.with_suffix('')).replace('\\', '.').replace('/', '.')
        
        # Ensure project root is in sys.path
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)
        
        # Import using the full module path
        module = importlib.import_module(module_path)
        
        # Get the node class
        node_class = getattr(module, node_class_name, None)
        if node_class is None:
            return None
        
        # Check if the class has get_form method
        if not hasattr(node_class, 'get_form'):
            return None
        
        # Create a simple instance to call get_form
        from Node.Core.Node.Core.Data import NodeConfig, NodeConfigData
        
        dummy_config = NodeConfig(
            id="temp",
            type=node_metadata.get('identifier', 'unknown'),
            data=NodeConfigData(form={})
        )
        
        instance = node_class(dummy_config)
        form = instance.get_form()
        
        if form is None:
            return None
        
        # Serialize the form using FormSerializer
        from Node.Core.Form.Core.FormSerializer import FormSerializer
        serializer = FormSerializer(form)
        return serializer.to_json()
        
    except Exception as e:
        print(f"Error loading form from {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None


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


@app.route('/api/node/<identifier>/form')
def api_node_form(identifier):
    """
    API endpoint to get form JSON for a specific node.
    Returns the serialized form fields and metadata.
    """
    # Find the node by identifier
    node = find_node_by_identifier(identifier)
    
    if node is None:
        return jsonify({'error': 'Node not found', 'identifier': identifier}), 404
    
    # Check if node has a form
    if not node.get('has_form'):
        return jsonify({
            'node': {
                'name': node.get('name'),
                'identifier': node.get('identifier'),
                'type': node.get('type'),
                'label': node.get('label'),
                'description': node.get('description'),
            },
            'form': None,
            'message': 'This node does not have a form'
        })
    
    # Load and serialize the form
    form_json = load_form_from_node(node)
    
    return jsonify({
        'node': {
            'name': node.get('name'),
            'identifier': node.get('identifier'),
            'type': node.get('type'),
            'label': node.get('label'),
            'description': node.get('description'),
            'form_class': node.get('form_class'),
            'file_path': node.get('file_path'),
        },
        'form': form_json
    })


def load_node_class(node_metadata: dict):
    """
    Dynamically load a node class from its metadata.
    Returns the node class or None if not found.
    """
    file_path = node_metadata.get('file_path')
    node_class_name = node_metadata.get('name')
    
    if not file_path or not node_class_name:
        return None
    
    try:
        from pathlib import Path
        
        # Get the project root (NewDesign folder)
        project_root = Path(__file__).parent.parent
        
        # Convert file path to module path
        file_path_obj = Path(file_path)
        relative_path = file_path_obj.relative_to(project_root)
        module_path = str(relative_path.with_suffix('')).replace('\\', '.').replace('/', '.')
        
        # Ensure project root is in sys.path
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)
        
        # Import using the full module path
        module = importlib.import_module(module_path)
        
        # Get the node class
        node_class = getattr(module, node_class_name, None)
        return node_class
        
    except Exception as e:
        print(f"Error loading node class from {file_path}: {e}")
        traceback.print_exc()
        return None


@app.route('/api/node/<identifier>/execute', methods=['POST'])
def api_node_execute(identifier):
    """
    API endpoint to execute a node with given input data and form values.
    
    Request body:
    {
        "input_data": { ... },  # Data to pass as NodeOutput
        "form_data": { ... }    # Form field values
    }
    
    Returns the node execution output.
    """
    # Find the node by identifier
    node_metadata = find_node_by_identifier(identifier)
    
    if node_metadata is None:
        return jsonify({'error': 'Node not found', 'identifier': identifier}), 404
    
    # Get request data
    try:
        request_data = request.get_json()
    except Exception as e:
        return jsonify({'error': 'Invalid JSON in request body', 'details': str(e)}), 400
    
    if not request_data:
        return jsonify({'error': 'Request body is required'}), 400
    
    input_data = request_data.get('input_data', {})
    form_data = request_data.get('form_data', {})
    
    # Load the node class
    node_class = load_node_class(node_metadata)
    
    if node_class is None:
        return jsonify({
            'error': 'Failed to load node class',
            'identifier': identifier,
            'file_path': node_metadata.get('file_path')
        }), 500
    
    try:
        from Node.Core.Node.Core.Data import NodeConfig, NodeConfigData, NodeOutput
        
        # Create NodeConfig with form data
        node_config = NodeConfig(
            id=f"exec_{identifier}",
            type=identifier,
            data=NodeConfigData(form=form_data)
        )
        
        # Create NodeOutput from input data
        node_output = NodeOutput(data=input_data)
        
        # Create node instance
        node_instance = node_class(node_config)
        
        # Run the node asynchronously
        async def run_node():
            await node_instance.init()
            result = await node_instance.run(node_output)
            return result
        
        # Execute in asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_node())
        finally:
            loop.close()
        
        # Return the result
        return jsonify({
            'success': True,
            'node': {
                'name': node_metadata.get('name'),
                'identifier': identifier,
            },
            'input': input_data,
            'form_data': form_data,
            'output': result.model_dump() if hasattr(result, 'model_dump') else result
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'error': 'Execution failed',
            'error_type': type(e).__name__,
            'details': str(e),
            'identifier': identifier
        }), 500


def run_server(host='0.0.0.0', port=5000, debug=True):
    """
    Run the Flask development server.
    """
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()


