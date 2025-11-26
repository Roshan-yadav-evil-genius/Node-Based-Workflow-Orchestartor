from abc import ABC, abstractmethod


class BaseNodeMethod(ABC):

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def loop(self):
        pass