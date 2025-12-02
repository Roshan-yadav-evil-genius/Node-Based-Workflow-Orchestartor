from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class NodeData(BaseModel):
    """
    Runtime payload for the iteration.
    """
    id: str = Field(..., description="Unique identifier for this unit of work")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Main data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")
