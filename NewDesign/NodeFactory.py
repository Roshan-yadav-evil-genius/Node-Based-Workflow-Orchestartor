from typing import Optional
from Nodes.BaseNode import BaseNode
from Nodes.NodeConfig import NodeConfig


class NodeFactory:
    """
    Factory class responsible for creating node instances from node type and config.
    Follows Single Responsibility Principle - only handles node creation.
    """
    
    @staticmethod
    def create_node(node_type: str, config: NodeConfig) -> Optional[BaseNode]:
        """
        Create a node instance based on node type and configuration.
        
        Args:
            node_type: String identifier for the node type
            config: NodeConfig object with node configuration
            
        Returns:
            BaseNode instance or None if node type is unknown
        """
        # Import here to avoid circular imports
        from Nodes.PlaywrightFreelanceJobMonitorProducer import PlaywrightFreelanceJobMonitorProducer
        from Nodes.IfPythonJob import IfPythonJob
        from Nodes.StoreNode import StoreNode
        from Nodes.StoreReader import StoreReader
        from Nodes.AiMlScoring import AiMlScoring
        from Nodes.IfScoreThreshold import IfScoreThreshold
        from Nodes.QueueNode import QueueNode
        from Nodes.QueueReader import QueueReader
        from Nodes.LlmProposalPreparer import LlmProposalPreparer
        from Nodes.PlaywrightFreelanceBidder import PlaywrightFreelanceBidder
        from Nodes.DbNode import DbNode
        from Nodes.QueryDb import QueryDb
        from Nodes.TelegramSender import TelegramSender
        from Nodes.DbStatusUpdater import DbStatusUpdater

        mapping = {
            "playwright-freelance-job-monitor-producer": PlaywrightFreelanceJobMonitorProducer,
            "if-python-job": IfPythonJob,
            "store-node": StoreNode,
            "store-reader": StoreReader,
            "ai-ml-scoring": AiMlScoring,
            "if-score-threshold": IfScoreThreshold,
            "queue-node-dummy": QueueNode,  # Map to our dummy QueueNode
            "queue-reader-dummy": QueueReader,  # Map to our dummy QueueReader
            "llm-proposal-preparer": LlmProposalPreparer,
            "playwright-freelance-bidder": PlaywrightFreelanceBidder,
            "db-node": DbNode,
            "query-db": QueryDb,
            "telegram-sender": TelegramSender,
            "db-status-updater": DbStatusUpdater
        }
        
        node_cls = mapping.get(node_type)
        if node_cls:
            return node_cls(config)
        print(f"[NodeFactory] Warning: Unknown node type '{node_type}'")
        return None
