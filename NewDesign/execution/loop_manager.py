import asyncio
import structlog
from typing import List, Optional
from Nodes.Core.BaseNode import BaseNode, ProducerNode, BlockingNode, NonBlockingNode
from Nodes.Core.Data import NodeOutput
from execution.executor import Executor

logger = structlog.get_logger(__name__)

class LoopManager:
    """
    Manages a single loop in Production Mode.
    Executes node chains in defined order.
    """
    def __init__(self, producer: ProducerNode, chain: List[BlockingNode | NonBlockingNode], executor: Optional[Executor] = None):
        self.producer = producer
        self.chain = chain # List of nodes after the producer
        self.executor = executor or Executor()
        self.running = False

    async def start(self):
        self.running = True
        logger.info("[LoopManager] Starting loop (each node executes in its preferred pool)")
        
        while self.running:
            try:
                # 1. Execute Producer in its preferred pool
                data = await self.executor.execute_in_pool(
                    self.producer.execution_pool,
                    self.producer,
                    NodeOutput(data={})
                )
                
                # 2. Execute Chain (Blocking -> NonBlocking) - each node in its preferred pool
                for node in self.chain:
                    data = await self.executor.execute_in_pool(
                        node.execution_pool,
                        node,
                        data
                    )
                    
                    # If NonBlocking, iteration ends (conceptually)
                    if isinstance(node, NonBlockingNode):
                        break
                        
            except Exception as e:
                logger.exception("[LoopManager] Error in loop", error=str(e))
                # In real impl, send to DLQ
                await asyncio.sleep(1) # Prevent tight loop on error

    def stop(self):
        self.running = False
    
    def shutdown(self):
        """Shutdown executor pools when loop stops."""
        self.executor.shutdown()
