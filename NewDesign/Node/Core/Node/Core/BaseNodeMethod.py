from abc import ABC, abstractmethod

from .Data import NodeOutput


class BaseNodeMethod(ABC):
    
    def setup(self):
        """
        Before the Loop Manager starts the loop, the setup method is called.
        This method is used to initialize the node and set up any necessary resources.
        Default implementation does nothing.
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