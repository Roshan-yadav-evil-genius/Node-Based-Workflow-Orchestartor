"""
Example script to run the workflow in Development Mode.

Development Mode allows you to execute nodes one at a time,
useful for testing and debugging individual nodes.
"""

import asyncio
import json
import redis.asyncio as redis
from orchestrator import Orchestrator
from domain import NodeData


async def main():
    """Main execution function."""
    # Initialize Redis client
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=False
    )
    
    try:
        await redis_client.ping()
        print("✓ Connected to Redis")
    except Exception as e:
        print(f"⚠ Warning: Could not connect to Redis: {e}")
        print("⚠ Cache operations may fail, but node execution will still work")
    
    # Create orchestrator in Development Mode
    orchestrator = Orchestrator(mode="development", redis_client=redis_client)
    
    # Load workflow from JSON file
    print("\n📋 Loading workflow from workflow.json...")
    with open('workflow.json', 'r') as f:
        workflow_data = json.load(f)
    
    await orchestrator.load_workflow(workflow_data)
    print("✓ Workflow loaded successfully")
    
    # Clear any existing cache
    await orchestrator.clear_cache()
    print("✓ Cache cleared")
    
    # Example: Execute nodes in sequence
    print("\n🔧 Executing workflow nodes step by step...\n")
    
    try:
        # Step 1: Execute producer node
        print("1️⃣ Executing: playwright-freelance-job-monitor-producer")
        result1 = await orchestrator.execute_node("playwright-freelance-job-monitor-producer")
        print(f"   ✓ Job ID: {result1.get('job_id')}")
        print(f"   ✓ Job Title: {result1.get('job_title')}")
        print(f"   ✓ Is Python Job: {result1.get('is_python_job')}\n")
        
        # Step 2: Execute conditional node
        print("2️⃣ Executing: if-python-job")
        result2 = await orchestrator.execute_node("if-python-job")
        condition_result = result2.metadata.get('condition_label', 'Unknown')
        print(f"   ✓ Condition Result: {condition_result}\n")
        
        if condition_result == "Yes":
            # Step 3: Store node
            print("3️⃣ Executing: store-node")
            result3 = await orchestrator.execute_node("store-node")
            print(f"   ✓ Data stored\n")
            
            # Step 4: Store reader
            print("4️⃣ Executing: store-reader")
            result4 = await orchestrator.execute_node("store-reader")
            print(f"   ✓ Data read from store\n")
            
            # Step 5: AI/ML Scoring
            print("5️⃣ Executing: ai-ml-scoring")
            result5 = await orchestrator.execute_node("ai-ml-scoring")
            score = result5.get('score', 0.0)
            print(f"   ✓ Score: {score:.2f}\n")
            
            # Step 6: Score threshold check
            print("6️⃣ Executing: if-score-threshold")
            result6 = await orchestrator.execute_node("if-score-threshold")
            score_condition = result6.metadata.get('condition_label', 'Unknown')
            print(f"   ✓ Score Condition: {score_condition}\n")
            
            if score_condition == "Yes":
                # High score path
                print("7️⃣ Executing: queue-node (high score path)")
                await orchestrator.execute_node("queue-node")
                print("   ✓ Data queued\n")
                
                print("8️⃣ Executing: queue-reader")
                await orchestrator.execute_node("queue-reader")
                print("   ✓ Data read from queue\n")
                
                print("9️⃣ Executing: llm-proposal-preparer")
                result9 = await orchestrator.execute_node("llm-proposal-preparer")
                proposal = result9.get('proposal_text', '')[:100] + "..."
                print(f"   ✓ Proposal generated: {proposal}\n")
                
                print("🔟 Executing: playwright-freelance-bidder")
                result10 = await orchestrator.execute_node("playwright-freelance-bidder")
                print(f"   ✓ Bid submitted: {result10.get('bid_id')}\n")
            else:
                # Low score path
                print("7️⃣ Executing: db-node (low score path)")
                await orchestrator.execute_node("db-node")
                print("   ✓ Data written to DB\n")
                
                print("8️⃣ Executing: query-db")
                await orchestrator.execute_node("query-db")
                print("   ✓ DB queried\n")
                
                print("9️⃣ Executing: telegram-sender")
                result9 = await orchestrator.execute_node("telegram-sender")
                print(f"   ✓ Telegram message sent: {result9.get('telegram_message_id')}\n")
                
                print("🔟 Executing: db-status-updater")
                result10 = await orchestrator.execute_node("db-status-updater")
                print(f"   ✓ Status updated: {result10.get('job_status')}\n")
        else:
            print("   ⏭ Skipping (not a Python job)\n")
        
        print("✅ Workflow execution complete!")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
    
    # Shutdown
    await orchestrator.shutdown()
    await redis_client.aclose()
    print("\n✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
