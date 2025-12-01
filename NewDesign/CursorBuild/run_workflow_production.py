"""
Example script to run the workflow in Production Mode.

Production Mode runs the workflow continuously in loops.
Each producer node starts its own loop that runs indefinitely.
"""

import asyncio
import json
import redis.asyncio as redis
from orchestrator import Orchestrator


async def main():
    """Main execution function."""
    # Initialize Redis client
    # Make sure Redis is running on localhost:6379
    # For testing without Redis, you can use a mock, but the dummy nodes
    # should work fine even if Redis isn't fully functional for queues
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=False  # We handle encoding ourselves
    )
    
    try:
        # Test Redis connection
        await redis_client.ping()
        print("✓ Connected to Redis")
    except Exception as e:
        print(f"⚠ Warning: Could not connect to Redis: {e}")
        print("⚠ The workflow will still run, but queue operations may fail")
        print("⚠ For full functionality, start Redis: redis-server")
    
    # Create orchestrator in Production Mode
    orchestrator = Orchestrator(mode="production", redis_client=redis_client)
    
    # Load workflow from JSON file
    print("\n📋 Loading workflow from workflow.json...")
    with open('workflow.json', 'r') as f:
        workflow_data = json.load(f)
    
    await orchestrator.load_workflow(workflow_data)
    print("✓ Workflow loaded successfully")
    
    # Get producer nodes
    workflow_graph = orchestrator.get_workflow_graph()
    producer_nodes = workflow_graph.get_producer_nodes()
    
    print(f"\n🚀 Starting {len(producer_nodes)} loop(s)...")
    print(f"   Producer nodes: {producer_nodes}")
    
    # Start all loops
    await orchestrator.start_all_loops()
    
    print("\n✅ All loops started! Workflow is running...")
    print("   Press Ctrl+C to stop\n")
    
    # Keep running until interrupted
    try:
        # Run for a specified duration (e.g., 60 seconds) or until interrupted
        await asyncio.sleep(60)  # Run for 60 seconds
        print("\n⏱ Time limit reached, stopping loops...")
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping loops...")
    
    # Stop all loops
    await orchestrator.stop_all_loops()
    print("✓ All loops stopped")
    
    # Shutdown orchestrator
    await orchestrator.shutdown()
    
    # Close Redis connection
    await redis_client.aclose()
    print("✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
