"""
WorkflowOrchestrator: Architecture + Class Skeleton

This file contains:
- Data classes: NodeConfig, NodeData, ExecutionContext
- Node abstractions: BaseNode, ProducerNode, BlockingNode, NonBlockingNode
- Example concrete nodes: QueueNode (producer and reader variants), MLScoringNode, LLMNode
- LoopManager: runtime for a single loop with pluggable executor types
- ResourceRegistry: shared resources (queues, DB clients, models)
- WorkflowOrchestrator: high-level kernel that registers resources and manages loops

Notes:
- This is a skeleton designed to show clear separation of responsibilities and runtime adapters.
- Implementation details (persistence, real ML logic, real LLM calls) are intentionally left minimal.
- Use this as a blueprint to implement robust production behavior: retries, backpressure, tracing, metrics, graceful shutdown.
"""
from __future__ import annotations
import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, List, Callable, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import inspect

# -------------------------
# Data models / contexts
# -------------------------

@dataclass
class NodeConfig:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NodeData:
    payload: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionContext:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    retries: int = 0
    deadline_ms: Optional[int] = None
    cancel_token: Optional[asyncio.Event] = None
    extra: Dict[str, Any] = field(default_factory=dict)

# -------------------------
# Node abstractions
# -------------------------

class BaseNode(Protocol):
    """Base node protocol. Concrete nodes should inherit one of ProducerNode/BlockingNode/NonBlockingNode.
    Nodes must accept a NodeConfig at construction time and accept (ExecutionContext, NodeData) on run.
    """

    config: NodeConfig

    def __init__(self, config: NodeConfig): ...

    def run(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]: ...

    async def run_async(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]: ...


class ProducerNode(BaseNode):
    """ProducerNode: produces new NodeData each loop iteration.
    Semantics: it is the loop driver. When executed, it returns data (or None if nothing produced).
    """
    def __init__(self, config: NodeConfig):
        self.config = config

    def run(self, ctx: ExecutionContext, data: Optional[NodeData] = None) -> Optional[NodeData]:
        raise NotImplementedError

    async def run_async(self, ctx: ExecutionContext, data: Optional[NodeData] = None) -> Optional[NodeData]:
        # default adapter: call sync run in threadpool if overridden
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.run, ctx, data)


class BlockingNode(BaseNode):
    """BlockingNode: enforces synchronous/sequential behavior for the chain.
    When called, next Producer iteration must wait until this node and its downstream blocking chain complete.
    """
    def __init__(self, config: NodeConfig):
        self.config = config

    def run(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]:
        raise NotImplementedError

    async def run_async(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.run, ctx, data)


class NonBlockingNode(BaseNode):
    """NonBlockingNode: performs work but immediately returns control to the producer loop.
    Downstream effects can continue asynchronously (e.g., pushing to a queue, writing to DB).
    """
    def __init__(self, config: NodeConfig):
        self.config = config

    def run(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]:
        raise NotImplementedError

    async def run_async(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.run, ctx, data)

# -------------------------
# Example concrete nodes
# -------------------------

class InMemoryQueue:
    """A tiny async-friendly in-memory queue used as shared resource."""
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.Queue(maxsize=maxsize)

    async def put(self, item: Any):
        await self._queue.put(item)

    async def get(self) -> Any:
        return await self._queue.get()

    def qsize(self) -> int:
        return self._queue.qsize()


class QueueProducerNode(NonBlockingNode):
    """Pushes NodeData into a shared queue resource.
    Config params expect: orchestrator_resource_name -> name used to lookup queue in registry
    """
    def __init__(self, config: NodeConfig, orchestrator_lookup: Callable[[str], Any]):
        super().__init__(config)
        self._lookup = orchestrator_lookup

    async def run_async(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]:
        q_name = self.config.params.get("queue_name")
        queue: InMemoryQueue = self._lookup(q_name)
        # fire-and-forget push
        await queue.put(data)
        # return immediately; NonBlocking => producer continues
        return data


