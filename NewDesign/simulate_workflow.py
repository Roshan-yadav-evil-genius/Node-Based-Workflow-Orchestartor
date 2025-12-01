import asyncio
import json
import os
import sys

sys.path.append(os.getcwd())

from WorkflowOrchestrator import WorkflowOrchestrator

async def main():
    try:
        # Load workflow.json
        with open("workflow.json", "r") as f:
            workflow_data = json.load(f)
            
        orchestrator = WorkflowOrchestrator()
        
        # Load and initialize workflow
        orchestrator.load_workflow(workflow_data)
        
        # Run Production Mode
        # Note: In a real scenario, this runs indefinitely. 
        # For simulation, we'll let it run for a few seconds then stop.
        
        print("\n[Simulation] Starting Workflow Simulation...")
        simulation_task = asyncio.create_task(orchestrator.run_production())
        
        await asyncio.sleep(10) # Run for 10 seconds
        
        print("\n[Simulation] Stopping Simulation...")
        # Stop all loops
        for manager in orchestrator.loop_managers:
            manager.stop()
            
        await simulation_task
        print("[Simulation] Simulation Completed.")
        
    except Exception as e:
        print(f"[Simulation] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
