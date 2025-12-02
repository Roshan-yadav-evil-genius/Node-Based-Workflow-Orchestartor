import asyncio
import json
from typing import Dict, List, Any, Set
from Nodes.BaseNode import BaseNode
from Nodes.NodeData import NodeData
from Nodes.NodeConfig import NodeConfig
from Nodes.ProducerNode import ProducerNode
from Nodes.NonBlockingNode import NonBlockingNode
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

        # 2. Build edge map from workflow edges
        edges = workflow_json.get("edges", [])
        edge_map: Dict[str, List[str]] = {}  # source -> [targets]
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                if source not in edge_map:
                    edge_map[source] = []
                edge_map[source].append(target)

        # 3. Find all ProducerNodes dynamically
        producer_nodes: List[str] = []
        for node_id, node in self.nodes.items():
            if isinstance(node, ProducerNode):
                producer_nodes.append(node_id)
                print(f"[Orchestrator] Found ProducerNode: {node_id}")

        # 4. For each ProducerNode, traverse graph to build chain until NonBlockingNode
        for producer_id in producer_nodes:
            chain_ids = self._traverse_chain_from_producer(producer_id, edge_map)
            
            if chain_ids:
                self.create_loop(producer_id, chain_ids)
                print(f"[Orchestrator] Created loop starting at {producer_id} with chain: {chain_ids}")
            else:
                print(f"[Orchestrator] Warning: No chain found for ProducerNode {producer_id}")

    def _traverse_chain_from_producer(self, producer_id: str, edge_map: Dict[str, List[str]]) -> List[str]:
        """
        Traverse the graph from a ProducerNode following edges until a NonBlockingNode is reached.
        Returns the chain of node IDs (excluding the producer itself).
        """
        chain_ids: List[str] = []
        visited: Set[str] = {producer_id}  # Track visited nodes to avoid cycles
        current_id = producer_id
        
        while current_id in edge_map:
            # Get next nodes from edges
            next_nodes = edge_map[current_id]
            
            # For now, follow the first path (can be extended to handle branching)
            # In a more sophisticated implementation, we might handle all branches
            if not next_nodes:
                break
                
            next_id = next_nodes[0]  # Take first edge
            
            # Check if we've already visited this node (cycle detection)
            if next_id in visited:
                print(f"[Orchestrator] Warning: Cycle detected at node {next_id}, stopping traversal")
                break
            
            # Check if node exists
            if next_id not in self.nodes:
                print(f"[Orchestrator] Warning: Node {next_id} referenced in edges but not found")
                break
            
            # Add to chain
            chain_ids.append(next_id)
            visited.add(next_id)
            
            # Check if this is a NonBlockingNode (marks loop end)
            next_node = self.nodes[next_id]
            if isinstance(next_node, NonBlockingNode):
                # Found loop end marker
                break
            
            # Continue to next node
            current_id = next_id
        
        return chain_ids

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
