# Workflow Orchestrator — Final Requirements (merged)


The Workflow Orchestrator is the central coordinator that runs workflows composed of interconnected nodes arranged into one or more **loops**. Each loop is an isolated execution track controlled by a single Producer. Loops run inside either a thread or process execution pool; the LoopManager’s core execution model is synchronous (per v3). However, **node implementations are allowed to use `async/await` internally** for flexibility — from the LoopManager’s perspective a node still "blocks" until it returns.

---

## 2. Core Concepts

### 2.1 Node (BaseNode)
* Smallest executable unit. Each node receives:
  * `NodeConfig` — static initialization/config data.
  * `NodeData` — runtime payload for the iteration.
* From the LoopManager’s viewpoint **every node is blocking**: the LoopManager **waits** for `node.execute(...)` to complete before moving on.
* **Internal node flexibility:** nodes may internally use `async/await`, spawn threads, call `asyncio.run`, use background workers, etc., but they must ensure `execute()` returns only when the node’s synchronous contract is satisfied.

### 2.2 Node Types
* **ProducerNode**
  * Marks loop start. Called first each iteration.
  * Produces or fetches work units that drive the loop.
  * When an iteration completes (per execution flow rules), the LoopManager returns control to Producer to begin next iteration.
* **BlockingNode**
  * Performs work that must be completed prior to continuation.
  * The LoopManager waits for the Blocking node **and all downstream Blocking children** in its synchronous chain to finish before proceeding.
* **Non-Blocking Node**
  * Semantically marks loop-end in the execution model.
  * From the LoopManager’s perspective it still blocks while executing, then the iteration ends and control returns to Producer.
  * Nodes can (internally) offload long side-effects — but the node must ensure its `execute()` completes in a way consistent with loop semantics.

> **Important:** Although we keep the names (Blocking / Non-Blocking) for intent and developer guidance, the final merged rule is that **the LoopManager waits for each node's `execute()`**; Non-Blocking nodes are treated as the iteration end marker.

### 2.3 QueueNode and QueueReader

**QueueNode**

* Inherits from **NonBlockingNode**.
* Writes/publishes data to a Redis-backed queue via `QueueManager.push()`.
* Acts as the **loop end marker** in the execution model.
* Still executes synchronously from the LoopManager’s perspective, but may use `async/await` internally.
* After its execution finishes, the LoopManager immediately returns to the Producer to start the next iteration.

**QueueReader**

* Inherits from **ProducerNode**.
* Begins a new loop iteration by reading from a Redis queue using `QueueManager.pop()`.
* Internal logic (blocking pop, timeouts, backoff) is up to the developer.
* The orchestrator treats it as the **loop entry point** (Producer).

---

## 3. Execution Model & Flow

1. **Loop iteration begins**: LoopManager invokes the **ProducerNode**.
2. **Synchronous chain**: LoopManager sequentially invokes downstream nodes. Each node's `execute()` must return before continuing.
3. **Iteration end marker**: When the LoopManager calls a **Non-Blocking Node** (per flow design), that node completes synchronously and the iteration ends.
4. **Restart**: LoopManager returns control to ProducerNode for the next iteration.

*Loops run inside ThreadPool or ProcessPool execution contexts. The LoopManager core is synchronous and does not rely on an `asyncio` event loop for orchestration control.*

---

## 4. Concurrency & Async/Blocking Reconciliation

* **LoopManager / Orchestrator:** synchronous control flow; runs in threads/processes.
* **Nodes:** allowed to use `async/await` internally. Node authors must ensure:
  * The node’s public `execute()` contract is synchronous from the LoopManager’s perspective (i.e., `execute()` returns only when the node has reached the state that should allow the orchestrator to continue the chain).
  * If using asyncio internally, node implementations must manage their own event loop boundaries (e.g., `asyncio.run(...)`, manage loop creation per thread, or use appropriate adaptors).
* **Reason:** outputs of a node directly become inputs of downstream nodes; synchronous completion guarantees consistent handoff and deterministic loop timing while still allowing modern async code within nodes.

---

## 5. Cross-loop Communication — QueueManager (Redis-backed)

* The orchestrator **must** provide a `QueueManager` abstraction that uses Redis as the backing store (multi-process safe).
* `QueueManager` responsibilities:
  * Create/maintain named queues (dictionary) accessible to all loops/processes.
  * Provide `push(queue_name, data)` and `pop(queue_name, timeout)` / blocking pop semantics.
  * Handle serialization, connection pooling, and BPOP/BRPOP semantics as needed.
