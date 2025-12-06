from abc import ABC, abstractmethod

from .Data import NodeOutput


class BaseNodeMethod(ABC):
    
    def setup(self):
        """
        setup method is not utlized directly but is called by init method.
        This method is used to initialize the node and set up any necessary resources.
        Default implementation does nothing.
        """
        pass

    @abstractmethod
    def init(self):
        """
        Before the Loop Manager starts the loop, the init method is called.
        """
        pass

    @abstractmethod
    async def execute(self, previous_node_output: NodeOutput) -> NodeOutput:
        """
        Execute the node logic.
        """
        pass

    def cleanup(self):
        """
        After the Loop Manager finishes the loop, the cleanup method is called.
        This method is used to clean up any necessary resources.
        Default implementation does nothing.
        """
        pass