class QueueReaderNode(BlockingNode):
    """Reads an item from a shared queue and returns it; blocking semantics apply.
    Typically used as the first node (or early node) in another loop.
    """
    def __init__(self, config: NodeConfig, orchestrator_lookup: Callable[[str], Any]):
        super().__init__(config)
        self._lookup = orchestrator_lookup

    async def run_async(self, ctx: ExecutionContext, data: Optional[NodeData] = None) -> Optional[NodeData]:
        q_name = self.config.params.get("queue_name")
        queue: InMemoryQueue = self._lookup(q_name)
        item = await queue.get()
        return item


class MLScoringNode(BlockingNode):
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        # In real implementation: load pickled model or lightweight runner

    def run(self, ctx: ExecutionContext, data: NodeData) -> NodeData:
        # dummy scoring
        payload = data.payload
        score = 0.9 if isinstance(payload, dict) else 0.1
        data.metadata.setdefault("scores", {})["ml_score"] = score
        return data


class LLMProposalNode(NonBlockingNode):
    def __init__(self, config: NodeConfig):
        super().__init__(config)

    async def run_async(self, ctx: ExecutionContext, data: NodeData) -> Optional[NodeData]:
        # pretend to call LLM; in production, rate-limit and handle costs
        await asyncio.sleep(0.05)
        data.metadata.setdefault("proposal", "generated")
        return data

# -------------------------
# Resource registry
# -------------------------

class ResourceRegistry:
    def __init__(self):
        self._resources: Dict[str, Any] = {}

    def register(self, name: str, resource: Any):
        self._resources[name] = resource

    def get(self, name: str) -> Any:
        return self._resources[name]

    def has(self, name: str) -> bool:
        return name in self._resources

# -------------------------
# LoopManager
# -------------------------

class LoopType:
    ASYNCIO = "asyncio"
    THREAD = "thread"
    PROCESS = "process"


class LoopManager:
    """Manages execution of a linear graph (nodes list) for one logical loop.

    Important rules enforced here:
    - First node is usually a ProducerNode or a BlockingNode that waits for input (like QueueReader)
    - For NonBlockingNode: schedule asynchronous invocation and continue the producer loop immediately
    - For BlockingNode: await completion before continuing the Producer
    - LoopManager DOES NOT own queues or shared resources; it uses the ResourceRegistry
    """

    def __init__(self, name: str, nodes: List[BaseNode], registry: ResourceRegistry,
                 loop_type: str = LoopType.ASYNCIO, max_workers: int = 8):
        self.name = name
        self.nodes = nodes
        self.registry = registry
        self.loop_type = loop_type
        self.max_workers = max_workers
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._process_pool: Optional[ProcessPoolExecutor] = None

    async def start(self):
        if self.loop_type == LoopType.ASYNCIO:
            self._running = True
            self._task = asyncio.create_task(self._async_loop())
        else:
            # For THREAD or PROCESS: run the asyncio loop wrapper but with executors for blocking node calls
            self._running = True
            self._task = asyncio.create_task(self._async_loop())

    async def stop(self):
        self._running = False
        if self._task:
            await self._task
        if self._thread_pool:
            self._thread_pool.shutdown(wait=False)
        if self._process_pool:
            self._process_pool.shutdown(wait=False)

    async def _async_loop(self):
        # Very simple loop: call producer; route into chain based on node types
        # Assumes nodes are ordered for linear pipelines. For graph, replace with dispatcher logic.
        if not self.nodes:
            return
        producer = self.nodes[0]
        while self._running:
            ctx = ExecutionContext()
            # 1) produce
            produced = None
            if hasattr(producer, "run_async") and inspect.iscoroutinefunction(producer.run_async):
                produced = await producer.run_async(ctx, None)
            else:
                # run sync in executor
                loop = asyncio.get_running_loop()
                if self._thread_pool is None:
                    self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
                produced = await loop.run_in_executor(self._thread_pool, producer.run, ctx, None)

            if produced is None:
                # nothing produced; small sleep to avoid busy-looping
                await asyncio.sleep(0.1)
                continue

            # 2) execute chain from node 1 onwards
            await self._execute_chain(ctx, produced)

    async def _execute_chain(self, ctx: ExecutionContext, data: NodeData):
        current = data
        for node in self.nodes[1:]:
            # NonBlocking => schedule and continue immediately
            if isinstance(node, NonBlockingNode):
                # schedule fire-and-forget
                asyncio.create_task(node.run_async(ctx, current))
                # producer loop should continue; do not wait
                continue

            # BlockingNode => wait for its completion
            if isinstance(node, BlockingNode):
                # node may implement run_async
                if inspect.iscoroutinefunction(node.run_async):
                    current = await node.run_async(ctx, current)
                else:
                    loop = asyncio.get_running_loop()
                    if self._thread_pool is None:
                        self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
                    current = await loop.run_in_executor(self._thread_pool, node.run, ctx, current)
                # if chain has more nodes, continue; producer should wait until the entire blocking chain finishes
                continue

            # If node is a ProducerNode or unknown, treat as blocking by default
            else:
                if hasattr(node, "run_async") and inspect.iscoroutinefunction(node.run_async):
                    current = await node.run_async(ctx, current)
                else:
                    loop = asyncio.get_running_loop()
                    if self._thread_pool is None:
                        self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
                    current = await loop.run_in_executor(self._thread_pool, node.run, ctx, current)

