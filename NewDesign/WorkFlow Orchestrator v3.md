# Clarification Document: Final Workflow Orchestrator Execution Rules

This document consolidates the final, non-negotiable rules governing the $\text{LoopManager}$ execution and node behavior, resolving all prior ambiguities.

## 1. ⚙️ Unified Execution and Concurrency Model

The execution flow is **strictly synchronous** within each loop, and all nodes must be implemented accordingly.

| Element | Final Rule | Rationale/Implication |
| :--- | :--- | :--- |
| **All Nodes** | **All Nodes are Blocking.** The $\text{LoopManager}$ must **wait for the full execution** of the $\text{Producer}$, $\text{Blocking}$, and $\text{Non-Blocking}$ nodes before proceeding. | There is **no asynchronous execution** within the core $\text{LoopManager}$ thread. Any I/O-wait logic is permitted in the node itself. |
| **Concurrency Pool** | Loops operate exclusively within $\text{ThreadPool}$ or $\text{ProcessPool}$ environments. | **$\text{Asyncio}$ is not supported** for the $\text{LoopManager}$'s core execution flow due to its blocking nature. |
| **I/O Operations** | All I/O calls (DB access, Queue pushes, etc.) are **synchronous** relative to the LoopManager's thread. | The $\text{LoopManager}$ thread will block while the node performs its work, which is acceptable because the loop is isolated to a single thread/process. |

---

## 2. 🔁 Loop Flow Control (Producer and Non-Blocking Role)

The primary purpose of the $\text{Producer}$ and $\text{Non-Blocking}$ classifications is to define the start and end of the synchronous loop iteration.

### 2.1 The Execution Cycle

The $\text{LoopManager}$ executes the flow sequentially until it hits the $\text{Non-Blocking Node}$, at which point the iteration is complete.

1.  **Start:** $\text{LoopManager}$ calls the **Producer Node**.
2.  **Middle:** $\text{LoopManager}$ sequentially calls all **Blocking Nodes**.
3.  **End:** $\text{LoopManager}$ calls the **Non-Blocking Node** (the synchronous execution chain ends here).
4.  **Restart:** Immediately after the $\text{Non-Blocking Node}$ returns, the $\text{LoopManager}$ **jumps back to the Producer Node** to initiate the next iteration.



### 2.2 Final Node Classification

| Node Type | Function | Classification |
| :--- | :--- | :--- |
| **QueueReader** | Waits for data from a queue ($\text{pop}$) and starts a new loop iteration. | **Producer Node** (Loop Start Marker) |
| **QueueNode** | Pushes data to a queue ($\text{write}$) and exits the synchronous chain. | **Non-Blocking Node** (Loop End Marker) |

---

## 3. ⚠️ Immediate Failure Policy (Error Handling)

The system enforces an **Immediate Failure Policy** with **zero retries** to prioritize overall system throughput and stability.

* **Zero Retries:** There will be **NO automatic retries** for any failing node.
* **Action on Error:** As soon as an unhandled exception occurs in **any node** ($\text{Producer}$, $\text{Blocking}$, or $\text{Non-Blocking}$), the $\text{LoopManager}$ must **immediately send control back to the Producer Node**. This terminates the failed iteration and restarts the loop process with the next unit of work.
* **Mandatory Data Isolation (DLQ):** The failed $\text{NodeData}$ payload and its associated exception details **must be sent to a Dead-Letter Queue (DLQ)**. This is a mandatory terminal action for the failed payload to prevent data loss and allow for external investigation.