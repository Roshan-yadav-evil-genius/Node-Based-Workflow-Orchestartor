import asyncio
from typing import List, Optional
from Nodes.BaseNode import BaseNode
from Nodes.ProducerNode import ProducerNode
from Nodes.BlockingNode import BlockingNode
from Nodes.NonBlockingNode import NonBlockingNode
from Nodes.NodeData import NodeData
from Nodes.ExecutionPool import ExecutionPool

class LoopManager:
    """
    Manages a single loop in Production Mode.
    Executes node chains in defined order.
    """
    def __init__(self, producer: ProducerNode, chain: List[BaseNode]):
        self.producer = producer
        self.chain = chain # List of nodes after the producer
        self.running = False

    def select_pool(self) -> ExecutionPool:
        """
        Determines the execution pool for the loop.
        Priority: PROCESS > THREAD > ASYNC
        """
        pools = [self.producer.execution_pool] + [node.execution_pool for node in self.chain]
        
        if ExecutionPool.PROCESS in pools:
            return ExecutionPool.PROCESS
        if ExecutionPool.THREAD in pools:
            return ExecutionPool.THREAD
        return ExecutionPool.ASYNC

    async def start(self):
        self.running = True
        print(f"[LoopManager] Starting loop with pool: {self.select_pool().value}")
        
        while self.running:
            try:
                # 1. Execute Producer
                data = await self.producer.execute(NodeData(id="init", payload={}))
                
                # 2. Execute Chain (Blocking -> NonBlocking)
                for node in self.chain:
                    data = await node.execute(data)
                    
                    # If NonBlocking, iteration ends (conceptually)
                    if isinstance(node, NonBlockingNode):
                        break
                        
            except Exception as e:
                print(f"[LoopManager] Error in loop: {e}")
                # In real impl, send to DLQ
                await asyncio.sleep(1) # Prevent tight loop on error

    def stop(self):
        self.running = False
