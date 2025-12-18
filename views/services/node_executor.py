"""
Node Executor Module
Executes nodes with input and form data.
"""

import asyncio
import traceback
from typing import Any, Dict

from .node_loader import NodeLoader


class NodeExecutor:
    """
    Executes nodes asynchronously with input and form data.
    
    Responsibilities:
    - Create node instances with configuration
    - Execute nodes with input data
    - Handle async execution
    """
    
    def __init__(self, node_loader: NodeLoader):
        """
        Initialize NodeExecutor.
        
        Args:
            node_loader: NodeLoader for loading node classes.
        """
        self._node_loader = node_loader
    
    def execute(self, node_metadata: Dict, input_data: Dict, form_data: Dict) -> Dict:
        """
        Execute a node with the given input and form data.
        
        Args:
            node_metadata: Node metadata dict.
            input_data: Input data to pass to the node.
            form_data: Form field values.
            
        Returns:
            Dict with execution result or error information.
        """
        node_class = self._node_loader.load_class(node_metadata)
        
        if node_class is None:
            return {
                'success': False,
                'error': 'Failed to load node class',
                'identifier': node_metadata.get('identifier'),
                'file_path': node_metadata.get('file_path')
            }
        
        try:
            result = self._run_node(node_class, node_metadata, input_data, form_data)
            
            return {
                'success': True,
                'node': {
                    'name': node_metadata.get('name'),
                    'identifier': node_metadata.get('identifier'),
                },
                'input': input_data,
                'form_data': form_data,
                'output': result.model_dump() if hasattr(result, 'model_dump') else result
            }
            
        except Exception as e:
            traceback.print_exc()
            return {
                'success': False,
                'error': 'Execution failed',
                'error_type': type(e).__name__,
                'details': str(e),
                'identifier': node_metadata.get('identifier')
            }
    
    def _run_node(self, node_class, node_metadata: Dict, input_data: Dict, form_data: Dict) -> Any:
        """
        Run the node asynchronously and return the result.
        """
        from Node.Core.Node.Core.Data import NodeConfig, NodeConfigData, NodeOutput
        
        # Create NodeConfig with form data
        node_config = NodeConfig(
            id=f"exec_{node_metadata.get('identifier')}",
            type=node_metadata.get('identifier'),
            data=NodeConfigData(form=form_data)
        )
        
        # Create NodeOutput from input data
        node_output = NodeOutput(data=input_data)
        
        # Create node instance
        node_instance = node_class(node_config)
        
        # Run the node asynchronously
        async def run_async():
            await node_instance.init()
            result = await node_instance.run(node_output)
            return result
        
        # Execute in asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_async())
        finally:
            loop.close()
        
        return result

