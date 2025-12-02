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
        chain_ids = [node.config.node_id for node in manager.chain]
        print(f"Loop {i+1}: Producer='{producer_id}', Chain Length={chain_len}")
        
        # Show branches in dictionary format if available
        if producer_id in orchestrator.loop_branches and orchestrator.loop_branches[producer_id]:
            branch_info = orchestrator.loop_branches[producer_id]
            # Format as dictionary with proper labels (Yes/No)
            formatted_branches = {}
            for label, nodes in branch_info.items():
                # Properly format Yes/No labels
                if label and label.lower() == 'yes':
                    display_label = 'Yes'
                elif label and label.lower() == 'no':
                    display_label = 'No'
                else:
                    display_label = label.capitalize() if label else 'default'
                formatted_branches[display_label] = nodes
            
            # Find branching node by checking which nodes are in branches but not sequential
            branch_node_ids = set()
            for nodes in branch_info.values():
                branch_node_ids.update(nodes)
            
            # Show sequential nodes before branch, then branches
            sequential_nodes = [nid for nid in chain_ids if nid not in branch_node_ids]
            if sequential_nodes:
                print(f"  Sequential: {sequential_nodes}")
            print(f"  Branches: {formatted_branches}")
        else:
            print(f"  Chain: {chain_ids}")

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
