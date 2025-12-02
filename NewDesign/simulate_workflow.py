import asyncio
import json
import os
import sys

sys.path.append(os.getcwd())

import structlog
from logging_config import setup_logging
from WorkflowOrchestrator import WorkflowOrchestrator

logger = structlog.get_logger(__name__)

async def main():
    # Setup logging first
    setup_logging()
    
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
        
        logger.info("[Simulation] Starting Workflow Simulation...")
        simulation_task = asyncio.create_task(orchestrator.run_production())
        
        await asyncio.sleep(10) # Run for 10 seconds
        
        logger.info("[Simulation] Stopping Simulation...")
        # Stop all loops
        for manager in orchestrator.loop_managers:
            manager.stop()
            
        await simulation_task
        logger.info("[Simulation] Simulation Completed.")
        
    except Exception as e:
        logger.exception("[Simulation] Error", error=str(e))

if __name__ == "__main__":
    asyncio.run(main())
