from abc import ABC
from .BaseNode import BaseNode

class ProducerNode(BaseNode, ABC):
    """
    Marks loop start. Called first each iteration.
    Starts and controls the loop. Controls timing and triggers downstream nodes.
    """
    pass
