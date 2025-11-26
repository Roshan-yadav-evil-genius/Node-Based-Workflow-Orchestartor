"""
Unit tests for the workflow engine.
"""

import unittest
import asyncio
from typing import Any, Optional
from engine import (
    Node,
    ProducerNode,
    BlockingNode,
    NonBlockingNode,
    IFNode,
    WorkflowGraph,
    WorkflowEngine,
    AsyncExecutionStrategy,
    ThreadExecutionStrategy,
)


# Test Node Implementations

class TestProducer(ProducerNode):
    """Test producer node."""

    def __init__(self, items: list):
        super().__init__()
        self.items = items
        self.index = 0

    @property
    def identifier(self) -> str:
        return "test_producer"

    @property
    def label(self) -> str:
        return "Test Producer"

    @property
    def description(self) -> str:
        return "Test producer for unit tests"

    def produce(self) -> Optional[Any]:
        if self.index < len(self.items):
            item = self.items[self.index]
            self.index += 1
            return item
        return None


class TestBlocking(BlockingNode):
    """Test blocking node."""

    def __init__(self, multiplier: int = 2):
        super().__init__()
        self.multiplier = multiplier

    @property
    def identifier(self) -> str:
        return "test_blocking"

    @property
    def label(self) -> str:
        return "Test Blocking"

    @property
    def description(self) -> str:
        return "Test blocking node for unit tests"

    def process(self, data: Any) -> Any:
        return data * self.multiplier


class TestNonBlocking(NonBlockingNode):
    """Test non-blocking node."""

    @property
    def identifier(self) -> str:
        return "test_nonblocking"

    @property
    def label(self) -> str:
        return "Test Non-Blocking"

    @property
    def description(self) -> str:
        return "Test non-blocking node for unit tests"

    def process(self, data: Any) -> Any:
        return data + 1


class TestIF(IFNode):
    """Test IF node."""

    def __init__(self, threshold: int = 10):
        super().__init__()
        self.threshold = threshold

    @property
    def identifier(self) -> str:
        return "test_if"

    @property
    def label(self) -> str:
        return "Test IF"

    @property
    def description(self) -> str:
        return "Test IF node for unit tests"

    def evaluate(self, data: Any) -> bool:
        return data > self.threshold


class TestWorkflowGraph(unittest.TestCase):
    """Test cases for WorkflowGraph."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = WorkflowGraph()
        self.producer = TestProducer([1, 2, 3])
        self.blocking = TestBlocking()
        self.nonblocking = TestNonBlocking()

    def test_add_node(self):
        """Test adding nodes to graph."""
        self.graph.add_node(self.producer)
        self.graph.add_node(self.blocking)
        nodes = self.graph.get_all_nodes()
        self.assertIn(self.producer, nodes)
        self.assertIn(self.blocking, nodes)

    def test_connect_nodes(self):
        """Test connecting nodes."""
        self.graph.add_node(self.producer)
        self.graph.add_node(self.blocking)
        self.graph.connect(self.producer, self.blocking)
        downstream = self.graph.get_downstream(self.producer)
        self.assertIn(self.blocking, downstream)

    def test_cycle_detection(self):
        """Test cycle detection."""
        self.graph.add_node(self.producer)
        self.graph.add_node(self.blocking)
        self.graph.connect(self.producer, self.blocking)
        # Try to create cycle
        with self.assertRaises(ValueError):
            self.graph.connect(self.blocking, self.producer)

    def test_contains_blocking_downstream(self):
        """Test blocking downstream detection."""
        self.graph.add_node(self.producer)
        self.graph.add_node(self.blocking)
        self.graph.connect(self.producer, self.blocking)
        self.assertTrue(self.graph.contains_blocking_downstream(self.producer))

    def test_contains_nonblocking_downstream(self):
        """Test non-blocking downstream detection."""
        self.graph.add_node(self.producer)
        self.graph.add_node(self.nonblocking)
        self.graph.connect(self.producer, self.nonblocking)
        self.assertFalse(self.graph.contains_blocking_downstream(self.producer))

    def test_validate_dag(self):
        """Test DAG validation."""
        self.graph.add_node(self.producer)
        self.graph.add_node(self.blocking)
        self.graph.connect(self.producer, self.blocking)
        is_valid, error = self.graph.validate()
        self.assertTrue(is_valid)
        self.assertIsNone(error)


class TestExecutionStrategy(unittest.TestCase):
    """Test cases for execution strategies."""

    def setUp(self):
        """Set up test fixtures."""
        self.blocking = TestBlocking(multiplier=3)

    async def test_async_execution(self):
        """Test async execution strategy."""
        strategy = AsyncExecutionStrategy()
        result = await strategy.execute_node(self.blocking, 5)
        self.assertEqual(result, 15)

    async def test_thread_execution(self):
        """Test thread execution strategy."""
        strategy = ThreadExecutionStrategy(max_workers=2)
        result = await strategy.execute_node(self.blocking, 5)
        self.assertEqual(result, 15)
        strategy.shutdown()


class TestWorkflowEngine(unittest.TestCase):
    """Test cases for WorkflowEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = WorkflowGraph()
        self.strategy = AsyncExecutionStrategy()
        self.engine = WorkflowEngine(self.graph, self.strategy)

    def test_register_producer(self):
        """Test producer registration."""
        producer = TestProducer([1, 2])
        self.graph.add_node(producer)
        self.engine.register_producer(producer)
        self.assertIn(producer, self.engine._producers)

    def test_register_invalid_producer(self):
        """Test registering producer not in graph."""
        producer = TestProducer([1, 2])
        with self.assertRaises(ValueError):
            self.engine.register_producer(producer)

    async def test_simple_workflow(self):
        """Test simple workflow execution."""
        producer = TestProducer([1, 2, 3])
        blocking = TestBlocking(multiplier=2)

        self.graph.add_node(producer)
        self.graph.add_node(blocking)
        self.graph.connect(producer, blocking)

        self.engine.register_producer(producer)

        # Run for a short time
        try:
            await asyncio.wait_for(self.engine.start(), timeout=1.0)
        except asyncio.TimeoutError:
            await self.engine.stop()


class TestNodeTypes(unittest.TestCase):
    """Test cases for node type implementations."""

    def test_producer_node(self):
        """Test producer node."""
        producer = TestProducer([1, 2, 3])
        self.assertEqual(producer.produce(), 1)
        self.assertEqual(producer.produce(), 2)
        self.assertEqual(producer.produce(), 3)
        self.assertIsNone(producer.produce())

    def test_blocking_node(self):
        """Test blocking node."""
        blocking = TestBlocking(multiplier=5)
        result = blocking.run(10)
        self.assertEqual(result, 50)

    def test_nonblocking_node(self):
        """Test non-blocking node."""
        nonblocking = TestNonBlocking()
        result = nonblocking.run(5)
        self.assertEqual(result, 6)

    def test_if_node(self):
        """Test IF node."""
        if_node = TestIF(threshold=10)
        result = if_node.run(15)
        self.assertTrue(result["result"])
        self.assertEqual(result["branch"], "yes")
        result = if_node.run(5)
        self.assertFalse(result["result"])
        self.assertEqual(result["branch"], "no")


if __name__ == "__main__":
    unittest.main()

