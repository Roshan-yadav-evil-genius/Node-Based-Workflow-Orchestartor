import asyncio
from typing import Any, Dict, Optional

class QueueManager:
    """
    Abstracts Redis-backed queues for cross-loop communication.
    """
    def __init__(self):
        # In a real implementation, this would be a Redis client.
        # For now, we use an in-memory dictionary of asyncio.Queues.
        self._queues: Dict[str, asyncio.Queue] = {}

    async def get_queue(self, queue_name: str) -> asyncio.Queue:
        if queue_name not in self._queues:
            self._queues[queue_name] = asyncio.Queue()
        return self._queues[queue_name]

    async def push(self, queue_name: str, data: Any):
        """
        Push data to a named queue.
        """
        queue = await self.get_queue(queue_name)
        await queue.put(data)
        print(f"[QueueManager] Pushed to '{queue_name}': {data}")

    async def pop(self, queue_name: str, timeout: Optional[float] = None) -> Any:
        """
        Pop data from a named queue.
        """
        queue = await self.get_queue(queue_name)
        if timeout:
            return await asyncio.wait_for(queue.get(), timeout)
        return await queue.get()
