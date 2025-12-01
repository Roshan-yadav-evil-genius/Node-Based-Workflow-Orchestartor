"""
Observability module for logging, metrics, and health monitoring.

This module provides structured logging, metrics collection, and health
monitoring capabilities following the Single Responsibility Principle.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from domain import NodeData


class Logger:
    """
    Structured logger for workflow orchestrator.
    
    Provides structured logging for node execution, errors, and loop lifecycle
    events with consistent formatting.
    """
    
    def __init__(self, name: str = "workflow_orchestrator", level: int = logging.INFO):
        """
        Initialize Logger.
        
        Args:
            name: Logger name
            level: Logging level
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        
        # Add console handler if not already present
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def log_node_execution_start(self, node_id: str, execution_pool: str) -> None:
        """Log node execution start."""
        self._logger.info(
            f"Node execution started: node_id={node_id}, pool={execution_pool}"
        )
    
    def log_node_execution_complete(
        self,
        node_id: str,
        execution_time: float,
        success: bool = True
    ) -> None:
        """Log node execution completion."""
        status = "success" if success else "failure"
        self._logger.info(
            f"Node execution completed: node_id={node_id}, "
            f"execution_time={execution_time:.3f}s, status={status}"
        )
    
    def log_node_error(self, node_id: str, error: Exception) -> None:
        """Log node execution error."""
        self._logger.error(
            f"Node execution error: node_id={node_id}, "
            f"error_type={type(error).__name__}, error_message={str(error)}",
            exc_info=True
        )
    
    def log_loop_start(self, producer_id: str, execution_pool: str) -> None:
        """Log loop start."""
        self._logger.info(
            f"Loop started: producer_id={producer_id}, pool={execution_pool}"
        )
    
    def log_loop_stop(self, producer_id: str) -> None:
        """Log loop stop."""
        self._logger.info(f"Loop stopped: producer_id={producer_id}")
    
    def log_iteration_start(self, producer_id: str, iteration: int) -> None:
        """Log loop iteration start."""
        self._logger.debug(
            f"Iteration started: producer_id={producer_id}, iteration={iteration}"
        )
    
    def log_iteration_complete(self, producer_id: str, iteration: int) -> None:
        """Log loop iteration completion."""
        self._logger.debug(
            f"Iteration completed: producer_id={producer_id}, iteration={iteration}"
        )
    
    def log_dlq_send(self, node_id: str) -> None:
        """Log DLQ send event."""
        self._logger.warning(f"Failed execution sent to DLQ: node_id={node_id}")
    
    def log_workflow_loaded(self, node_count: int, edge_count: int) -> None:
        """Log workflow loading."""
        self._logger.info(
            f"Workflow loaded: nodes={node_count}, edges={edge_count}"
        )


