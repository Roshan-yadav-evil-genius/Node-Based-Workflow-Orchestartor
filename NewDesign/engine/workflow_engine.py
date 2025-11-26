"""
Workflow Engine orchestrator.
Single Responsibility: Orchestrate workflow execution.
"""

import asyncio
from typing import List, Set, Any, Optional, Dict, Callable
from .workflow_graph import WorkflowGraph
from .execution_strategy import ExecutionStrategy
from .base_node import Node
from .producer_node import ProducerNode
from .blocking_node import BlockingNode
from .non_blocking_node import NonBlockingNode
from .if_node import IFNode


class WorkflowEngine:
    """
    Main workflow engine that orchestrates the execution of workflow nodes.
    Manages producer loops, blocking/non-blocking chains, and execution flow.
    """

    def __init__(
        self,
        graph: WorkflowGraph,
        execution_strategy: ExecutionStrategy
    ):
        """
        Initialize the workflow engine.
        
        Args:
            graph: Workflow graph containing nodes and connections
            execution_strategy: Execution strategy (async/thread/process)
        """
        self._graph = graph
        self._execution_strategy = execution_strategy
        self._producers: Set[ProducerNode] = set()
        self._running = False
        self._tasks: List[asyncio.Task] = []

    def register_producer(self, producer: ProducerNode) -> None:
        """
        Register a producer node to be executed by the engine.
        
        Args:
            producer: Producer node to register
            
        Raises:
            ValueError: If producer is not in the graph
        """
        if producer not in self._graph.get_all_nodes():
            raise ValueError(f"Producer {producer.identifier} not in graph")
        if not isinstance(producer, ProducerNode):
            raise ValueError(f"Node {producer.identifier} is not a ProducerNode")
        self._producers.add(producer)

    async def start(self) -> None:
        """
        Start the workflow engine.
        Begins execution of all registered producers in parallel.
        """
        if self._running:
            raise RuntimeError("Engine is already running")

        # Validate graph
        is_valid, error = self._graph.validate()
        if not is_valid:
            raise ValueError(f"Invalid workflow graph: {error}")

        if not self._producers:
            raise ValueError("No producers registered")

        self._running = True

        # Start all producers in parallel
        tasks = [
            self._handle_producer(producer)
            for producer in self._producers
        ]
        self._tasks = tasks

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False

    async def stop(self) -> None:
        """
        Stop the workflow engine.
        Cancels all running tasks.
        """
        if not self._running:
            return

        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete cancellation
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Shutdown execution strategy if it has a shutdown method
        if hasattr(self._execution_strategy, 'shutdown'):
            self._execution_strategy.shutdown()

    async def _handle_producer(self, producer: ProducerNode) -> None:
        """
        Handle a single producer's execution loop.
        
        Args:
            producer: Producer node to handle
        """
        while self._running:
            try:
                # Produce a work item
                work_item = await self._execution_strategy.execute_node(producer, None)

                if work_item is None:
                    # No work available, sleep briefly
                    await asyncio.sleep(0.1)
                    continue

                # Get downstream nodes
                downstream = self._graph.get_downstream(producer)

                if not downstream:
                    # No downstream nodes, continue loop
                    continue

                # Handle each downstream path
                for next_node in downstream:
                    if self._graph.contains_blocking_downstream(next_node):
                        # Blocking path - execute and wait
                        await self._execute_blocking_chain(next_node, work_item)
                    else:
                        # Non-blocking path - execute asynchronously
                        asyncio.create_task(
                            self._execute_nonblocking_chain(next_node, work_item)
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error and continue (in production, use proper logging)
                print(f"Error in producer {producer.identifier}: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def _execute_blocking_chain(
        self,
        start_node: Node,
        data: Any
    ) -> Any:
        """
        Execute a blocking chain of nodes synchronously.
        Producer waits for this chain to complete.
        
        Args:
            start_node: Starting node of the chain
            data: Initial input data
            
        Returns:
            Final output from the chain
        """
        return await self._execute_chain_recursive(start_node, data)

    async def _execute_nonblocking_chain(
        self,
        start_node: Node,
        data: Any
    ) -> None:
        """
        Execute a non-blocking chain of nodes asynchronously.
        Producer does not wait for this chain to complete.
        
        Args:
            start_node: Starting node of the chain
            data: Initial input data
        """
        try:
            await self._execute_chain_recursive(start_node, data)
        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error in non-blocking chain starting at {start_node.identifier}: {e}")

    async def _execute_chain_recursive(
        self,
        node: Node,
        data: Any
    ) -> Any:
        """
        Recursively execute a chain of nodes.
        
        Args:
            node: Current node to execute
            data: Input data for the node
            
        Returns:
            Output data from the chain
        """
        # Execute current node
        output = await self._execution_strategy.execute_node(node, data)

        # Handle IF node branching
        if isinstance(node, IFNode):
            return await self._handle_if_node(node, output)

        # Get downstream nodes
        downstream = self._graph.get_downstream(node)

        if not downstream:
            return output

        # Execute all downstream paths
        # For non-IF nodes, execute all downstream sequentially
        current_data = output
        for next_node in downstream:
            current_data = await self._execute_chain_recursive(next_node, current_data)

        return current_data

    async def _handle_if_node(
        self,
        if_node: IFNode,
        output: Dict[str, Any]
    ) -> Any:
        """
        Handle IF node execution and route to appropriate branch.
        
        Args:
            if_node: The IF node that was executed
            output: Output from IF node (contains 'result', 'data', 'branch')
            
        Returns:
            Output from the selected branch
        """
        branch = output.get("branch", "yes")
        data = output.get("data")

        # Get downstream nodes for the selected branch
        downstream = self._graph.get_downstream(if_node, branch=branch)

        if not downstream:
            return data

        # Execute the selected branch
        current_data = data
        for next_node in downstream:
            current_data = await self._execute_chain_recursive(next_node, current_data)

        return current_data

    def is_running(self) -> bool:
        """
        Check if the engine is currently running.
        
        Returns:
            True if engine is running, False otherwise
        """
        return self._running

