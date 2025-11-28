# Workflow Orchestrator Requirements

## 1. Overview

The Workflow Orchestrator is the central coordination system responsible for running workflows composed of interconnected nodes arranged into one or more **loops**. Each loop is an isolated execution track controlled by a single Producer. The entire codebase uses **async/await** throughout — LoopManager, nodes, and QueueManager all operate asynchronously. Loops run inside asyncio event loops, thread pools, or process pools.

The orchestrator ensures that nodes inside one loop and nodes across different loops communicate predictably while preserving each node's execution semantics.

### 1.1 Key Principles

* **Isolation:** Loops are fully isolated execution tracks running in separate pools (asyncio, threads, or processes).
* **Decoupling:** Cross-loop data flow is handled exclusively via an abstracted, multi-process safe queue system (Redis).
* **Predictability:** Node execution behavior is strictly determined by the **node type** and the **LoopManager**'s async execution strategy.
* **Fail-Fast:** Immediate failure policy with zero retries to preserve throughput and isolate problematic payloads.
* **Async-First:** The entire codebase uses async/await patterns throughout for optimal I/O performance and scalability.

---

## 2. Core Concepts

### 2.1 Node (BaseNode)

A **Node** is the smallest executable unit inside a workflow loop. Each node inherits from `BaseNode`.

* Each node receives two objects:
  * `NodeConfig` — static initialization/config settings
  * `NodeData` — runtime payload for the iteration
* All nodes implement an **async `execute()` method**: the LoopManager **awaits** `await node.execute(...)` before moving on.
* Nodes use `async/await` throughout their implementation for I/O operations, queue access, and any asynchronous work.
* Nodes never manage their own concurrency; they simply "run" when invoked by the LoopManager via async execution.

### 2.2 Node Types

The orchestrator supports three fundamental node types:

#### ProducerNode

* Marks loop start. Called first each iteration.
* Starts and controls the loop. Controls timing and triggers downstream nodes.
* Produces or fetches work units that drive the loop.
* When an iteration completes (per execution flow rules), the LoopManager returns control to Producer to begin next iteration.
* Designed to allow other parallel loops to run independently.

#### BlockingNode

* Performs work that must be completed prior to continuation.
* Executes work that must be completed *before* upstream nodes (like the Producer) continue.
* The LoopManager awaits the Blocking node **and all downstream Blocking children** in its async chain to complete before proceeding.
* Runs asynchronously and passes output to the next node if it exists.
* Awaits the entire downstream chain to complete before returning control.
* Forms strict **sequential async paths** within the workflow.

#### Non-Blocking Node

* Can semantically mark loop-end in the execution model (when present).
* Performs a computation or transformation but does not force the Producer to wait for downstream operations.
* From the LoopManager's perspective it awaits the node's execution, then the iteration ends and control returns to Producer.
* Nodes can offload long side-effects asynchronously — the node must ensure its `execute()` completes in a way consistent with loop semantics.
* Useful for creating **async boundaries** within the workflow.

> **Important:** Although we keep the names (Blocking / Non-Blocking) for intent and developer guidance, the final rule is that **the LoopManager awaits each node's `execute()`**. A loop iteration ends when either: (1) a Non-Blocking node is encountered, OR (2) there are no more downstream nodes to execute (end of chain reached). Non-Blocking nodes are not required to mark loop end.

### 2.3 Examples of Producer and NonBlockingNode 

**QueueNode**

* Inherits from **NonBlockingNode**.
* Writes/publishes data to a Redis-backed queue via `await QueueManager.push()`.
* Can act as a **loop end marker** in the execution model (when used as the last node in a chain).
* Executes asynchronously using `async/await`.
* After its execution completes, the LoopManager immediately returns to the Producer to start the next iteration.
* Pushes data to a queue, enabling data to be consumed in a different loop.

**QueueReader**

* Inherits from **ProducerNode**.
* Begins a new loop iteration by reading from a Redis queue using `await QueueManager.pop()`.
* Awaits data from a queue (`pop`) and starts a new loop iteration.
* Internal logic (async pop, timeouts, backoff) is up to the developer.
* The orchestrator treats it as the **loop entry point** (Producer).

