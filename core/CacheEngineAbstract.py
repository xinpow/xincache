from abc import ABC, abstractmethod

class CacheEngineAbstract(ABC):
    @abstractmethod
    def set(self, key: str, value: any):
        pass

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

    @abstractmethod
    def clear(self, key: str):
        pass