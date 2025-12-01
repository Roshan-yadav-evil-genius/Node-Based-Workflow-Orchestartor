from abc import ABC, abstractmethod
from .NodeConfig import NodeConfig
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool

class BaseNode(ABC):
    def __init__(self, config: NodeConfig):
        self.config = config

    @property
    @abstractmethod
    def execution_pool(self) -> ExecutionPool:
        """
        The preferred execution pool for this node.
        """
        pass

    @abstractmethod
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the node logic.
        """
        pass
