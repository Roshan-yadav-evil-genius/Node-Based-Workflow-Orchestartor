from datetime import datetime
from typing import Any, Dict
from ....Core.Node.Core import ProducerNode, NodeOutput, PoolType
import asyncio
import structlog
import uuid
import random
import json
from pathlib import Path
import aiofiles

logger = structlog.get_logger(__name__)

class JobMonitor(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "playwright-freelance-job-monitor-producer"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def setup(self):
        jobs_file = Path(__file__).parent / "jobs.jl"
        async with aiofiles.open(jobs_file, 'r', encoding='utf-8') as f:
            lines = await f.readlines()
            self._job_lines = [json.loads(line) for line in lines if line.strip()]
        self.execution_count = 0

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        # Check execution limit
        form_data = self.node_config.data.form or {}
        job_limit = int(form_data.get("job_limit", 0))
        
        if job_limit > 0 and self.execution_count >= job_limit:
            from ....Core.Node.Core.Data import ExecutionCompleted
            logger.info("Job execution limit reached", limit=job_limit)
            return ExecutionCompleted(
                data={"message": "Execution limit reached"},
            )

        self.execution_count += 1
        await asyncio.sleep(2) # Simulate delay
        job_data = {"project_details": self.get_job_data()}

        return NodeOutput(
            data=job_data,
        )
    
    def get_job_data(self) -> Dict[str, Any]:
        return random.choice(self._job_lines)