# -------------------------
# WorkflowOrchestrator (kernel)
# -------------------------

class WorkflowOrchestrator:
    """Top-level coordinator: manages resource registry and lifecycle of LoopManagers."""

    def __init__(self):
        self.registry = ResourceRegistry()
        self.loops: Dict[str, LoopManager] = {}

    def register_resource(self, name: str, resource: Any):
        self.registry.register(name, resource)

    def create_loop(self, name: str, nodes: List[BaseNode], loop_type: str = LoopType.ASYNCIO,
                    max_workers: int = 8) -> LoopManager:
        lm = LoopManager(name=name, nodes=nodes, registry=self.registry, loop_type=loop_type, max_workers=max_workers)
        self.loops[name] = lm
        return lm

    async def start_all(self):
        # start loops in parallel
        await asyncio.gather(*[lm.start() for lm in self.loops.values()])

    async def stop_all(self):
        await asyncio.gather(*[lm.stop() for lm in self.loops.values()])

# -------------------------
# Example wiring (pseudo-bootstrap)
# -------------------------

async def example_bootstrap():
    orch = WorkflowOrchestrator()

    # register a shared queue resource
    shared_q = InMemoryQueue()
    orch.register_resource("jobs_queue", shared_q)

    # build loop A: Producer -> ML scoring -> QueueProducer
    producer = ProducerNode(NodeConfig(name="job_monitor"))
    # For demo, we create a minimal inline producer implementation
    class DemoProducer(ProducerNode):
        async def run_async(self, ctx, data=None):
            await asyncio.sleep(0.2)
            # produce a small dict
            return NodeData(payload={"title": "DevOps job"}, metadata={})

    loopA_nodes = [DemoProducer(NodeConfig("demo_prod")), MLScoringNode(NodeConfig("ml_score")),
                   QueueProducerNode(NodeConfig("push_q", {"queue_name": "jobs_queue"}), orch.registry.get)]
    loopA = orch.create_loop("discovery_loop", loopA_nodes, loop_type=LoopType.ASYNCIO)

    # build loop B: QueueReader -> LLM -> Bidder (non-blocking)
    loopB_nodes = [QueueReaderNode(NodeConfig("reader", {"queue_name": "jobs_queue"}), orch.registry.get),
                   LLMProposalNode(NodeConfig("llm"))]
    loopB = orch.create_loop("proposal_loop", loopB_nodes, loop_type=LoopType.ASYNCIO)

    # start orchestration
    await orch.start_all()
    # run for a few seconds
    await asyncio.sleep(2)
    await orch.stop_all()


# If run as script, execute the demo
if __name__ == "__main__":
    asyncio.run(example_bootstrap())
