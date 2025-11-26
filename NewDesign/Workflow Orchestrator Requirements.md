# Workflow Orchestrator Requirements

## 1. Overview

The Workflow Orchestrator is the central coordination system responsible for running workflows composed of interconnected nodes. Each workflow may contain one or more **loops**, and each loop represents an independent execution track. Loops can run using different pool types such as **threads**, **asyncio**, or **multiprocessing**, depending on the workflow’s requirements.

The orchestrator ensures that nodes inside one loop and nodes across different loops communicate predictably while preserving each node’s execution semantics.

---

## 2. Core Concepts

### 2.1 Node

A **Node** is the smallest executable unit inside a workflow loop. Each node inherits from `BaseNode`. We support three node types:

* **ProducerNode** — Starts and controls the loop. Controls timing and triggers downstream nodes.
* **BlockingNode** — Requires completion of its chain before returning control.
* **NonBlockingNode** — Executes synchronously but side‑effects (DB writes, queue pushes, triggers) happen independently.

Each node receives two objects:

* `NodeConfig` — initialization/config settings
* `NodeData` — incoming data during a loop run

Nodes never manage their own concurrency; they simply “run” when invoked.

### 2.2 Loop

A **Loop** is a continuous execution track controlled by a single **ProducerNode**. It contains a chain of Blocking and NonBlocking nodes.

Each loop runs in its own execution pool:

* ThreadPool
* Asyncio event loop
* ProcessPool

Loops behave like pipelines with timing rules defined by the node types.

### 2.3 Queue Nodes and Cross‑Loop Communication

Queues are just another type of node. They are not owned by the LoopManager.

Loops may:

* Push data into a QueueNode
* Read data from the QueueNode in a different loop

The orchestrator must ensure coordination across loops, delivering data produced in one loop into another loop that is consuming the same queue.

---

## 3. Workflow Orchestrator Responsibilities

### 3.1 Lifecycle Management

* Load workflows and initialize NodeConfig for each node
* Build loops from node graphs
* Start, stop, pause, and resume loops
* Assign pool types per loop (thread, asyncio, or process)

### 3.2 Loop Execution

The orchestrator manages:

* How ProducerNodes trigger iterations
* How Blocking and NonBlocking nodes chain execution
* How errors are propagated or isolated per node/loop

### 3.3 Communication Between Loops

The orchestrator provides an internal messaging interface enabling:

* Data routed to QueueNode in Loop A to be consumed in Loop B
* Message passing without tightly coupling loops

This avoids loops needing to know each other’s runtime details.

### 3.4 State Handling

The orchestrator maintains:

* Loop state (running, stopped, error)
* Node state (healthy, failing, retrying)

It may optionally support persistence for crash recovery.

### 3.5 Health, Logging, and Observability

The orchestrator should expose:

* Logs per loop and per node
* Health indicators for nodes
* Metrics (iterations/sec, errors, queue depth, etc.)

---

## 4. Execution Rules

### 4.1 Producer Node Rules

* Controls the loop iteration
* Runs first in each loop
* Waits for Blocking nodes to complete
* Does **not** wait for NonBlocking nodes

### 4.2 Blocking Node Rules

* Executes synchronously
* Forwards its output to the next node
* Next iteration only starts after completion of all downstream Blocking nodes

### 4.3 NonBlocking Node Rules

* Executes synchronously but does not block loop
* Side effects may run independently
* Loop continues immediately

---

## 5. LoopManager Responsibilities

LoopManager handles one loop at a time:

* Maintains reference to the ProducerNode
* Executes node chains in defined order
* Handles data transformation between nodes
* Delegates concurrency to Workflow Orchestrator (pool type)

LoopManager **does not**:

* Manage queues internally
* Communicate directly with other LoopManagers

All cross‑loop data flows go through orchestrator-level messaging.

---

## 6. Cross‑Loop Data Flow

When a node pushes data to a queue:

* Workflow Orchestrator registers the event
* Orchestrator routes the message to all LoopManagers interested in that queue
* Loop B receives data as NodeData for its QueueReader node

This enables plug‑and‑play pipelines.

---

## 7. Error Handling Expectations

For reliability:

* Node-level exceptions must be captured and reported
* Loops can continue or be paused based on policy
* Orchestrator may isolate failures to avoid system-wide crash

---

## 8. Developer Expectations / Summary

Developers should understand:

* Nodes follow strict timing semantics
* Loops are fully isolated execution tracks
* Queue nodes enable multi-loop coordination
* Orchestrator controls life cycle, messaging, and concurrency
* Loops can run using multiple concurrency models

The orchestrator is the conductor; nodes are musicians; queues are message sheets; loops are orchestral sections playing in sync.

---

If additional details or examples are needed (sequence diagrams, data contracts, or a full lifecycle chart), these can be added next.
