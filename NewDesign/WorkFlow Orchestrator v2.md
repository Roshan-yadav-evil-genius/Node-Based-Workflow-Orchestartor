This is a comprehensive **Architecture.md** document for your Workflow Orchestrator, integrating all the requirements and clarifications we've discussed.

I've structured it for immediate developer consumption, detailing the components, data contracts, and execution rules.

***

# Workflow Orchestrator Architecture Specification

## 1. 🚀 Overview and Goal

The Workflow Orchestrator is the central coordination system responsible for running workflows composed of interconnected nodes. Its primary goal is to provide a reliable, predictable, and scalable pipeline execution environment by managing concurrency and enforcing strict node execution semantics across different concurrency models.

### 1.1 Key Principles

* **Isolation:** Loops are fully isolated execution tracks running in separate pools (threads, processes, or asyncio).
* **Decoupling:** Cross-loop data flow is handled exclusively via an abstracted, multi-process safe queue system (Redis).
* **Predictability:** Node synchronous/asynchronous behavior is strictly determined by the **node type** and the **LoopManager**'s $\text{AWAIT}$ strategy.

---

## 2. 🏛️ Core Components

| Component | Responsibility | Key Interactions |
| :--- | :--- | :--- |
| **Workflow Orchestrator** | Lifecycle management (start/stop), assigning pool types, managing the Redis Queue Dictionary, and routing messages between loops. | **Loads JSON** input, **Initializes Nodes**, Manages **LoopManagers**. |
| **LoopManager** | Maintains a reference to the **ProducerNode**, executes the node chain in order, and controls the loop iteration timing based on node completion. | Runs within an execution **Pool**, calls **Node.execute()**. |
| **Node** | Smallest executable unit. Executes its task synchronously when invoked by the LoopManager. | Receives $\text{NodeData}$, returns updated $\text{NodeData}$ or signals completion. |
| **Redis Queue Dictionary** | Provides the inherently multi-process safe communication channel for all cross-loop data transfer [clarification]. Abstracted by the $\text{QueueManager}$ API. | Used by **QueueNode** (write) and **QueueReader** (read). |

### 2.1 Workflow Input Contract

The Orchestrator receives the workflow structure as a **React Flow JSON** containing:

* **Nodes**: List of node objects including `id`, `type` (e.g., 'producer', 'blocking', 'non-blocking'), and `data` (which maps to the $\text{NodeConfig}$).
* **Edges**: List of connections defining the flow and used to prepare the node mapping (the execution chain) [clarification].

---

## 3. 🧩 Node Execution Semantics and Rules

All nodes execute **synchronously** internally. The sync/async behavior is governed by the LoopManager's $\text{AWAIT}$ strategy.

| Node Type | Purpose | LoopManager $\text{AWAIT}$ Behavior | Downstream Task Handling |
| :--- | :--- | :--- | :--- |
| **1. Producer Node** | Starts the loop and generates work. | LoopManager calls this first and re-invokes it when the current iteration is complete. | **Invokes** all immediate downstream nodes. |
| **2. Blocking Node** | Executes work that must be completed before upstream continues. | **LoopManager AWAITS** the completion of this node and all of its downstream **Blocking** children. | Forwards output to the next node in the synchronous path. |
| **3. Non-Blocking Node** | Performs computation without forcing the Producer to wait for side-effects. | **LoopManager AWAITS** its internal synchronous execution, then **immediately returns control** to the Producer. | Any side-effects (DB writes, queue pushes, etc.) are handled independently via the $\text{QueueManager}$ API, running asynchronously. |


---

## 4. 🔗 Cross-Loop Communication (Redis Queue Abstraction)

Cross-loop data flow is achieved through an abstracted $\text{QueueManager}$ API, which manages Redis-backed queues stored in the Orchestrator.

### 4.1 Redis Queue Dictionary

* The **Workflow Orchestrator** maintains a dictionary of named queues, where each queue instance is inherently **multi-process safe** (backed by Redis) [clarification].
* This approach guarantees predictable communication regardless of the sender/receiver pool types ($\text{Thread}$, $\text{Process}$, $\text{Asyncio}$) [clarification].

### 4.2 QueueManager API Contract

Nodes access the queue system only through the high-level $\text{QueueManager}$ API, which abstracts away Redis details (serialization, connection management, $\text{BPOP}$ logic) [clarification].

| Node Type | Action | API Call Abstraction |
| :--- | :--- | :--- |
| **QueueNode (Producer)** | Writes data to a queue | `orchestrator.queue_manager.push(queue_name, data)` |
| **QueueReader (Consumer)** | Reads data from a queue | `orchestrator.queue_manager.pop(queue_name, timeout)` |

The **QueueReader Node** in Loop B will use the `pop` method to block (or $\text{AWAIT}$) until data is available in the named queue.

---

## 5. ⚠️ Error Handling and Reliability

### 5.1 Node-Level Exceptions
* All node-level exceptions must be captured and reported by the LoopManager.
* Failure isolation is mandatory: The Orchestrator must support policies to prevent a single node or loop failure from crashing the entire system.

### 5.2 State and Observability
* The Orchestrator maintains state for each Loop (running, stopped, error) and Node (healthy, failing).
* Required metrics include iterations/sec, errors, and queue depth.

---

**Next Steps for Implementation:**

The immediate next step is to define the **Node Retry Policy** (e.g., how many times a Blocking Node should retry before failing the loop) to formalize the error handling specified in Section 5.1.