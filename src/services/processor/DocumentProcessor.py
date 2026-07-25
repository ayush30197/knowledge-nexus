from abc import ABC, abstractmethod

from models.Document import Document


class DocumentProcessor(ABC):

    @abstractmethod
    def process(self, key: str) -> Document:
        pass