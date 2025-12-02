from abc import ABC
from .BaseNode import BaseNode

class BlockingNode(BaseNode, ABC):
    """
    Performs work that must be completed prior to continuation.
    The LoopManager awaits the Blocking node and all downstream Blocking children 
    in its async chain to complete before proceeding.
    """
    pass
