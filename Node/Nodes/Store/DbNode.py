from ..System.QueueNode import QueueNode

class DbNode(QueueNode):
    @classmethod
    def identifier(cls) -> str:
        return "db-node"
