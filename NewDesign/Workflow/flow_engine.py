import asyncio
import structlog
from typing import Dict, List, Any, Type
from Node.Core.Node.Core.BaseNode import BaseNode, ProducerNode
from Node.Core.Node.Core.Data import NodeOutput
from .flow_graph import FlowGraph
from .flow_analyzer import FlowAnalyzer
from .flow_builder import FlowBuilder
from .flow_node import FlowNode
from .node_registry import NodeRegistry
from .PostProcessing import PostProcessor
from .PostProcessing.queue_mapper import QueueMapper
from .PostProcessing.node_validator import NodeValidator
from .execution.flow_runner import FlowRunner
from .storage.data_store import DataStore

logger = structlog.get_logger(__name__)


class FlowEngine:
    """
    Central coordination system for flow execution.
    """

    _post_processors: List[Type[PostProcessor]] = [QueueMapper, NodeValidator]

    def __init__(self):
        self.data_store = DataStore()
        self.flow_runners: List[FlowRunner] = []
        self.flow_graph = FlowGraph()
        self.flow_analyzer = FlowAnalyzer(self.flow_graph)
        self.flow_builder = FlowBuilder(self.flow_graph, NodeRegistry())

    def create_loop(self, producer_flow_node: FlowNode):
        producer = producer_flow_node.instance
        if not isinstance(producer, ProducerNode):
            raise ValueError(f"Node {producer_flow_node.id} is not a ProducerNode")
        runner = FlowRunner(producer_flow_node)
        self.flow_runners.append(runner)

    async def run_production(self):
        logger.info("Starting Production Mode...")
        tasks = [runner.start() for runner in self.flow_runners]
        if not tasks:
            logger.info("No flows to run.")
            return
        await asyncio.gather(*tasks)

    async def run_development_node(self, node_id: str, input_data: NodeOutput) -> NodeOutput:
        node = self.flow_graph.get_node_instance(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        result = await node.execute(previous_node_output=input_data)
        return result

    def load_workflow(self, workflow_json: Dict[str, Any]):
        self.flow_builder.load_workflow(workflow_json)

        for processor_class in self._post_processors:
            processor = processor_class(self.flow_graph)
            processor.execute()

        first_node_id = self.flow_analyzer.get_first_node_id()
        if first_node_id:
            first_node = self.flow_graph.node_map[first_node_id]
            logger.info(f"Workflow Loaded Successfully", graph=first_node.to_dict())
        else:
            raise ValueError("No first node found in the workflow")

        producer_nodes = self.flow_analyzer.get_producer_nodes()
        for producer_flow_node in producer_nodes:
            try:
                self.create_loop(producer_flow_node)
                logger.info(f"Created Loop", producer_node_id=producer_flow_node.id)
            except ValueError as e:
                logger.warning(f"Failed to create loop", error=str(e))