class MetricsCollector:
    """
    Collects metrics for workflow execution.
    
    Tracks execution times, queue lengths, error rates, and other
    performance metrics for observability.
    """
    
    def __init__(self):
        """Initialize MetricsCollector."""
        self._node_execution_times: Dict[str, List[float]] = defaultdict(list)
        self._node_execution_counts: Dict[str, int] = defaultdict(int)
        self._node_error_counts: Dict[str, int] = defaultdict(int)
        self._loop_iteration_counts: Dict[str, int] = defaultdict(int)
        self._queue_lengths: Dict[str, List[int]] = defaultdict(list)
        self._start_times: Dict[str, float] = {}
    
    def record_node_execution_start(self, node_id: str) -> None:
        """Record start of node execution."""
        self._start_times[node_id] = time.time()
    
    def record_node_execution_complete(self, node_id: str, success: bool = True) -> None:
        """Record completion of node execution."""
        if node_id not in self._start_times:
            return
        
        execution_time = time.time() - self._start_times[node_id]
        del self._start_times[node_id]
        
        self._node_execution_times[node_id].append(execution_time)
        self._node_execution_counts[node_id] += 1
        
        if not success:
            self._node_error_counts[node_id] += 1
    
    def record_loop_iteration(self, producer_id: str) -> None:
        """Record a loop iteration."""
        self._loop_iteration_counts[producer_id] += 1
    
    def record_queue_length(self, queue_name: str, length: int) -> None:
        """Record queue length."""
        self._queue_lengths[queue_name].append(length)
    
    def get_node_metrics(self, node_id: str) -> Dict:
        """
        Get metrics for a specific node.
        
        Returns:
            Dict with execution_count, error_count, avg_execution_time, etc.
        """
        execution_times = self._node_execution_times.get(node_id, [])
        execution_count = self._node_execution_counts.get(node_id, 0)
        error_count = self._node_error_counts.get(node_id, 0)
        
        avg_time = (
            sum(execution_times) / len(execution_times)
            if execution_times else 0.0
        )
        min_time = min(execution_times) if execution_times else 0.0
        max_time = max(execution_times) if execution_times else 0.0
        
        return {
            "node_id": node_id,
            "execution_count": execution_count,
            "error_count": error_count,
            "success_rate": (
                (execution_count - error_count) / execution_count
                if execution_count > 0 else 1.0
            ),
            "avg_execution_time": avg_time,
            "min_execution_time": min_time,
            "max_execution_time": max_time,
            "total_executions": len(execution_times),
        }
    
    def get_loop_metrics(self, producer_id: str) -> Dict:
        """
        Get metrics for a specific loop.
        
        Returns:
            Dict with iteration_count, etc.
        """
        return {
            "producer_id": producer_id,
            "iteration_count": self._loop_iteration_counts.get(producer_id, 0),
        }
    
    def get_queue_metrics(self, queue_name: str) -> Dict:
        """
        Get metrics for a specific queue.
        
        Returns:
            Dict with current_length, avg_length, etc.
        """
        lengths = self._queue_lengths.get(queue_name, [])
        current_length = lengths[-1] if lengths else 0
        avg_length = sum(lengths) / len(lengths) if lengths else 0.0
        
        return {
            "queue_name": queue_name,
            "current_length": current_length,
            "avg_length": avg_length,
            "max_length": max(lengths) if lengths else 0,
            "min_length": min(lengths) if lengths else 0,
        }
    
    def get_all_metrics(self) -> Dict:
        """Get all collected metrics."""
        return {
            "nodes": {
                node_id: self.get_node_metrics(node_id)
                for node_id in self._node_execution_counts.keys()
            },
            "loops": {
                producer_id: self.get_loop_metrics(producer_id)
                for producer_id in self._loop_iteration_counts.keys()
            },
            "queues": {
                queue_name: self.get_queue_metrics(queue_name)
                for queue_name in self._queue_lengths.keys()
            },
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._node_execution_times.clear()
        self._node_execution_counts.clear()
        self._node_error_counts.clear()
        self._loop_iteration_counts.clear()
        self._queue_lengths.clear()
        self._start_times.clear()


class HealthMonitor:
    """
    Monitors system health and connectivity.
    
    Provides health checks for Redis connectivity, loop status, and
    overall system health.
    """
    
    def __init__(self, redis_client, orchestrator=None):
        """
        Initialize HealthMonitor.
        
        Args:
            redis_client: Redis client for connectivity checks
            orchestrator: Optional Orchestrator instance for status checks
        """
        self._redis = redis_client
        self._orchestrator = orchestrator
    
    async def check_redis_health(self) -> Dict:
        """
        Check Redis connectivity and health.
        
        Returns:
            Dict with status, latency, etc.
        """
        start_time = time.time()
        try:
            await self._redis.ping()
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "connected": True,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False,
            }
    
    async def check_loop_health(self) -> Dict:
        """
        Check health of running loops.
        
        Returns:
            Dict with loop status information
        """
        if self._orchestrator is None:
            return {
                "status": "unknown",
                "error": "Orchestrator not available",
            }
        
        if self._orchestrator.mode != "production":
            return {
                "status": "n/a",
                "mode": self._orchestrator.mode,
            }
        
        running_loops = self._orchestrator.get_running_loops()
        
        return {
            "status": "healthy" if running_loops else "no_loops",
            "running_loops": len(running_loops),
            "loop_ids": running_loops,
        }
    
    async def get_health_status(self) -> Dict:
        """
        Get overall system health status.
        
        Returns:
            Dict with comprehensive health information
        """
        redis_health = await self.check_redis_health()
        loop_health = await self.check_loop_health()
        
        overall_status = "healthy"
        if not redis_health.get("connected"):
            overall_status = "unhealthy"
        elif loop_health.get("status") == "unknown":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "redis": redis_health,
            "loops": loop_health,
        }
