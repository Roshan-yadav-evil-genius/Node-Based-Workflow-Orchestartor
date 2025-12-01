"""
Base class for conditional nodes that route workflow based on conditions.
"""

import asyncio
import random
from abc import abstractmethod
from typing import Optional

from domain import NodeConfig, NodeData
from nodes import BlockingNode


class ConditionalNode(BlockingNode):
    """
    Base class for conditional nodes that evaluate conditions and route to different paths.
    
    Conditional nodes evaluate a condition and set metadata indicating which path
    should be taken (Yes/No, True/False, etc.). The WorkflowLoader uses this metadata
    along with edge labels to determine the next node in the chain.
    """
    
    def __init__(self, node_config: NodeConfig, condition_key: str, true_label: str = "Yes", false_label: str = "No"):
        """
        Initialize conditional node.
        
        Args:
            node_config: Static configuration for this node
            condition_key: Key in metadata to store the condition result
            true_label: Label for true/yes path (default: "Yes")
            false_label: Label for false/no path (default: "No")
        """
        super().__init__(node_config)
        self._condition_key = condition_key
        self._true_label = true_label
        self._false_label = false_label
    
    @abstractmethod
    def evaluate_condition(self, node_data: NodeData) -> bool:
        """
        Evaluate the condition based on input data.
        
        Args:
            node_data: Input data for evaluation
            
        Returns:
            bool: True if condition is met, False otherwise
        """
        pass
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the conditional node by evaluating the condition.
        
        Args:
            node_data: Input data for evaluation
            
        Returns:
            NodeData: Output data with condition result in metadata
        """
        # Simulate evaluation delay
        delay = random.uniform(0.1, 0.3)
        await asyncio.sleep(delay)
        
        # Evaluate condition
        condition_result = self.evaluate_condition(node_data)
        
        # Set metadata for routing
        node_data.metadata[self._condition_key] = condition_result
        node_data.metadata["condition_label"] = self._true_label if condition_result else self._false_label
        
        return node_data
