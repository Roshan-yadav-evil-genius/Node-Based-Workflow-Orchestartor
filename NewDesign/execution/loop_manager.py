import asyncio
import structlog
from typing import List, Optional
from Nodes.Core.BaseNode import BaseNode, ProducerNode, BlockingNode, NonBlockingNode
from Nodes.Core.Data import NodeOutput
from core.utils import node_type
from execution.executor import Executor

logger = structlog.get_logger(__name__)


class LoopManager:
    """
    Manages a single loop in Production Mode.
    Executes node chains in defined order.
    """

    def __init__(
        self,
        producer: ProducerNode,
        chain: List[BlockingNode | NonBlockingNode],
        executor: Optional[Executor] = None,
    ):
        self.producer = producer
        self.chain = chain  # List of nodes after the producer
        self.executor = executor or Executor()
        self.running = False
        self.loop_count = 0
        self.loop_identifier = self.producer.config.id

    async def start(self):
        self.running = True

        while self.running:
            self.loop_count += 1
            try:
                logger.info(
                    f"Executing Producer",
                    loop_id=self.loop_identifier,
                    node_id=self.producer.config.id,
                    node_type=f"{node_type(self.producer)}({self.producer.identifier()})",
                    loop_count=self.loop_count,
                )
                # 1. Execute Producer in its preferred pool
                data = await self.executor.execute_in_pool(
                    self.producer.execution_pool, self.producer, NodeOutput(data={})
                )
                logger.info(
                    f"Producer Executed",
                    loop_id=self.loop_identifier,
                    node_id=self.producer.config.id,
                    output=data,
                    node_type=f"{node_type(self.producer)}({self.producer.identifier()})",
                    loop_count=self.loop_count,
                )
                # 2. Execute Chain (Blocking -> NonBlocking) - each node in its preferred pool
                for node in self.chain:
                    logger.info(
                        f"Executing Node",
                        loop_id=self.loop_identifier,
                        node_id=node.config.id,
                        node_type=f"{node_type(node)}({node.identifier()})",
                        input=data,
                        loop_count=self.loop_count,
                    )
                    data = await self.executor.execute_in_pool(
                        node.execution_pool, node, data
                    )
                    logger.info(
                        f"Node Executed",
                        loop_id=self.loop_identifier,
                        node_id=node.config.id,
                        output=data,
                        node_type=f"{node_type(node)}({node.identifier()})",
                    )
                    # If NonBlocking, iteration ends (conceptually)
                    if isinstance(node, NonBlockingNode):
                        break

            except Exception as e:
                logger.exception("Error in loop", error=str(e))
                # In real impl, send to DLQ
                await asyncio.sleep(1)  # Prevent tight loop on error

    def stop(self):
        self.running = False

    def shutdown(self):
        """Shutdown executor pools when loop stops."""
        self.executor.shutdown()
