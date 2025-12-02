from typing import Any, Dict
from pydantic import BaseModel, Field
from typing import Optional

class NodeConfig(BaseModel):
    """
    Static initialization/config settings for a node.
    """
    node_id: str = Field(..., description="Unique identifier for the node")
    node_name: str = Field(..., description="Human-readable name for the node")
    form_data: Optional[Dict[str, Any]] = Field(default=None, description="Form data for the node")
