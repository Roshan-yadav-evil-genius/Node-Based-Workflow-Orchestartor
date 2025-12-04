from datetime import datetime
from typing import Any, Dict
from ...Core import ProducerNode, NodeOutput, PoolType
import asyncio
import structlog
import uuid
import random

logger = structlog.get_logger(__name__)

class PlaywrightFreelanceJobMonitorProducer(ProducerNode):
    @classmethod
    def identifier(cls) -> str:
        return "playwright-freelance-job-monitor-producer"

    @property
    def execution_pool(self) -> PoolType:
        return PoolType.ASYNC

    async def execute(self, node_data: NodeOutput) -> NodeOutput:

        await asyncio.sleep(2) # Simulate delay
        job_data = self.get_job_data()

        return NodeOutput(
            id=self.config.id,
            data=job_data,
            metadata={"sourceNodeID": self.config.id,"sourceNodeName": self.config.type}
        )
    
    def get_job_data(self) -> Dict[str, Any]:
        job_title = random.choice(["Python Developer", "React Developer", "Data Scientist", "Java Engineer", "Python Fullstack Developer", "React Fullstack Developer", "Data Science Fullstack Developer", "Java Fullstack Developer"])
        job_descript = random.choice(["We are looking for a Python Developer with 3 years of experience in Django and Flask.", "We are looking for a React Developer with 2 years of experience in React and React Native.", "We are looking for a Data Scientist with 5 years of experience in data analysis and machine learning.", "We are looking for a Java Engineer with 4 years of experience in Spring Boot and Hibernate."])
        job_budget = random.randint(100, 1000)
        job_posting_date = datetime.now().strftime("%Y-%m-%d")
        job_location = random.choice(["Remote", "On-site", "Hybrid"])

        job_data = {
            "job_id": str(uuid.uuid4()),
            "job_title": job_title,
            "description": job_descript,
            "budget": job_budget,
            "posting_date": job_posting_date,
            "location": job_location
        }
        return job_data
