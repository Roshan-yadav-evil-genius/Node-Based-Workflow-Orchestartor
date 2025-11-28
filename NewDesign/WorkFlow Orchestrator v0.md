# Node Architecture Requirements

This document explains the three node types in the workflow engine—**Producer**, **Non-Blocking**, and **Blocking**—and outlines their expected behavior, execution rules, and role within the workflow loop.

![Architecture Design](./Node%20Architecture.png)

---

## **1. Producer Node**

### **Purpose**

The Producer Node starts a workflow loop. It continuously generates or fetches new units of work and controls when the next iteration of the loop begins.

### **Execution Expectations**

* Executes synchronously.
* Initiates the workflow by producing new data or tasks.
* Continues to the next iteration **only after all connected Blocking Nodes have fully completed their work**.
* If it encounters a Non-Blocking Node, it **immediately regains control**, allowing the loop to continue without waiting for downstream processes.
* Designed to allow other parallel loops to run independently.

### **Key Outcomes**

* Guarantees controlled execution for blocking flows.
* Provides high throughput when connected to non-blocking flows.

---

## **2. Non-Blocking Node**

### **Purpose**

A Non-Blocking Node performs a computation or transformation but does not force the Producer to wait for downstream operations.

### **Execution Expectations**

* Runs synchronously internally.
* After finishing its task, it returns control immediately to the Producer.
* Any downstream operations (e.g., queue publishing, DB writes, triggers) run in **separate loops** or independent systems.
* Useful for creating **async boundaries** within the workflow.

### **Key Outcomes**

* Ensures high responsiveness for the Producer loop.
* Allows time‑consuming tasks to be handled asynchronously.
* Decouples upstream and downstream workflows.

---

## **3. Blocking Node**

### **Purpose**

A Blocking Node executes work that must be completed *before* upstream nodes (like the Producer) continue.

### **Execution Expectations**

* Triggered when new data arrives.
* Runs synchronously and passes output to the next node if it exists.
* Waits for the entire downstream chain to complete before returning control.
* Forms strict **synchronous paths** within the workflow.

### **Key Outcomes**

* Enforces sequential execution where required.
* Guarantees that dependent operations are completed before upstream resumes.

---

## **Overall Behavior Summary**

| Node Type        | Internal Execution | Control Return Behavior                                            | Use Case                                            |
| ---------------- | ------------------ | ------------------------------------------------------------------ | --------------------------------------------------- |
| **Producer**     | Sync               | Waits for blocking nodes, immediate return from non‑blocking nodes | Starting loops, generating jobs, orchestrating flow |
| **Non‑Blocking** | Sync               | Immediate return to Producer                                       | Async branching, offloading long tasks              |
| **Blocking**     | Sync               | Waits for downstream completion                                    | Critical synchronous operations                     |

---

## **Workflow Design Principles**

* All nodes execute synchronously **inside** themselves.
* Async vs sync behavior is determined entirely by **connection style** and **node type**.
* Producers decide loop timing based on whether downstream chains contain blocking or non‑blocking paths.
* Storage systems (queues / databases) are natural async boundaries.

---

If you need, a follow‑up diagram, sequence flow, or engine‑execution pseudocode can be added.
