from abc import ABC, abstractmethod
from typing import Optional, Dict
from .Data import NodeConfig, NodeOutput, PoolType

class BaseNode(ABC):
    def __init__(self, config: NodeConfig):
        self.config = config

    @property
    @abstractmethod
    def execution_pool(self) -> PoolType:
        """
        The preferred execution pool for this node.
        """
        pass

    @abstractmethod
    async def execute(self, previous_node_output: NodeOutput) -> NodeOutput:
        """
        Execute the node logic.
        """
        pass

    @classmethod
    @abstractmethod
    def identifier(cls) -> str:
        """
        Return the node type identifier (kebab-case string).
        This identifier is used to map node types from workflow definitions to node classes.
        """
        pass

    def ready(self) -> Dict[str, str]:
        """
        Validate that the node has all required config fields.
        
        Returns:
            Dictionary mapping field names to error messages.
            Empty dict if node is ready, non-empty dict if validation fails.
        """
        return {}

class NonBlockingNode(BaseNode, ABC):
    """
    Semantically marks loop-end in the execution model.
    Performs a computation or transformation but does not force the Producer 
    to wait for downstream operations.
    """
    pass


class ProducerNode(BaseNode, ABC):
    """
    Marks loop start. Called first each iteration.
    Starts and controls the loop. Controls timing and triggers downstream nodes.
    """
    pass


class BlockingNode(BaseNode, ABC):
    """
    Performs work that must be completed prior to continuation.
    The LoopManager awaits the Blocking node and all downstream Blocking children 
    in its async chain to complete before proceeding.
    """
    pass

class LogicalNode(BlockingNode, ABC):
    """
    Base class for logical/conditional nodes that perform decision-making operations.
    Inherits from BlockingNode, ensuring logical operations complete before continuation.
    """
    pass


