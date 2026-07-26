from textwrap import dedent
from typing import List

from markdown_it import MarkdownIt
from markdown_it.token import Token

from models.Document import Document, Metadata, Content
from api.document_router import s3_service
from services.processor.DocumentProcessor import DocumentProcessor

open_token_to_content_type = {
    'heading_open':'heading',
    'paragraph_open':'paragraph',
    'bullet_list_open':'list',
    'ordered_list_open':'list',
    'list_item_open':'list',
}

open_close_mapping = {
    'heading_open':'heading_close',
    'paragraph_open':'paragraph_close',
    'bullet_list_open':'bullet_list_close',
    'ordered_list_open':'ordered_list_close',
    'list_item_open': 'list_item_close',
}

class MarkdownDocumentProcessor(DocumentProcessor):
    def process(self, key: str) -> Document:
        file_bytes = self._read(key)
        file_metadata = self._extract_metadata(key)
        text = self._decode(file_bytes)



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
        md = MarkdownIt()
        tokens = md.parse(text)
        order = 1
        contents: List[Content] = []
        current_block = ""
        content_text = ""
        for token in tokens:
            # if coding block then set the content
            # if opening then start the block
            # if inline then set the text
            # if closing then append to the contents and then reset the block and text
            if token.type == "fence":
                content = Content(
                    type="code",
                    text=token.content,
                    order=order
                )
                order += 1
                contents.append(content)
                continue
            if token.type in open_token_to_content_type:
                current_block = token.type
                content_text = ""
                continue
            if token.type == "inline":
                # TODO: Handle multiple inline children (bold, italic, links, etc.)
                content_text = token.children[0].content
                continue
            if current_block in open_close_mapping and token.type == open_close_mapping[current_block]:
                content = Content(
                    type=open_token_to_content_type[current_block],
                    text=content_text,
                    order=order
                )
                order += 1
                contents.append(content)
                current_block = ""
                content_text = ""

        return contents


# - One
#     - Two
#
def dummy_markdown():
    print("testing markdown-it-py")
    sample_markdown = dedent("""
    # Hello

    This is a paragraph.
    
    ```python
    print("Hi")
    ```
    """)

    print("testing completed")

if __name__ == "__main__":
    dummy_markdown()