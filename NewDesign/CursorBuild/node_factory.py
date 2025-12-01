"""
Node factory for creating node instances from workflow definitions.

This module provides a factory pattern for instantiating appropriate node
classes based on workflow configuration, following the Single Responsibility Principle.
"""

from typing import Any, Dict, Optional, Type

from domain import NodeConfig, NodeType
from nodes import (
    BaseNode,
    BlockingNode,
    NonBlockingNode,
    ProducerNode,
    QueueNode,
    QueueReader,
)

# Import all dummy node implementations
from Node.playwright_freelance_job_monitor_producer import PlaywrightFreelanceJobMonitorProducer
from Node.if_python_job_node import IfPythonJobNode
from Node.if_score_threshold_node import IfScoreThresholdNode
from Node.store_reader import StoreReader
from Node.queue_reader_dummy import QueueReaderDummy
from Node.query_db import QueryDB
from Node.ai_ml_scoring_node import AIMLScoringNode
from Node.llm_proposal_preparer import LLMProposalPreparer
from Node.playwright_freelance_bidder import PlaywrightFreelanceBidder
from Node.telegram_sender import TelegramSender
from Node.db_status_updater import DBStatusUpdater
from Node.store_node import StoreNode
from Node.queue_node_dummy import QueueNodeDummy
from Node.db_node import DBNode


