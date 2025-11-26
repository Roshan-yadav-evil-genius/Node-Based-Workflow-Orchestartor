"""
workflow_engine.py

A simple, extensible node-based workflow engine demonstrating:
- ProducerNode, NonBlockingNode, BlockingNode semantics
- Producer waits for blocking downstream paths only
- Non-blocking downstream processed in independent async tasks (decoupled loop)
- Easy to extend with new node types

Run with: python workflow_engine.py
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Set
import time
import uuid
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class Node:
    """
    Base Node class (single responsibility: one piece of work).
    Each node must implement run(input_data) -> output_data.
    Nodes execute synchronously inside run().
    """

    def __init__(self, name: str):
        self.name = name
        self.downstreams: List["Node"] = []

    def connect_to(self, node: "Node") -> None:
        self.downstreams.append(node)

    def run(self, data: Any) -> Any:
        """Synchronous execution of node. Override in subclasses."""
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self.name}>"


class ProducerNode(Node):
    """
    ProducerNode: generates units of work and controls loop timing.
    It should only continue to next iteration after all connected Blocking downstreams complete.
    """

    def __init__(self, name: str, produce_fn: Callable[[], Optional[Any]], interval: float = 1.0):
        super().__init__(name)
        self.produce_fn = produce_fn
        self.interval = interval  # time between iterations if nothing produced

    def run(self, data=None):
        """Producer synchronous run is just producing data (synchronous)."""
        out = self.produce_fn()
        return out


class NonBlockingNode(Node):
    """
    NonBlockingNode: runs sync internally, returns control immediately to Producer.
    Downstream work should be processed independently (engine will schedule it separately).
    """

    def run(self, data: Any) -> Any:
        logging.info("%s processing (non-blocking) data=%s", self, data)
        # Simulate fast sync work
        time.sleep(0.1)
        return {"nb_processed_by": self.name, "payload": data}


class BlockingNode(Node):
    """
    BlockingNode: runs synchronously and forces upstream to wait until its downstream chain completes.
    """

    def run(self, data: Any) -> Any:
        logging.info("%s processing (blocking) data=%s", self, data)
        # Simulate more expensive sync work
        time.sleep(0.6)
        return {"b_processed_by": self.name, "payload": data}


class IfNode(Node):
    """
    Simple branching node. Evaluates predicate(data) and routes to different downstreams.
    This Node itself is synchronous.
    """

    def __init__(self, name: str, predicate: Callable[[Any], bool]):
        super().__init__(name)
        self.predicate = predicate

    def run(self, data: Any) -> Any:
        logging.info("%s evaluating predicate on %s", self, data)
        res = self.predicate(data)
        return {"if_result": res, "payload": data}


# ------------------------------
# Engine
# ------------------------------
class WorkflowEngine:
    def __init__(self, max_workers: int = 8):
        self.producers: List[ProducerNode] = []
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._loop = asyncio.get_event_loop()
        # caching of graph properties
        self._contains_blocking_cache: Dict[Node, bool] = {}

    def register_producer(self, p: ProducerNode) -> None:
        self.producers.append(p)

    def contains_blocking_downstream(self, node: Node, visited: Optional[Set[Node]] = None) -> bool:
        """
        DFS to check whether any path downstream contains a BlockingNode.
        Cached for speed; invalidation left simple for demo.
        """
        if visited is None:
            visited = set()
        if node in visited:
            return False
        visited.add(node)
        # cache hit
        if node in self._contains_blocking_cache:
            return self._contains_blocking_cache[node]
        if isinstance(node, BlockingNode):
            self._contains_blocking_cache[node] = True
            return True
        for d in node.downstreams:
            if self.contains_blocking_downstream(d, visited):
                self._contains_blocking_cache[node] = True
                return True
        self._contains_blocking_cache[node] = False
        return False

    async def _run_blocking_chain(self, start_node: Node, data: Any):
        """
        Execute a synchronous chain where each node runs synchronously and the producer waits until completion.
        Follows linear downstreams and IfNode decisions. For general DAG, we take simple depth-first sequential path.
        """
        current_nodes = [(start_node, data)]
        results = []
        while current_nodes:
            node, payload = current_nodes.pop(0)
            out = await self._loop.run_in_executor(self._executor, node.run, payload)
            # If IfNode: decide which downstreams to follow
            if isinstance(node, IfNode):
                cond = out.get("if_result")
                # choose downstream index 0 -> True, 1 -> False if there are two branches, else all
                if len(node.downstreams) >= 2:
                    chosen = node.downstreams[0] if cond else node.downstreams[1]
                    current_nodes.append((chosen, out))
                else:
                    # if only one downstream, pass along
                    for d in node.downstreams:
                        current_nodes.append((d, out))
            else:
                # for standard nodes: push to all downstreams sequentially
                for d in node.downstreams:
                    current_nodes.append((d, out))
            results.append(out)
        return results

    async def _run_nonblocking_chain(self, start_node: Node, data: Any):
        """
        Runs the non-blocking downstream chain in an independent async task (doesn't block producer).
        We run nodes sequentially but in the background. For broader scale, each node could be pushed into a queue.
        """
        logging.info("Scheduling non-blocking chain from %s with data=%s", start_node, data)
        # run synchronously inside threadpool but not awaited by producer
        await self._run_blocking_chain(start_node, data)

    async def _handle_producer_once(self, producer: ProducerNode):
        produced = producer.run()
        if produced is None:
            await asyncio.sleep(producer.interval)
            return

        # For each downstream node, determine if its path contains blocking nodes
        tasks = []
        for node in producer.downstreams:
            has_blocking = self.contains_blocking_downstream(node)
            if has_blocking:
                logging.info("Producer will wait for blocking path starting at %s", node)
                # run synchronously (producer waits)
                # Running blocking chain in same thread of "producer" semantics: run in executor and await
                tasks.append(self._run_blocking_chain(node, produced))
            else:
                logging.info("Producer will NOT wait for non-blocking path starting at %s", node)
                # schedule independent task and don't await (decoupled)
                asyncio.create_task(self._run_nonblocking_chain(node, produced))
        if tasks:
            # await all blocking paths to finish before next producer iteration
            await asyncio.gather(*tasks)

    async def start(self):
        logging.info("Starting engine with %d producers", len(self.producers))
        # Run a simple loop over producers concurrently
        while True:
            # prepare one iteration for each producer in parallel
            await asyncio.gather(*(self._handle_producer_once(p) for p in self.producers))
            # small tick to avoid busy-looping
            await asyncio.sleep(0.01)


# ------------------------------
# Example: Wire up the flow from your diagram (simulated)
# ------------------------------
def example():
    engine = WorkflowEngine()

    # Simulated Producer (Playwright job monitor)
    def produce_job():
        # generate a job occasionally
        if uuid.uuid4().int % 3 == 0:
            job = {"id": str(uuid.uuid4()), "title": "python dev", "budget": 100}
            logging.info("Producer produced job %s", job["id"])
            return job
        return None

    p = ProducerNode("PlaywrightMonitorProducer", produce_fn=produce_job, interval=0.5)

    # IF Node: is_python_job
    def is_python_job(job):
        title = job.get("title", "")
        return "python" in title.lower()

    if_node = IfNode("IsPythonJobIF", predicate=is_python_job)

    # Store node (non-blocking): write to store and return id
    class StoreNode(NonBlockingNode):
        def run(self, data):
            logging.info("%s storing data %s", self, data)
            time.sleep(0.05)
            # simulate store id
            return {"store_id": str(uuid.uuid4()), "payload": data}

    store = StoreNode("Store")

    # Scoring Node (Non-blocking or blocking depending on your design)
    class ScoringNode(NonBlockingNode):
        def run(self, data):
            # pretend to call ML scorer; do quickly
            job = data if isinstance(data, dict) else data.get("payload", {})
            score = (job.get("budget", 0) / 100.0) + (1.0 if "python" in job.get("title", "").lower() else 0)
            result = {"score": score, "payload": job}
            logging.info("%s scored %s -> %.2f", self, job.get("id"), score)
            time.sleep(0.12)
            return result

    scorer = ScoringNode("AI_ML_Scorer")

    # If score > 0.8 -> queue path (non-blocking node chain)
    # We'll simulate a QueuePublisher as NonBlocking (producer shouldn't wait)
    class QueuePublisher(NonBlockingNode):
        def run(self, data):
            logging.info("%s publishing to queue: %s", self, data)
            time.sleep(0.05)
            return {"queued": True, "payload": data}

    qp = QueuePublisher("QueuePublisher")

    # QueueReader -> LLM -> PlaywrightBidder should run in its own loop (simulate separate worker)
    class QueueReader(BlockingNode):
        def run(self, data):
            logging.info("%s reading queue item %s", self, data)
            time.sleep(0.2)
            return {"read": data}

    class LLMPrepare(BlockingNode):
        def run(self, data):
            logging.info("%s building proposal for %s", self, data)
            time.sleep(0.4)
            return {"proposal": "proposal-text", "payload": data}

    class PlaywrightBidder(BlockingNode):
        def run(self, data):
            logging.info("%s submitting bid for %s", self, data)
            time.sleep(0.3)
            return {"bid_submitted": True, "payload": data}

    qr = QueueReader("QueueReader")
    llm = LLMPrepare("LLMPrep")
    bidder = PlaywrightBidder("PlaywrightBidder")

    # DB branch for low score (blocking path) -> notification (non-blocking)
    class DBWriter(BlockingNode):
        def run(self, data):
            logging.info("%s writing job to DB %s", self, data)
            time.sleep(0.25)
            return {"db_id": str(uuid.uuid4()), "payload": data}

    class TelegramNotifier(NonBlockingNode):
        def run(self, data):
            logging.info("%s notifying telegram group about job %s", self, data)
            time.sleep(0.05)
            return {"notified": True, "payload": data}

    dbwriter = DBWriter("DBWriter")
    notifier = TelegramNotifier("TelegramNotifier")

    # Wire up nodes resembling the diagram:
    p.connect_to(if_node)
    if_node.connect_to(store)  # if true or single branch, goes to store
    # store -> scorer
    store.connect_to(scorer)
    # After scoring, branch if score>0.8; we simulate that with an IfNode-like behavior:
    def score_pred(d):
        # d may be scorer output
        s = d.get("score", 0) if isinstance(d, dict) else 0
        return s > 0.8

    score_if = IfNode("Score>0.8IF", predicate=score_pred)
    scorer.connect_to(score_if)

    # True branch -> queue -> queue reader chain (we want this chain to be non-blocking relative to producer)
    score_if.connect_to(qp)      # True branch (index 0)
    score_if.connect_to(dbwriter)  # False branch (index 1)

    qp.connect_to(qr)  # note: qp is non-blocking, but queue reader / llm / bidder are blocking chain (worker)
    qr.connect_to(llm)
    llm.connect_to(bidder)

    # DB writer chain then notify (we treat DB writer as blocking in producer context)
    dbwriter.connect_to(notifier)

    # Register producer and start
    engine.register_producer(p)

    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        logging.info("Shutting down example.")


if __name__ == "__main__":
    example()