### 2.4 Loop

A **Loop** is a continuous execution track controlled by a single **ProducerNode**. It contains a chain of Blocking and NonBlocking nodes.

* **Multiple Loops in a Workflow:** A single workflow can contain multiple Producer nodes, each creating its own independent loop. The orchestrator manages all loops concurrently.
* **Loop Boundaries:** A loop iteration ends when either:
  * A Non-Blocking node is encountered, OR
  * There are no more downstream nodes to execute (end of chain reached)
* Each loop runs in its own execution pool:
  * **Asyncio Event Loop** — for async/await-based execution (primary mode)
  * **ThreadPool** — for thread-based execution (with async support)
  * **ProcessPool** — for process-based execution (with async support)
* **Note:** Asyncio is the **primary and recommended** pool type for the LoopManager's core execution flow. All nodes use async/await throughout.
* Loops behave like async pipelines with timing rules defined by the node types.
* Loops are fully isolated execution tracks that can run in parallel.

---

## 3. Execution Model & Flow

The execution flow is **fully asynchronous** within each loop. All nodes must implement async `execute()` methods and use `async/await` throughout.

### 3.1 The Execution Cycle

The LoopManager executes the flow sequentially (awaiting each node) until either:
- It hits a Non-Blocking Node, OR
- There are no more downstream nodes to execute

At this point, the iteration is complete.

1. **Start:** LoopManager awaits the **Producer Node** (`await producer.execute(...)`).
2. **Middle:** LoopManager sequentially awaits all **Blocking Nodes**. Each node's `execute()` must complete before continuing.
3. **End:** The iteration ends when either:
   - LoopManager awaits a **Non-Blocking Node** (the async execution chain ends here), OR
   - There are no more downstream nodes to execute (end of chain reached)
4. **Restart:** Immediately after the iteration ends, the LoopManager **jumps back to the Producer Node** to initiate the next iteration.

### 3.2 Execution Rules Summary

| Node Type | Execution Model | LoopManager Behavior | Use Case |
|-----------|-----------------|---------------------|----------|
| **Producer** | Async (`async execute()`) | Awaited first, re-invoked after iteration completes | Starting loops, generating jobs, orchestrating flow |
| **Blocking** | Async (`async execute()`) | Awaits node and all downstream Blocking children to complete | Critical sequential operations, sequential async processing |
| **Non-Blocking** | Async (`async execute()`) | Awaits node execution, then iteration ends | Async branching, offloading long tasks, creating async boundaries |

### 3.3 Async Execution Model

* **LoopManager / Orchestrator:** fully async control flow using `async/await`; runs in asyncio event loops, thread pools, or process pools.
* **Nodes:** all nodes implement `async execute()` methods. Node authors must:
  * Implement `async def execute(node_data: NodeData) -> NodeData` for all nodes.
  * Use `async/await` for all I/O operations, queue access, and asynchronous work.
  * Ensure `execute()` completes (via await) only when the node has reached the state that should allow the orchestrator to continue the chain.
* **Reason:** outputs of a node directly become inputs of downstream nodes; async completion guarantees consistent handoff and deterministic loop timing while enabling optimal I/O performance and scalability.

*Loops run inside asyncio event loops (primary), ThreadPool, or ProcessPool execution contexts. The LoopManager core uses async/await throughout for orchestration control.*

---

## 4. Multiple Loops in a Single Workflow

A single workflow can contain multiple Producer nodes, each creating its own independent loop. The orchestrator must identify, create, and manage all loops concurrently.

### 4.1 Loop Identification

* **Each ProducerNode starts a new loop.** When the orchestrator loads a workflow, it identifies all Producer nodes in the graph.
* **Loop boundaries are determined by:**
  * Starting point: A ProducerNode (or QueueReader acting as Producer)
  * Continuation: Blocking nodes that form the sequential chain
  * End point: Either a Non-Blocking node OR the end of the chain (no more downstream nodes)
* **Multiple Non-Blocking nodes** can exist in a workflow, each marking the end of its respective loop iteration.

### 4.2 Concurrent Loop Management