class NodeFactory:
    """
    Factory for creating node instances from workflow definitions.
    
    Maps node types from JSON workflow definitions to Python node classes
    and handles node registration and instantiation.
    """
    
    # Registry of node type strings to node classes
    _node_registry: Dict[str, Type[BaseNode]] = {}
    
    @classmethod
    def register_node_type(cls, node_type: str, node_class: Type[BaseNode]) -> None:
        """
        Register a custom node type.
        
        Args:
            node_type: String identifier for the node type
            node_class: Python class that implements BaseNode
        """
        cls._node_registry[node_type] = node_class
    
    @classmethod
    def create_node(
        self,
        node_type: str,
        node_id: str,
        node_config_dict: Dict[str, Any],
        queue_manager=None
    ) -> BaseNode:
        """
        Create a node instance from workflow definition.
        
        Args:
            node_type: Type of node (e.g., 'producer', 'blocking', 'non-blocking', 'queue', 'queue-reader')
            node_id: Unique identifier for the node
            node_config_dict: Configuration dictionary from workflow JSON
            queue_manager: Optional QueueManager instance for queue nodes
            
        Returns:
            BaseNode: Instantiated node instance
            
        Raises:
            ValueError: If node_type is not recognized
        """
        # Extract execution pool from config
        execution_pool_str = node_config_dict.get('execution_pool', 'async')
        execution_pool = self._parse_execution_pool(execution_pool_str)
        
        # Create NodeConfig
        node_config = NodeConfig(
            node_id=node_id,
            node_type=node_type,
            execution_pool=execution_pool,
            config=node_config_dict.get('config', {})
        )
        
        # Check if custom node type is registered
        if node_type in self._node_registry:
            node_class = self._node_registry[node_type]
            return node_class(node_config)
        
        # Handle built-in node types
        node_type_lower = node_type.lower()
        
        # Dummy node implementations
        if node_type_lower == 'playwright-freelance-job-monitor-producer' or node_type_lower == 'playwright_freelance_job_monitor_producer':
            return PlaywrightFreelanceJobMonitorProducer(node_config)
        
        elif node_type_lower == 'if-python-job' or node_type_lower == 'if_python_job':
            threshold = node_config_dict.get('config', {}).get('threshold', 0.8)
            return IfPythonJobNode(node_config)
        
        elif node_type_lower == 'if-score-threshold' or node_type_lower == 'if_score_threshold':
            threshold = node_config_dict.get('config', {}).get('threshold', 0.8)
            return IfScoreThresholdNode(node_config, threshold=threshold)
        
        elif node_type_lower == 'store-reader' or node_type_lower == 'store_reader':
            return StoreReader(node_config)
        
        elif node_type_lower == 'queue-reader-dummy' or node_type_lower == 'queue_reader_dummy':
            queue_name = node_config_dict.get('config', {}).get('queue_name', 'default')
            return QueueReaderDummy(node_config, queue_name=queue_name)
        
        elif node_type_lower == 'query-db' or node_type_lower == 'query_db':
            return QueryDB(node_config)
        
        elif node_type_lower == 'ai-ml-scoring' or node_type_lower == 'ai_ml_scoring':
            return AIMLScoringNode(node_config)
        
        elif node_type_lower == 'llm-proposal-preparer' or node_type_lower == 'llm_proposal_preparer':
            return LLMProposalPreparer(node_config)
        
        elif node_type_lower == 'playwright-freelance-bidder' or node_type_lower == 'playwright_freelance_bidder':
            return PlaywrightFreelanceBidder(node_config)
        
        elif node_type_lower == 'telegram-sender' or node_type_lower == 'telegram_sender':
            group_id = node_config_dict.get('config', {}).get('group_id', 'default_group')
            return TelegramSender(node_config, group_id=group_id)
        
        elif node_type_lower == 'db-status-updater' or node_type_lower == 'db_status_updater':
            return DBStatusUpdater(node_config)
        
        elif node_type_lower == 'store-node' or node_type_lower == 'store_node':
            store_name = node_config_dict.get('config', {}).get('store_name', 'default_store')
            return StoreNode(node_config, store_name=store_name)
        
        elif node_type_lower == 'queue-node-dummy' or node_type_lower == 'queue_node_dummy':
            queue_name = node_config_dict.get('config', {}).get('queue_name', 'default_queue')
            return QueueNodeDummy(node_config, queue_name=queue_name)
        
        elif node_type_lower == 'db-node' or node_type_lower == 'db_node':
            table_name = node_config_dict.get('config', {}).get('table_name', 'jobs')
            return DBNode(node_config, table_name=table_name)
        
        # Built-in node types
        elif node_type_lower == 'queue':
            queue_name = node_config_dict.get('queue_name')
            if not queue_name:
                raise ValueError(f"QueueNode '{node_id}' requires 'queue_name' in config")
            return QueueNode(node_config, queue_name, queue_manager)
        
        elif node_type_lower == 'queue-reader' or node_type_lower == 'queuereader':
            queue_name = node_config_dict.get('queue_name')
            if not queue_name:
                raise ValueError(f"QueueReader '{node_id}' requires 'queue_name' in config")
            timeout = node_config_dict.get('timeout', 5.0)
            return QueueReader(node_config, queue_name, queue_manager, timeout)
        
        elif node_type_lower == 'producer':
            # Return abstract ProducerNode - users should subclass this
            # For now, we'll create a basic implementation
            return _BasicProducerNode(node_config)
        
        elif node_type_lower == 'blocking':
            # Return abstract BlockingNode - users should subclass this
            return _BasicBlockingNode(node_config)
        
        elif node_type_lower == 'non-blocking' or node_type_lower == 'nonblocking':
            # Return abstract NonBlockingNode - users should subclass this
            return _BasicNonBlockingNode(node_config)
        
        else:
            raise ValueError(f"Unknown node type: {node_type}")
    
    @staticmethod
    def _parse_execution_pool(pool_str: str) -> Any:
        """Parse execution pool string to ExecutionPool enum."""
        from domain import ExecutionPool
        
        pool_str_lower = pool_str.lower()
        if pool_str_lower == 'async':
            return ExecutionPool.ASYNC
        elif pool_str_lower == 'thread':
            return ExecutionPool.THREAD
        elif pool_str_lower == 'process':
            return ExecutionPool.PROCESS
        else:
            # Default to ASYNC if unknown
            return ExecutionPool.ASYNC


# Basic implementations for abstract node types
# These are placeholders - users should subclass and implement their own logic

class _BasicProducerNode(ProducerNode):
    """Basic producer node implementation for factory use."""
    
    async def execute(self, node_data):
        """Basic implementation - returns data unchanged."""
        return node_data


class _BasicBlockingNode(BlockingNode):
    """Basic blocking node implementation for factory use."""
    
    async def execute(self, node_data):
        """Basic implementation - returns data unchanged."""
        return node_data


class _BasicNonBlockingNode(NonBlockingNode):
    """Basic non-blocking node implementation for factory use."""
    
    async def execute(self, node_data):
        """Basic implementation - returns data unchanged."""
        return node_data
