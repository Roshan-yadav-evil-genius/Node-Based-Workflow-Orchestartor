from abc import ABC, abstractmethod
from typing import Optional
from .Data import NodeConfig, NodeOutput, PoolType
from .BaseNodeProperty import BaseNodeProperty
from .BaseNodeMethod import BaseNodeMethod

class BaseNode(BaseNodeProperty, BaseNodeMethod, ABC):
    """
    Dont Use This Class Directly. Use One of the Subclasses Instead.
    This class is used to define the base node class and is not meant to be instantiated directly.
    use for type hinting and inheritance.
    """
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.form = self.get_form
        

    def is_ready(self) -> bool:
        """
        Validate that the node has all required config fields.
        
        Returns:
            bool: True if node is ready (form is valid or None), False otherwise.
        """
        if self.form is None:
            return True
        return self.form.is_valid()
    
    def init(self):
        """
        Initialize the node.
        This method is called before calling execute method.
        It is used to validate the node and set up any necessary resources.
        Default implementation does nothing.
        """

        if not self.is_ready():
            raise ValueError(f"Node {self.config.id} is not ready")
        self.setup()

    


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
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self.output: Optional[str] = None
        self.test_result = False
        

    def set_output(self, output: bool):
        self.test_result = output
        self.output = "yes" if output else "no"

