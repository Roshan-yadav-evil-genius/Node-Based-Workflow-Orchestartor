from ..System.QueueNode import QueueNode

class StoreNode(QueueNode):
    @classmethod
    def identifier(cls) -> str:
        return "store-node"
