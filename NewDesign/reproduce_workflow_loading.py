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



if __name__ == "__main__":
    asyncio.run(main())
