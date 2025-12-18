from ..System.QueueReader import QueueReader

class QueryDb(QueueReader):
    @classmethod
    def identifier(cls) -> str:
        return "query-db"
