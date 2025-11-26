from .Node.Node import Node
from .PlaceNodeForm import PlaceNodeForm


class PlaceNode(Node):
    """
    Concrete implementation using Django forms with dependencies.
    
    This node creates a form with three fields: country (select), state (select),
    and language (select). The state and language fields depend on the selected
    country and state respectively, and are populated dynamically.
    """
    
    @property
    def identifier(self) -> str:
        return "place"
    
    @property
    def label(self) -> str:
        return "Place"
    
    @property
    def description(self) -> str:
        return "Node for selecting country, state, and language"
    
    @property
    def icon(self) -> str:
        return "place-icon"
    
    @property
    def form(self):
        """Get the associated form for this node."""
        return PlaceNodeForm()

    def setup(self):
        """Setup method called during node initialization."""
        pass

    def loop(self):
        """Loop method called during node execution."""
        pass

    async def main(self):
        """Main method called as the entry point for node execution."""
        pass
