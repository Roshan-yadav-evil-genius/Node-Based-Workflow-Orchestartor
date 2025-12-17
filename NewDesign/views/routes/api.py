"""
API Routes Module
REST API endpoints for node operations.
"""

from flask import Blueprint, jsonify, request, current_app


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/nodes')
def get_nodes():
    """
    Get all nodes as a hierarchical tree structure.
    """
    services = current_app.extensions['services']
    nodes = services.node_registry.get_all_nodes()
    return jsonify(nodes)


@api_bp.route('/nodes/flat')
def get_nodes_flat():
    """
    Get all nodes as a flat list.
    """
    services = current_app.extensions['services']
    nodes = services.node_registry.get_nodes_flat()
    return jsonify(nodes)


@api_bp.route('/nodes/count')
def get_nodes_count():
    """
    Get total count of all nodes.
    """
    services = current_app.extensions['services']
    count = services.node_registry.get_count()
    return jsonify({'count': count})


@api_bp.route('/node/<identifier>/form')
def get_node_form(identifier):
    """
    Get form JSON for a specific node.
    """
    services = current_app.extensions['services']
    
    # Find the node by identifier
    node = services.node_registry.find_by_identifier(identifier)
    
    if node is None:
        return jsonify({
            'error': 'Node not found', 
            'identifier': identifier
        }), 404
    
    # Check if node has a form
    if not node.get('has_form'):
        return jsonify({
            'node': _format_node_response(node),
            'form': None,
            'message': 'This node does not have a form'
        })
    
    # Load and serialize the form
    form_json = services.form_loader.load_form(node)
    
    return jsonify({
        'node': _format_node_response(node, include_form_class=True),
        'form': form_json
    })


@api_bp.route('/node/<identifier>/execute', methods=['POST'])
def execute_node(identifier):
    """
    Execute a node with given input data and form values.
    
    Request body:
    {
        "input_data": { ... },
        "form_data": { ... }
    }
    """
    services = current_app.extensions['services']
    
    # Find the node by identifier
    node = services.node_registry.find_by_identifier(identifier)
    
    if node is None:
        return jsonify({
            'error': 'Node not found', 
            'identifier': identifier
        }), 404
    
    # Parse request data
    try:
        request_data = request.get_json()
    except Exception as e:
        return jsonify({
            'error': 'Invalid JSON in request body', 
            'details': str(e)
        }), 400
    
    if not request_data:
        return jsonify({'error': 'Request body is required'}), 400
    
    input_data = request_data.get('input_data', {})
    form_data = request_data.get('form_data', {})
    
    # Execute the node
    result = services.node_executor.execute(node, input_data, form_data)
    
    if not result.get('success'):
        return jsonify(result), 500
    
    return jsonify(result)


@api_bp.route('/node/<identifier>/form/field-options', methods=['POST'])
def get_field_options(identifier):
    """
    Get options for a dependent field based on parent field value.
    
    Used for cascading dropdowns where selecting a parent value
    populates child field options.
    
    Request body:
    {
        "parent_field": "country",
        "parent_value": "india",
        "dependent_field": "state"
    }
    
    Returns:
    {
        "field": "state",
        "options": [{"value": "maharashtra", "text": "Maharashtra"}, ...]
    }
    """
    services = current_app.extensions['services']
    
    # Find the node by identifier
    node = services.node_registry.find_by_identifier(identifier)
    
    if node is None:
        return jsonify({
            'error': 'Node not found', 
            'identifier': identifier
        }), 404
    
    # Parse request data
    try:
        request_data = request.get_json()
    except Exception as e:
        return jsonify({
            'error': 'Invalid JSON in request body', 
            'details': str(e)
        }), 400
    
    if not request_data:
        return jsonify({'error': 'Request body is required'}), 400
    
    parent_field = request_data.get('parent_field')
    parent_value = request_data.get('parent_value')
    dependent_field = request_data.get('dependent_field')
    
    if not all([parent_field, dependent_field]):
        return jsonify({
            'error': 'parent_field and dependent_field are required'
        }), 400
    
    # Get field options from form
    options = services.form_loader.get_field_options(
        node, dependent_field, parent_value
    )
    
    return jsonify({
        'field': dependent_field,
        'options': [{'value': v, 'text': t} for v, t in options]
    })


def _format_node_response(node: dict, include_form_class: bool = False) -> dict:
    """
    Format node metadata for API response.
    """
    response = {
        'name': node.get('name'),
        'identifier': node.get('identifier'),
        'type': node.get('type'),
        'label': node.get('label'),
        'description': node.get('description'),
    }
    
    if include_form_class:
        response['form_class'] = node.get('form_class')
        response['file_path'] = node.get('file_path')
    
    return response

