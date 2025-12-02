import asyncio
import json
from typing import Dict, List, Any, Set, Tuple
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
        self.loop_branches: Dict[str, Dict[str, List[str]]] = {}  # producer_id -> {branch_label: [node_ids]}

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

        # 2. Build edge map from workflow edges with metadata
        edges = workflow_json.get("edges", [])
        edge_map: Dict[str, List[Dict[str, str]]] = {}  # source -> [{"target": ..., "label": ...}]
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            source_handle = edge.get("sourceHandle")  # Yes/No label or null
            if source and target:
                if source not in edge_map:
                    edge_map[source] = []
                edge_map[source].append({
                    "target": target,
                    "label": source_handle if source_handle else None
                })

        # 3. Find all ProducerNodes dynamically
        producer_nodes: List[str] = []
        for node_id, node in self.nodes.items():
            if isinstance(node, ProducerNode):
                producer_nodes.append(node_id)
                print(f"[Orchestrator] Found ProducerNode: {node_id}")

        # 4. For each ProducerNode, traverse graph to build chain until NonBlockingNode
        for producer_id in producer_nodes:
            chain_ids, branch_info = self._traverse_chain_from_producer(producer_id, edge_map)
            
            if chain_ids:
                self.create_loop(producer_id, chain_ids)
                self.loop_branches[producer_id] = branch_info
                print(f"[Orchestrator] Created loop starting at {producer_id} with chain: {chain_ids}")
            else:
                print(f"[Orchestrator] Warning: No chain found for ProducerNode {producer_id}")

    def _traverse_chain_from_producer(self, producer_id: str, edge_map: Dict[str, List[Dict[str, str]]]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Traverse the graph from a ProducerNode following edges until a NonBlockingNode is reached.
        Handles conditional branches by following all paths.
        Returns tuple of (chain of node IDs, branch information dictionary).
        """
        chain_ids: List[str] = []
        branch_info: Dict[str, List[str]] = {}  # {branch_label: [node_ids]}
        visited: Set[str] = {producer_id}  # Track visited nodes to avoid cycles
        current_id = producer_id
        
        while current_id in edge_map:
            # Get next edges from edge map
            next_edges = edge_map[current_id]
            
            if not next_edges:
                break
            
            # Check if this is a branching node (multiple outgoing edges)
            if len(next_edges) > 1:
                # Branching node - add it to chain first if not already added
                if current_id not in chain_ids and current_id != producer_id:
                    chain_ids.append(current_id)
                    visited.add(current_id)
                
                # Follow all branches and collect nodes maintaining order
                all_branch_nodes: List[str] = []
                branch_visited_combined: Set[str] = visited.copy()
                
                for edge in next_edges:
                    branch_target = edge["target"]
                    branch_label = edge.get("label") or "default"  # Use "default" if no label
                    
                    # Traverse this branch with a fresh visited set for this branch
                    branch_chain = self._traverse_branch(
                        branch_target, 
                        edge_map, 
                        branch_visited_combined.copy(),  # Use a copy to allow parallel branches
                        branch_label
                    )
                    
                    # Store branch information
                    if branch_label not in branch_info:
                        branch_info[branch_label] = []
                    branch_info[branch_label].extend(branch_chain)
                    
                    # Add nodes from this branch to the combined list
                    for node_id in branch_chain:
                        if node_id not in all_branch_nodes:
                            all_branch_nodes.append(node_id)
                        branch_visited_combined.add(node_id)
                
                # Add all nodes from all branches to the chain
                for node_id in all_branch_nodes:
                    if node_id not in chain_ids:
                        chain_ids.append(node_id)
                        visited.add(node_id)
                
                # After processing branches, we've reached NonBlockingNodes, so stop
                break
            else:
                # Single edge - follow normally
                next_edge = next_edges[0]
                next_id = next_edge["target"]
                
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
        
        return chain_ids, branch_info

    def _traverse_branch(self, start_id: str, edge_map: Dict[str, List[Dict[str, str]]], visited: Set[str], branch_label: str = None) -> List[str]:
        """
        Traverse a single branch from a starting node until a NonBlockingNode is reached.
        Returns the list of node IDs in this branch.
        """
        branch_chain: List[str] = []
        current_id = start_id
        
        while current_id:
            # Check if node exists
            if current_id not in self.nodes:
                print(f"[Orchestrator] Warning: Node {current_id} referenced in edges but not found")
                break
            
            # Check for cycles
            if current_id in visited:
                print(f"[Orchestrator] Warning: Cycle detected at node {current_id} in branch")
                break
            
            # Add to branch chain
            branch_chain.append(current_id)
            visited.add(current_id)
            
            # Check if this is a NonBlockingNode (marks branch end)
            current_node = self.nodes[current_id]
            if isinstance(current_node, NonBlockingNode):
                # Found branch end marker
                break
            
            # Get next edges
            if current_id not in edge_map:
                # No more edges, end of branch
                break
            
            next_edges = edge_map[current_id]
            if not next_edges:
                break
            
            # If multiple edges, follow all branches recursively
            if len(next_edges) > 1:
                # Another branching point - collect all branches
                sub_branch_visited = visited.copy()
                for edge in next_edges:
                    branch_target = edge["target"]
                    sub_branch_chain = self._traverse_branch(
                        branch_target,
                        edge_map,
                        sub_branch_visited.copy(),
                        edge.get("label")
                    )
                    # Add nodes maintaining order
                    for node_id in sub_branch_chain:
                        if node_id not in branch_chain:
                            branch_chain.append(node_id)
                        sub_branch_visited.add(node_id)
                break
            else:
                # Single edge - continue
                current_id = next_edges[0]["target"]
        
        return branch_chain

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
