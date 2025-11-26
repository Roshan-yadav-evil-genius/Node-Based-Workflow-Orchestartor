from abc import abstractmethod
from .BaseNodeProperty import BaseNodeProperty
from .BaseNodeMethod import BaseNodeMethod

class Node(BaseNodeProperty,BaseNodeMethod):

    @abstractmethod
    async def main(self):
        pass