* **Queue semantics:**
  * A `QueueNode` writes to a named queue using `QueueManager`.
  * A `QueueReader` (ProducerNode) pops from the same named queue to start its loop iteration.

---

## 6. Lifecycle, State, Observability

* Orchestrator responsibilities:
  * Load workflows (React Flow JSON) and initialize `NodeConfig`.
  * Build loop graphs from edges and nodes.
  * Start / stop / pause / resume loops.
  * Assign pool types (ThreadPool or ProcessPool) per loop.
  * Maintain loop state (running, stopped, error) and node state (healthy, failing).
  * Expose logs per loop/node and metrics: iterations/sec, errors, queue depth, DLQ size, etc.

---

## 7. Workflow Input Contract

* Input format: **React Flow JSON** with `nodes` (each with `id`, `type`, `data` => NodeConfig) and `edges` (connections used to construct execution chains).
* The orchestrator uses edges to determine immediate downstream nodes and whether paths contain Blocking semantics.

---

## 8. Error Handling (v3: Immediate Failure Policy)

* **Zero automatic retries.** No automatic retry attempts by the orchestrator for failing nodes.
* **On node error:**
  * Capture exception and related `NodeData` payload.
  * Send failed payload + exception details to a **Dead-Letter Queue (DLQ)** (mandatory).
  * Immediately terminate the current iteration and return control to the Producer to begin the next iteration.
* **Rationale:** Fail-fast design to preserve throughput and isolate recurring bad payloads into the DLQ for offline inspection.

---

## 9. LoopManager Responsibilities (summary)

* Keep reference to ProducerNode.
* Execute node chain in defined order; wait for each node’s `execute()` to return.
* Handle data transformation and pass NodeData to downstream nodes.
* Delegate pool allocation (thread or process) to orchestrator config.
* Report node-level exceptions and route failed payloads to DLQ.

**LoopManager must NOT**:
* Own or manage queue storage internals — it uses the orchestrator-level `QueueManager` abstraction for cross-loop communication.
* Implicitly retry failed nodes.

---

## 10. Developer Guidance & Expectations

* Node authors should:
  * Treat `execute()` as the synchronous contract with the orchestrator.
  * Use `async/await` internally if it simplifies I/O, but ensure `execute()` only returns when the node’s synchronous obligations are met.
  * When implementing QueueReader as a Producer, handle blocking pop semantics via `QueueManager.pop(...)` inside their node code.
* System implementers should:
  * Provide clear data contracts (schemas) for NodeData passed between nodes.
  * Ensure Redis QueueManager is fault tolerant and monitored (connection health, queue lengths, DLQ).
  * Provide observability (logs, metrics, health endpoints) per loop and node.

---

## 11. Open Implementation Decisions (left to implementation, not required to block spec)
* Exact serialization format for NodeData over Redis (e.g., JSON, CBOR, protobuf).
* DLQ retention/eviction policy and tooling for reprocessing DLQ items.
* Concrete retry or backoff strategies for external repair tools (kept out of orchestrator; DLQ is used instead).

---

## 12. Glossary
* **LoopManager:** the per-loop executor that runs nodes in sequence and enforces synchronous iteration semantics.
* **ProducerNode:** starts an iteration (QueueReader is treated as a Producer).
* **BlockingNode:** must finish (and downstream blocking chain must finish) before continuing.
* **Non-Blocking Node:** marks iteration end in v3 model; still executed synchronously.
* **QueueManager:** Redis-backed queue abstraction for cross-loop comms.
* **DLQ:** Dead-Letter Queue storing failed NodeData + error context.

---

### Change log — how conflicts were resolved
* **Execution semantics & node blocking:** v3 chosen as authoritative — LoopManager waits for all nodes. (You confirmed v3 priority.)
* **Async inside nodes:** allowed explicitly (you requested `async/await` allowed internally), while preserving the LoopManager’s synchronous contract.
* **Queue transport:** Redis-backed `QueueManager` mandated (you confirmed).
* **Error handling:** v3 Immediate Failure Policy adopted — zero retries + mandatory DLQ.
* **QueueReader role:** kept as ProducerNode type (you confirmed that final type classification matters; internal logic left to developer).

---

If any of the above items are off from what you intended, point out the exact lines/sections and I’ll update immediately.

