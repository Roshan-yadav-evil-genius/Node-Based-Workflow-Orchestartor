from datetime import datetime
from typing import Any, Dict
from ...Core.Node.Core import ProducerNode, NodeOutput, PoolType
import asyncio
import structlog
import uuid
import random
import json
from pathlib import Path
import aiofiles

logger = structlog.get_logger(__name__)

class PlaywrightFreelanceJobMonitorProducer(ProducerNode):
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

    async def execute(self, node_data: NodeOutput) -> NodeOutput:
        await asyncio.sleep(2) # Simulate delay
        job_data = {"project_details": self.get_job_data()}

        return NodeOutput(
            id=self.node_config.id,
            data=job_data,
            metadata={"sourceNodeID": self.node_config.id,"sourceNodeName": self.node_config.type}
        )
    
    def get_job_data(self) -> Dict[str, Any]:
        return random.choice(self._job_lines)