* The orchestrator creates a **separate LoopManager for each Producer node**.
* All loops run concurrently and independently in their own execution pools.
* Loops are fully isolated — a failure in one loop does not affect others.
* The orchestrator coordinates all loops, managing their lifecycle, state, and cross-loop communication.

### 4.3 Example Workflow Structure

A workflow might contain:
* **Loop 1:** ProducerNode → BlockingNode → NonBlockingNode (QueueNode)
* **Loop 2:** QueueReader (Producer) → BlockingNode → BlockingNode (ends at chain end)
* **Loop 3:** ProducerNode → BlockingNode → BlockingNode (ends at chain end)

All three loops run concurrently, with Loop 1 feeding data to Loop 2 via the queue.

---

## 5. Cross-Loop Communication — QueueManager (Redis-backed)

Cross-loop data flow is achieved through an abstracted `QueueManager` API, which manages Redis-backed queues stored in the Orchestrator.

### 5.1 Redis Queue Dictionary

* The **Workflow Orchestrator** maintains a dictionary of named queues, where each queue instance is inherently **multi-process safe** (backed by Redis).
* This approach guarantees predictable communication regardless of the sender/receiver pool types (Thread, Process).
* Queues are not owned by the LoopManager; they are managed at the orchestrator level.

### 5.2 QueueManager API Contract

Nodes access the queue system only through the high-level `QueueManager` API, which abstracts away Redis details (serialization, connection management, BPOP/BRPOP logic). All QueueManager methods are async.

| Node Type | Action | API Call Abstraction |
|-----------|--------|---------------------|
| **QueueNode** | Writes data to a queue | `await orchestrator.queue_manager.push(queue_name, data)` |
| **QueueReader** | Reads data from a queue | `await orchestrator.queue_manager.pop(queue_name, timeout)` |

The **QueueReader Node** in Loop B will use the `pop` method to await until data is available in the named queue.

### 5.3 Cross-Loop Data Flow

When a node pushes data to a queue:

* Workflow Orchestrator registers the event through the QueueManager.
* Orchestrator routes the message to all LoopManagers interested in that queue.
* Loop B receives data as NodeData for its QueueReader node.

This enables plug-and-play pipelines and decouples loops without requiring them to know each other's runtime details.

---

## 6. Workflow Orchestrator Responsibilities

### 6.1 Lifecycle Management

* Load workflows (React Flow JSON) and initialize `NodeConfig` for each node.
* **Identify all Producer nodes** in the workflow graph — each Producer node creates a new independent loop.
* **Build loops from node graphs** (using edges to construct execution chains):
  * For each Producer node, trace downstream nodes following edges
  * A loop continues through Blocking nodes
  * A loop iteration ends when a Non-Blocking node is encountered OR when there are no more downstream nodes
* **Create a LoopManager for each Producer node** — the orchestrator manages all loops concurrently.
* Start, stop, pause, and resume all loops (all operations are async).
* Assign pool types (Asyncio Event Loop, ThreadPool, or ProcessPool) per loop.
* **Coordinate multiple loops** running in parallel, ensuring proper isolation and cross-loop communication.

### 6.2 Loop Execution

The orchestrator manages:

* How ProducerNodes trigger iterations across all loops.
* How Blocking and NonBlocking nodes chain execution within each loop.
* How errors are propagated or isolated per node/loop.
* **Concurrent execution** of multiple loops, each running independently in their own execution pool.

### 6.3 Communication Between Loops

The orchestrator provides an internal messaging interface (via QueueManager) enabling:

* Data routed to QueueNode in Loop A to be consumed in Loop B.
* Message passing without tightly coupling loops.

This avoids loops needing to know each other's runtime details.

### 6.4 State Handling

The orchestrator maintains:

* Loop state (running, stopped, error).
* Node state (healthy, failing).

It may optionally support persistence for crash recovery.

### 6.5 Health, Logging, and Observability

The orchestrator should expose:

* Logs per loop and per node.
* Health indicators for nodes.
* Metrics: iterations/sec, errors, queue depth, DLQ size, etc.

---

## 7. LoopManager Responsibilities

LoopManager handles one loop at a time:

* Maintains reference to the ProducerNode.
* Executes node chains in defined order; awaits each node's `execute()` to complete.
* Handles data transformation and passes NodeData to downstream nodes.
* Delegates pool allocation (asyncio, thread, or process) to orchestrator config.
* Reports node-level exceptions and routes failed payloads to DLQ (all operations are async).

**LoopManager must NOT**:

* Own or manage queue storage internals — it uses the orchestrator-level `QueueManager` abstraction for cross-loop communication.
* Implicitly retry failed nodes.
* Communicate directly with other LoopManagers.

All cross-loop data flows go through orchestrator-level messaging.

---

## 8. Workflow Input Contract

* Input format: **React Flow JSON** with:
  * **Nodes**: List of node objects including `id`, `type` (e.g., 'producer', 'blocking', 'non-blocking'), and `data` (which maps to the `NodeConfig`).
  * **Edges**: List of connections defining the flow and used to prepare the node mapping (the execution chain).
* The orchestrator uses edges to determine immediate downstream nodes and whether paths contain Blocking semantics.

---

## 9. Error Handling (Immediate Failure Policy)

The system enforces an **Immediate Failure Policy** with **zero retries** to prioritize overall system throughput and stability.

### 9.1 Zero Retries

* **Zero automatic retries.** There will be **NO automatic retries** for any failing node.
* No automatic retry attempts by the orchestrator for failing nodes.

### 9.2 Action on Error

As soon as an unhandled exception occurs in **any node** (Producer, Blocking, or Non-Blocking):

* Capture exception and related `NodeData` payload.
* Send failed payload + exception details to a **Dead-Letter Queue (DLQ)** (mandatory). This is a mandatory terminal action for the failed payload to prevent data loss and allow for external investigation.
* The LoopManager must **immediately send control back to the Producer Node**. This terminates the failed iteration and restarts the loop process with the next unit of work.

### 9.3 Failure Isolation

* All node-level exceptions must be captured and reported by the LoopManager.
* Failure isolation is mandatory: The Orchestrator must support policies to prevent a single node or loop failure from crashing the entire system.
* Loops can continue or be paused based on policy, but the orchestrator may isolate failures to avoid system-wide crash.

### 9.4 Rationale

Fail-fast design to preserve throughput and isolate recurring bad payloads into the DLQ for offline inspection.

---

## 10. Developer Guidance & Expectations

### 10.1 Node Authors

Developers implementing nodes should:

* Implement `async def execute(node_data: NodeData) -> NodeData` for all nodes.
* Use `async/await` throughout for all I/O operations, queue access, and asynchronous work.
* Ensure `execute()` completes (via await) only when the node's obligations are met.
* When implementing QueueReader as a Producer, handle async pop semantics via `await QueueManager.pop(...)` inside their node code.
* Understand that nodes follow strict async timing semantics.
* Never manage their own concurrency; nodes simply "run" when invoked via async execution.

### 10.2 System Implementers

Developers implementing the orchestrator should:

* Provide clear data contracts (schemas) for NodeData passed between nodes.
* Ensure Redis QueueManager is fault tolerant and monitored (connection health, queue lengths, DLQ).
* Provide observability (logs, metrics, health endpoints) per loop and node.
* Understand that loops are fully isolated execution tracks.
* Understand that queue nodes enable multi-loop coordination.
* Understand that the orchestrator controls lifecycle, messaging, and concurrency.

### 10.3 Key Developer Expectations

Developers should understand:

* Nodes follow strict timing semantics.
* Loops are fully isolated execution tracks.
* Queue nodes enable multi-loop coordination.
* Orchestrator controls lifecycle, messaging, and concurrency.
* Loops run using Asyncio Event Loop (primary), ThreadPool, or ProcessPool.
* All nodes use async/await throughout; LoopManager awaits all node executions.

---

## 11. Open Implementation Decisions

The following items are left to implementation and are not required to block the specification:

* Exact serialization format for NodeData over Redis (e.g., JSON, CBOR, protobuf).
* DLQ retention/eviction policy and tooling for reprocessing DLQ items.
* Concrete retry or backoff strategies for external repair tools (kept out of orchestrator; DLQ is used instead).
* Specific health endpoint formats and metric collection mechanisms.

