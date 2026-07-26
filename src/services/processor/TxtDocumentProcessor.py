import uuid
from typing import List

from api.document_router import s3_service
from models.Document import Document, Metadata, Content
from services.processor.DocumentProcessor import DocumentProcessor

class TxtDocumentProcessor(DocumentProcessor):

    def process(self, key: str) -> Document:
        """
        Processor used for parsing text documents and converting them to canonical document
        """
        file_bytes = self._read(key)
        metadata = self._extract_metadata(key)
        text = self._decode(file_bytes)
        content_blocks = self._build_content(text)

        return Document(
            id = uuid.uuid4().hex,
            contents=content_blocks,
            metadata=metadata,
        )

    @staticmethod
    def _read(key: str) -> bytes:
        """
        Reads the file from MinIO
        """
        return s3_service.download(key=key)

    @staticmethod
    def _extract_metadata(key: str) -> Metadata:
        """
        Extract the metadata from the file object
        """
        return s3_service.metadata(key=key)

    @staticmethod
    def _decode(file_bytes: bytes) -> str:
        """
        Decode the data from the file
        """
        return file_bytes.decode("utf-8")

    @staticmethod
    def _build_content(text: str) -> List[Content]:
        """
        Build Contents Block of CDM
        """
        content = Content(
            type="text",
            text=text,
            order=1
        )
        return [content]
