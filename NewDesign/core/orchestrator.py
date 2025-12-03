import asyncio
import structlog
from typing import Dict, List, Any
from Nodes.Core.BaseNode import BaseNode
from Nodes.Core.NodeData import NodeData
from execution.loop_manager import LoopManager
from storage.data_store import DataStore
from core.loader import WorkflowLoader
from core.traverser import GraphTraverser

logger = structlog.get_logger(__name__)

class WorkflowOrchestrator:
    """
    Central coordination system for workflow execution.
    Follows Single Responsibility Principle - only handles coordination and lifecycle management.
    """
    def __init__(self):
        self.data_store = DataStore.set_shared_instance(DataStore())
        self.loop_managers: List[LoopManager] = []
        self.nodes: Dict[str, BaseNode] = {}  # Map of all nodes by ID
        self.loop_branches: Dict[str, Dict[str, List[str]]] = {}  # producer_id -> {branch_label: [node_ids]}
        self.workflow_loader = WorkflowLoader()

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
        logger.info("[Orchestrator] Starting Production Mode...")
        tasks = [manager.start() for manager in self.loop_managers]
        if not tasks:
            logger.info("[Orchestrator] No loops to run.")
            return
        await asyncio.gather(*tasks)

    async def run_development_node(self, node_id: str, input_data: NodeData) -> NodeData:
        """
        Execute a single node directly (Development Mode).
        """
        logger.info(f"[Orchestrator] Development Mode: Executing node {node_id}")
        node = self.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
            
        # In real dev mode, we would check Redis for upstream dependencies here
        
        return await node.execute(input_data)

    def load_workflow(self, workflow_json: Dict[str, Any]):
        """
        Load workflow from JSON definition.
        Delegates to WorkflowLoader and GraphTraverser following SRP.
        """
        logger.info("[Orchestrator] Loading workflow...")
        
        # Delegate workflow loading to WorkflowLoader
        workflow_graph = self.workflow_loader.load_workflow(workflow_json)
        
        # Store nodes in orchestrator for access
        self.nodes = workflow_graph.base_nodes
        
        # Delegate graph traversal to GraphTraverser
        graph_traverser = GraphTraverser(workflow_graph.base_nodes)
        loops = graph_traverser.find_loops(workflow_graph.get_edge_map(), workflow_graph.producer_node_ids)
        logger.debug(f"Loops: {loops}")
        # Create loops from traversal results
        for producer_id, chain_ids, branch_info in loops:
            if chain_ids:
                self.create_loop(producer_id, chain_ids)
                self.loop_branches[producer_id] = branch_info
                logger.info(f"[Orchestrator] Created loop starting at {producer_id} with chain: {chain_ids}")
            else:
                logger.warning(f"[Orchestrator] Warning: No chain found for ProducerNode {producer_id}")
