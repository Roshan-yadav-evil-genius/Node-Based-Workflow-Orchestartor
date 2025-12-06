from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..graph import WorkflowGraph


class PostProcessor(ABC):
    """
    Abstract base class for all workflow post-processing operations.
    Follows Single Responsibility Principle - each processor handles one concern.
    """

    def __init__(self, graph: "WorkflowGraph"):
        """
        Initialize PostProcessor with workflow graph.

        Args:
            graph: WorkflowGraph instance to process
        """
        self.graph = graph

    @abstractmethod
    def execute(self) -> None:
        """
        Execute the post-processing operation on the workflow graph.
        """
        pass
