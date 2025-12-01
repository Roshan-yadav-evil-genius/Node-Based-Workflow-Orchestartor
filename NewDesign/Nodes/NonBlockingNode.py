from abc import ABC
from .BaseNode import BaseNode

class NonBlockingNode(BaseNode, ABC):
    """
    Semantically marks loop-end in the execution model.
    Performs a computation or transformation but does not force the Producer 
    to wait for downstream operations.
    """
    pass
