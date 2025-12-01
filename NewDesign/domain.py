"""
Core domain models for the Workflow Orchestrator.

This module defines the fundamental data structures and enums used throughout
the system, following the Single Responsibility Principle.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ExecutionPool(Enum):
    """
    Execution pool types with priority ordering.
    
    Priority: PROCESS (highest) > THREAD (medium) > ASYNC (lowest)
    Used to determine the execution environment for nodes and loops.
    """
    ASYNC = "async"
    THREAD = "thread"
    PROCESS = "process"
    
    @classmethod
    def get_priority(cls, pool: 'ExecutionPool') -> int:
        """Get priority value for pool selection (higher = more priority)."""
        priorities = {
            cls.ASYNC: 1,
            cls.THREAD: 2,
            cls.PROCESS: 3,
        }
        return priorities.get(pool, 0)
    
    @classmethod
    def highest_priority(cls, pools: list['ExecutionPool']) -> 'ExecutionPool':
        """Select the highest priority pool from a list."""
        if not pools:
            return cls.ASYNC  # Default
        return max(pools, key=cls.get_priority)


class NodeType(Enum):
    """Node type classification for workflow execution semantics."""
    PRODUCER = "producer"
    BLOCKING = "blocking"
    NON_BLOCKING = "non-blocking"


@dataclass
class NodeConfig:
    """
    Static configuration data for node initialization.
    
    This is passed to nodes during initialization and remains constant
    throughout the node's lifecycle.
    """
    node_id: str
    node_type: str
    execution_pool: ExecutionPool = ExecutionPool.ASYNC
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert execution_pool string to enum if needed."""
        if isinstance(self.execution_pool, str):
            self.execution_pool = ExecutionPool(self.execution_pool)


@dataclass
class NodeData:
    """
    Runtime payload data passed between nodes during execution.
    
    This represents the dynamic data that flows through the workflow,
    transformed by each node as it executes.
    """
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the data dictionary."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the data dictionary."""
        self.data[key] = value
    
    def update(self, other: Dict[str, Any]) -> None:
        """Update data dictionary with values from another dict."""
        self.data.update(other)
    
    def copy(self) -> 'NodeData':
        """Create a deep copy of this NodeData instance."""
        import copy
        return copy.deepcopy(self)
