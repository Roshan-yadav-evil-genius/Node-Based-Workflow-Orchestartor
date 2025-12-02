from enum import Enum

class ExecutionPool(Enum):
    ASYNC = "ASYNC"
    THREAD = "THREAD"
    PROCESS = "PROCESS"
