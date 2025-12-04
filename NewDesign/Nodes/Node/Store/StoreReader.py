from ..System.QueueReader import QueueReader

class StoreReader(QueueReader):
    @classmethod
    def identifier(cls) -> str:
        return "store-reader"
