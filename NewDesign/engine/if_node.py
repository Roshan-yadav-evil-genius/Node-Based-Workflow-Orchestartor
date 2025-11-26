"""
IF Node implementation for conditional branching.
Single Responsibility: Conditional branching based on predicate evaluation.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional
from .blocking_node import BlockingNode


class IFNode(BlockingNode):
    """
    IF Node provides conditional branching within the workflow.
    It evaluates a predicate and routes data to either the "yes" or "no" branch.
    
    Execution Behavior:
    - Extends BlockingNode behavior (blocks upstream)
    - Evaluates condition on input data
    - Routes to appropriate branch based on evaluation
    - Supports multiple downstream paths
    """

    @abstractmethod
    def evaluate(self, data: Any) -> bool:
        """
        Evaluate the condition predicate on the input data.
        
        Args:
            data: Input data to evaluate
            
        Returns:
            True for "yes" branch, False for "no" branch
        """
        pass

    def process(self, data: Any) -> Dict[str, Any]:
        """
        Process the input data by evaluating the condition and returning
        routing information.
        
        Args:
            data: Input data to process
            
        Returns:
            Dictionary with 'result' (evaluated boolean) and 'data' (original data)
        """
        result = self.evaluate(data)
        return {
            "result": result,
            "data": data,
            "branch": "yes" if result else "no"
        }

    def run(self, data: Any = None) -> Dict[str, Any]:
        """
        Execute the IF node by evaluating the condition.
        
        Args:
            data: Input data to evaluate
            
        Returns:
            Dictionary with evaluation result and routing information
        """
        if data is None:
            raise ValueError("IFNode requires input data")
        return self.process(data)

