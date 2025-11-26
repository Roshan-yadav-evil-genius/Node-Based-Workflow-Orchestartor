# Workflow Engine

A flexible workflow execution system supporting Producer, Blocking, and Non-Blocking node types with configurable execution models (async/await, threads, or processes).

## Architecture

The workflow engine implements a Directed Acyclic Graph (DAG) of nodes with three distinct types:

1. **Producer Node**: Generates work items in a loop. Waits for blocking downstream nodes, but continues immediately when encountering non-blocking nodes.

2. **Blocking Node**: Executes synchronously and blocks upstream nodes until the entire downstream chain completes.

3. **Non-Blocking Node**: Executes synchronously but returns control immediately to the producer, allowing downstream operations to run independently.

4. **IF Node**: Special blocking node that provides conditional branching based on predicate evaluation.

## Features

- **Single Responsibility Principle**: Each component has one clear purpose
- **Pluggable Execution Models**: Choose between async/await, threads, or processes
- **DAG Support**: Full support for directed acyclic graphs with cycle detection
- **Conditional Branching**: IF nodes for routing data based on conditions
- **Type Safety**: Abstract base classes ensure proper node implementation

## Installation

No external dependencies required (uses only Python standard library).

## Quick Start

```python
import asyncio
from engine import (
    ProducerNode,
    BlockingNode,
    WorkflowGraph,
    WorkflowEngine,
    AsyncExecutionStrategy,
)

# Define your nodes
class MyProducer(ProducerNode):
    # Implement required methods
    pass

class MyProcessor(BlockingNode):
    # Implement required methods
    pass

# Create workflow
graph = WorkflowGraph()
graph.add_node(producer)
graph.add_node(processor)
graph.connect(producer, processor)

# Create engine
strategy = AsyncExecutionStrategy()
engine = WorkflowEngine(graph, strategy)
engine.register_producer(producer)

# Run
asyncio.run(engine.start())
```

## File Structure

```
engine/
├── __init__.py              # Package exports
├── base_node.py            # Base Node abstract class
├── producer_node.py        # ProducerNode implementation
├── blocking_node.py        # BlockingNode implementation
├── non_blocking_node.py    # NonBlockingNode implementation
├── if_node.py              # IFNode for conditional branching
├── workflow_graph.py        # DAG structure management
├── execution_strategy.py    # Execution strategy pattern
├── workflow_engine.py       # Main engine orchestrator
└── node_registry.py        # Node factory and registry

examples/
└── sample_workflow.py      # Example workflow implementation

tests/
└── test_workflow_engine.py # Unit tests
```

## Execution Models

### AsyncExecutionStrategy
Uses asyncio for async/await execution. Best for I/O-bound operations.

```python
strategy = AsyncExecutionStrategy()
```

### ThreadExecutionStrategy
Uses ThreadPoolExecutor for thread-based execution. Best for CPU-bound operations that can run in parallel.

```python
strategy = ThreadExecutionStrategy(max_workers=8)
```

### ProcessExecutionStrategy
Uses ProcessPoolExecutor for process-based execution. Best for CPU-intensive tasks requiring true parallelism.

```python
strategy = ProcessExecutionStrategy(max_workers=4)
```

**Note**: Nodes must be picklable for process execution.

## Example Workflow

See `examples/sample_workflow.py` for a complete example demonstrating:
- Producer generating work items
- Blocking nodes processing data
- IF nodes for conditional branching
- Non-blocking nodes for async operations

## Running Tests

```bash
python -m unittest tests.test_workflow_engine
```

## Design Principles

1. **Single Responsibility**: Each class has one clear purpose
2. **Strategy Pattern**: Execution model is pluggable
3. **Dependency Inversion**: Engine depends on abstractions
4. **Open/Closed**: Easy to add new node types without modifying engine
5. **Interface Segregation**: Separate interfaces for different node behaviors

## Node Implementation Guide

### Producer Node

```python
class MyProducer(ProducerNode):
    @property
    def identifier(self) -> str:
        return "my_producer"
    
    @property
    def label(self) -> str:
        return "My Producer"
    
    @property
    def description(self) -> str:
        return "Description of what this producer does"
    
    def produce(self):
        # Generate and return work item, or None if no work available
        return work_item
```

### Blocking Node

```python
class MyBlocking(BlockingNode):
    @property
    def identifier(self) -> str:
        return "my_blocking"
    
    @property
    def label(self) -> str:
        return "My Blocking Node"
    
    @property
    def description(self) -> str:
        return "Description of what this node does"
    
    def process(self, data):
        # Process data synchronously
        return processed_data
```

### Non-Blocking Node

```python
class MyNonBlocking(NonBlockingNode):
    @property
    def identifier(self) -> str:
        return "my_nonblocking"
    
    @property
    def label(self) -> str:
        return "My Non-Blocking Node"
    
    @property
    def description(self) -> str:
        return "Description of what this node does"
    
    def process(self, data):
        # Process data (downstream runs independently)
        return processed_data
```

### IF Node

```python
class MyIF(IFNode):
    @property
    def identifier(self) -> str:
        return "my_if"
    
    @property
    def label(self) -> str:
        return "My IF Node"
    
    @property
    def description(self) -> str:
        return "Description of what this node does"
    
    def evaluate(self, data):
        # Return True for "yes" branch, False for "no" branch
        return condition_result
```

## License

This project is part of the Node Architecture Design system.

