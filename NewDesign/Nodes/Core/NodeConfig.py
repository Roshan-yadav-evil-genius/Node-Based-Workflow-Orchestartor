from pydantic import BaseModel, Field

class NodeConfig(BaseModel):
    """
    Static initialization/config settings for a node.
    """
    node_id: str = Field(..., description="Unique identifier for the node")
    node_name: str = Field(..., description="Human-readable name for the node")
