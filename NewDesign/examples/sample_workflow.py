"""
Example workflow implementation demonstrating the workflow engine usage.
This example creates a simple workflow with Producer, Blocking, and Non-Blocking nodes.
"""

import asyncio
import sys
from pathlib import Path
import time
# Add parent directory to path to import engine
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import (
    ProducerNode,
    BlockingNode,
    NonBlockingNode,
    IFNode,
    WorkflowGraph,
    WorkflowEngine,
    AsyncExecutionStrategy,
    ThreadExecutionStrategy,
)


# Example Node Implementations

class SimpleProducer(ProducerNode):
    """Simple producer that generates sequential numbers."""

    def __init__(self, max_items: int = 10):
        super().__init__()
        self.max_items = max_items
        self.counter = 0

    @property
    def identifier(self) -> str:
        return "simple_producer"

    @property
    def label(self) -> str:
        return "Simple Producer"

    @property
    def description(self) -> str:
        return "Produces sequential numbers from 0 to max_items"

    def produce(self):
        if self.counter < self.max_items:
            item = self.counter
            self.counter += 1
            time.sleep(1)
            print(f"[Producer] Generated item: {item}")
            return item
        return None


class NumberProcessor(BlockingNode):
    """Blocking node that processes numbers."""

    @property
    def identifier(self) -> str:
        return "number_processor"

    @property
    def label(self) -> str:
        return "Number Processor"

    @property
    def description(self) -> str:
        return "Processes numbers synchronously (blocking)"

    def process(self, data):
        result = data * 2
        time.sleep(1)
        print(f"[Blocking] Processed {data} -> {result}")
        return result


class ScoreCalculator(BlockingNode):
    """Blocking node that calculates a score."""

    @property
    def identifier(self) -> str:
        return "score_calculator"

    @property
    def label(self) -> str:
        return "Score Calculator"

    @property
    def description(self) -> str:
        return "Calculates a score for the input"

    def process(self, data):
        # Simple score: data / 10.0
        score = data / 10.0
        time.sleep(1)
        print(f"[Score] Calculated score: {score}")
        return {"value": data, "score": score}


class ScoreFilter(IFNode):
    """IF node that filters based on score threshold."""

    def __init__(self, threshold: float = 0.8):
        super().__init__()
        self.threshold = threshold

    @property
    def identifier(self) -> str:
        return "score_filter"

    @property
    def label(self) -> str:
        return "Score Filter"

    @property
    def description(self) -> str:
        return f"Filters items based on score threshold ({self.threshold})"

    def evaluate(self, data):
        score = data.get("score", 0.0)
        result = score > self.threshold
        print(f"[IF] Score {score} > {self.threshold}? {result}")
        return result


class QueueWriter(NonBlockingNode):
    """Non-blocking node that writes to a queue (simulated)."""

    @property
    def identifier(self) -> str:
        return "queue_writer"

    @property
    def label(self) -> str:
        return "Queue Writer"

    @property
    def description(self) -> str:
        return "Writes to queue (non-blocking)"

    def process(self, data):
        print(f"[Non-Blocking] Writing to queue: {data}")
        # In real implementation, this would write to a queue/DB
        return data


class DatabaseWriter(NonBlockingNode):
    """Non-blocking node that writes to a database (simulated)."""

    @property
    def identifier(self) -> str:
        return "db_writer"

    @property
    def label(self) -> str:
        return "Database Writer"

    @property
    def description(self) -> str:
        return "Writes to database (non-blocking)"

    def process(self, data):
        print(f"[Non-Blocking] Writing to DB: {data}")
        # In real implementation, this would write to a database
        return data


async def main():
    """Main function demonstrating workflow engine usage."""

    # Create nodes
    producer = SimpleProducer(max_items=5)
    processor = NumberProcessor()
    score_calc = ScoreCalculator()
    score_filter = ScoreFilter(threshold=0.8)
    queue_writer = QueueWriter()
    db_writer = DatabaseWriter()

    # Create workflow graph
    graph = WorkflowGraph()
    graph.add_node(producer)
    graph.add_node(processor)
    graph.add_node(score_calc)
    graph.add_node(score_filter)
    graph.add_node(queue_writer)
    graph.add_node(db_writer)

    # Connect nodes
    graph.connect(producer, processor)
    graph.connect(processor, score_calc)
    graph.connect(score_calc, score_filter)
    graph.connect(score_filter, queue_writer, branch="yes")
    graph.connect(score_filter, db_writer, branch="no")

    # Create execution strategy (choose one)
    # strategy = AsyncExecutionStrategy()
    strategy = ThreadExecutionStrategy(max_workers=4)

    # Create and configure engine
    engine = WorkflowEngine(graph, strategy)
    engine.register_producer(producer)

    print("Starting workflow engine...")
    print("=" * 50)

    # Start engine (this will run until stopped)
    try:
        # Run for a short time to demonstrate
        await asyncio.wait_for(engine.start(), timeout=5.0)
    except asyncio.TimeoutError:
        print("\nStopping workflow engine...")
        await engine.stop()
        print("Workflow engine stopped.")


if __name__ == "__main__":
    asyncio.run(main())