---

## 12. Glossary

* **BaseNode:** The base class from which all nodes inherit.
* **BlockingNode:** Must finish (and downstream blocking chain must finish) before continuing.
* **DLQ:** Dead-Letter Queue storing failed NodeData + error context.
* **Loop:** A continuous execution track controlled by a single ProducerNode, running in an isolated pool (Asyncio Event Loop, ThreadPool, or ProcessPool).
* **LoopManager:** The per-loop executor that runs nodes in sequence and enforces async iteration semantics using await.
* **NodeConfig:** Static initialization/config data passed to nodes during initialization.
* **NodeData:** Runtime payload passed to nodes during execution.
* **Non-Blocking Node:** Marks iteration end in the execution model; executed asynchronously using await.
* **ProducerNode:** Starts an iteration (QueueReader is treated as a Producer).
* **QueueManager:** Redis-backed queue abstraction for cross-loop communication.
* **QueueNode:** A NonBlockingNode that writes data to a Redis queue.
* **QueueReader:** A ProducerNode that reads data from a Redis queue to start a loop iteration.
* **Workflow Orchestrator:** The central coordination system that manages loops, nodes, and cross-loop communication.

---

## 13. Change Log — Conflict Resolution

This section documents how conflicts between different versions were resolved, with priority given to higher version numbers (v4 > v3 > v2 > v1 > v0).

### 13.1 Execution Semantics & Node Blocking

* **v0-v1:** Non-blocking nodes return immediately to Producer.
* **v3-v4:** ALL nodes block from LoopManager perspective; Non-Blocking marks iteration end.
* **Resolution:** v3/v4 chosen as authoritative — LoopManager waits for all nodes. Non-Blocking nodes are treated as iteration end markers.

### 13.2 Pool Types

* **v1:** ThreadPool, Asyncio event loop, ProcessPool.
* **v3-v4:** Only ThreadPool or ProcessPool (no asyncio for LoopManager).
* **Updated Resolution (2024):** Asyncio Event Loop is now the **primary and recommended** pool type. The entire codebase uses async/await throughout. ThreadPool and ProcessPool are also supported with async capabilities.

### 13.3 Error Handling

* **v1-v2:** General error handling with optional retries.
* **v3-v4:** Immediate Failure Policy with zero retries + mandatory DLQ.
* **Resolution:** v3/v4 Immediate Failure Policy adopted — zero retries + mandatory DLQ.

### 13.4 QueueReader/QueueNode Classification

* **v0-v1:** Not explicitly defined.
* **v2-v4:** QueueReader = ProducerNode, QueueNode = NonBlockingNode.
* **Resolution:** v2/v3/v4 definitions adopted — QueueReader inherits from ProducerNode, QueueNode inherits from NonBlockingNode.

### 13.5 Async Execution Model

* **v0-v3:** Not explicitly addressed.
* **v4:** Explicitly allows `async/await` internally while preserving LoopManager's synchronous contract.
* **Updated Resolution (2024):** The entire codebase now uses async/await throughout. All nodes implement `async def execute()`, and LoopManager uses await for all node executions. This is a fundamental architectural change from the original v4 specification.

### 13.6 Queue Transport

* **v1:** General messaging interface.
* **v2-v4:** Redis-backed QueueManager mandated.
* **Resolution:** v2/v3/v4 adopted — Redis-backed QueueManager is mandatory for cross-loop communication.

---

## 14. Architecture Diagram Reference

For a visual representation of the node architecture, refer to `Node Architecture.png` in the project directory.

---

*This document consolidates requirements from versions v0 through v4, with priority given to higher version numbers when conflicts exist. All clarifications and refinements from later versions have been incorporated to provide a comprehensive and unambiguous specification.*

**Note (2024 Update):** This document has been updated to reflect that the entire codebase uses async/await throughout. All nodes implement async `execute()` methods, LoopManager uses await for all operations, and Asyncio Event Loop is the primary execution pool type. This represents a significant architectural evolution from the original synchronous execution model.

