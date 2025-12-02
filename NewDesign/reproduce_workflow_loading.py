import asyncio
import json
import os
import sys

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())

from WorkflowOrchestrator import WorkflowOrchestrator


async def main():
    print("--- Starting Reproduction Script ---")

    # 1. Load workflow.json
    try:
        with open("workflow.json", "r") as f:
            workflow_data = json.load(f)
        print("Loaded workflow.json")
    except FileNotFoundError:
        print("Error: workflow.json not found")
        return

    # 2. Initialize Orchestrator
    orchestrator = WorkflowOrchestrator()

    # 3. Load Workflow
    orchestrator.load_workflow(workflow_data)

    # 4. Verify Loops
    print(f"\nTotal Loops Created: {len(orchestrator.loop_managers)}")

    for i, manager in enumerate(orchestrator.loop_managers):
        producer_id = manager.producer.config.node_id
        chain_len = len(manager.chain)
        print(f"Loop {i+1}: Producer='{producer_id}', Chain Length={chain_len}")
        print(f"  Chain: {[node.config.node_id for node in manager.chain]}")

    # Expected checks
    producers = [m.producer.config.node_id for m in orchestrator.loop_managers]
    expected_producers = ["playwright-freelance-job-monitor-producer", "queue-reader"]

    missing = [p for p in expected_producers if p not in producers]

    if not missing:
        print("\nSUCCESS: All expected loops found.")
    else:
        print(f"\nFAILURE: Missing loops for producers: {missing}")


if __name__ == "__main__":
    asyncio.run(main())
