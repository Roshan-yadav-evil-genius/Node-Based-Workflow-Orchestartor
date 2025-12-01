import asyncio
import json
from typing import Dict, List, Any
from Nodes.BaseNode import BaseNode
from Nodes.NodeData import NodeData
from Nodes.NodeConfig import NodeConfig
from LoopManager import LoopManager
from QueueManager import QueueManager

class WorkflowOrchestrator:
    """
    Central coordination system.
    """
    def __init__(self):
        self.queue_manager = QueueManager()
        self.loop_managers: List[LoopManager] = []
        self.nodes: Dict[str, BaseNode] = {} # Map of all nodes by ID

    def register_node(self, node: BaseNode):
        self.nodes[node.config.node_id] = node

    def create_loop(self, producer_id: str, chain_ids: List[str]):
        producer = self.nodes.get(producer_id)
        chain = [self.nodes.get(nid) for nid in chain_ids]
        
        if not producer or any(n is None for n in chain):
            raise ValueError("Invalid node IDs provided for loop creation")
            
        manager = LoopManager(producer, chain)
        self.loop_managers.append(manager)

    async def run_production(self):
        """
        Start all loops.
        """
        print("[Orchestrator] Starting Production Mode...")
        tasks = [manager.start() for manager in self.loop_managers]
        if not tasks:
            print("[Orchestrator] No loops to run.")
            return
        await asyncio.gather(*tasks)

    async def run_development_node(self, node_id: str, input_data: NodeData) -> NodeData:
        """
        Execute a single node directly (Development Mode).
        """
        print(f"[Orchestrator] Development Mode: Executing node {node_id}")
        node = self.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
            
        # In real dev mode, we would check Redis for upstream dependencies here
        
        return await node.execute(input_data)

    def load_workflow(self, workflow_json: Dict[str, Any]):
        """
        Load workflow from JSON definition.
        """
        print("[Orchestrator] Loading workflow...")
        
        # 1. Instantiate Nodes
        for node_def in workflow_json.get("nodes", []):
            node_id = node_def["id"]
            node_type = node_def["type"]
            config_data = node_def["data"].get("config", {})
            config_data["node_id"] = node_id
            config_data["node_name"] = node_id # Use ID as name for now
            
            config = NodeConfig(**config_data)
            
            # Factory logic (simple mapping for now)
            node_instance = self._create_node_instance(node_type, config)
            if node_instance:
                self.register_node(node_instance)
                print(f"[Orchestrator] Registered node: {node_id} ({node_type})")

        # 2. Create Loops (Simplified logic for simulation)
        # In a real system, we would traverse the graph to identify loops.
        # Here we manually define the main loop based on the known structure for simulation.
        # We look for the Producer and create a loop starting from it.
        
        # Find Producer
        producer_id = "playwright-freelance-job-monitor-producer"
        if producer_id in self.nodes:
            # Manually defining the chain for this specific simulation to ensure order
            # In a real system, this is derived from 'edges'
            chain_ids = [
                "if-python-job",
                "store-node",
                "store-reader",
                "ai-ml-scoring",
                "if-score-threshold",
                # Branching is complex to represent in a linear list for this simple LoopManager.
                # For simulation, we will add the main path nodes.
                "queue-node" 
            ]
            
            # Filter out missing nodes just in case
            chain_ids = [nid for nid in chain_ids if nid in self.nodes]
            
            self.create_loop(producer_id, chain_ids)
            print(f"[Orchestrator] Created loop starting at {producer_id}")

            # Create second loop for queue reader
            reader_id = "queue-reader"
            if reader_id in self.nodes:
                chain_ids_2 = [
                    "llm-proposal-preparer",
                    "playwright-freelance-bidder"
                ]
                chain_ids_2 = [nid for nid in chain_ids_2 if nid in self.nodes]
                self.create_loop(reader_id, chain_ids_2)
                print(f"[Orchestrator] Created loop starting at {reader_id}")

    def _create_node_instance(self, node_type: str, config: NodeConfig) -> BaseNode:
        # Import here to avoid circular imports if any, or just for cleanliness
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
            "queue-node-dummy": QueueNode, # Map to our dummy QueueNode
            "queue-reader-dummy": QueueReader, # Map to our dummy QueueReader
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
        print(f"[Orchestrator] Warning: Unknown node type '{node_type}'")
        return None
