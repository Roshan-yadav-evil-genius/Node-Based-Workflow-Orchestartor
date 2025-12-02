from abc import ABC
from .BlockingNode import BlockingNode

class LogicalNodes(BlockingNode, ABC):
    """
    Base class for logical/conditional nodes that perform decision-making operations.
    Inherits from BlockingNode, ensuring logical operations complete before continuation.
    """
    pass
