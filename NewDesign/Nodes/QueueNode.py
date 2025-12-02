from .NonBlockingNode import NonBlockingNode
from .NodeData import NodeData
from .ExecutionPool import ExecutionPool
from DataStore import DataStore
import asyncio

class QueueNode(NonBlockingNode):
    @classmethod
    def identifier(cls) -> str:
        return "queue-node-dummy"

    @property
    def execution_pool(self) -> ExecutionPool:
        return ExecutionPool.ASYNC

    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the queue node by pushing data to the queue.
        
        Uses DataStore.get_shared_instance() to access the shared DataStore
        instance for queue operations.
        """
        data_store = DataStore.get_shared_instance()
        
        # Extract queue name from node config
        queue_name = self.config.dict().get("queue_name", "default")
        
        # Push data to queue
        await data_store.push(queue_name, node_data)
        print(f"[{self.config.node_name}] Pushed data to queue '{queue_name}': {node_data.payload}")
        
        return node_data
