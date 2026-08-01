from services.processor.DocumentProcessor import DocumentProcessor
from services.processor.MarkdownDocumentProcessor import MarkdownDocumentProcessor
from services.processor.TxtDocumentProcessor import TxtDocumentProcessor


class DocumentProcessorRegistry:
    DOCUMENT_PROCESSOR_REGISTRY = {
        ".txt": TxtDocumentProcessor,
        ".md": MarkdownDocumentProcessor
    }

    def resolve_processor(self, key: str) -> type[DocumentProcessor]:
        extension = self._extract_extension(key)
        if extension in self.DOCUMENT_PROCESSOR_REGISTRY:
            return self.DOCUMENT_PROCESSOR_REGISTRY[extension]
        raise ValueError(
            f"{extension} not supported. "
            f"Supported extensions: {', '.join(self.DOCUMENT_PROCESSOR_REGISTRY.keys())}"
        )

    @staticmethod
    def _extract_extension(key: str) -> str:
        if "." not in key:
            raise ValueError("invalid key")
        return "." + key.split(".")[-1]
