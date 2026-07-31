import uuid
from dataclasses import dataclass
from textwrap import dedent
from typing import List

from markdown_it import MarkdownIt
from markdown_it.token import Token

from models.Document import Document, Metadata, Content
from api.document_router import s3_service
from services.processor.DocumentProcessor import DocumentProcessor

OPEN_TOKEN_TO_CONTENT_TYPE = {
    'heading_open':'heading',
    'paragraph_open':'paragraph',
    'bullet_list_open':'list',
    'ordered_list_open':'list',
    'list_item_open':'list',
}

OPEN_CLOSE_MAPPING = {
    'heading_open':'heading_close',
    'paragraph_open':'paragraph_close',
    'bullet_list_open':'bullet_list_close',
    'ordered_list_open':'ordered_list_close',
    'list_item_open': 'list_item_close',
}

class MarkdownDocumentProcessor(DocumentProcessor):
    def __init__(self):
        self.md = MarkdownIt()

    @dataclass
    class MarkdownParserState:
        order: int
        contents: List[Content]
        block_stack: List[str]
        content_text: str
        current_list_item: str
        list_items: List[str]

    def process(self, key: str) -> Document:
        file_bytes = self._read(key)
        file_metadata = self._extract_metadata(key)
        text = self._decode(file_bytes)
        content_blocks = self._build_content(text)

        return Document(
            id=uuid.uuid4().hex,
            contents=content_blocks,
            metadata=file_metadata,
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

    def _build_content(self, text: str) -> List[Content]:
        """
        Build Contents Block of CDM
        """

        # use the Markdown library to parse the Markdown file text
        tokens = self.md.parse(text)

        state = self.MarkdownParserState(
            order=1,
            contents=[],
            block_stack=[],
            content_text="",
            current_list_item="",
            list_items=[]
        )

        for token in tokens:
            if token.type == "fence":
                self._handle_fence(token, state)
            elif token.type in OPEN_TOKEN_TO_CONTENT_TYPE:
                self._handle_open(token, state)
            elif token.type == "inline":
                self._handle_inline(token, state)
            elif token.type.endswith("_close"):
                self._handle_close(token, state)
        return state.contents

    @staticmethod
    def _handle_open(token: Token, state: MarkdownParserState):
        state.block_stack.append(token.type)
        if token.type == "list_item_open":
            state.current_list_item = ""
        elif token.type in (
                "heading_open",
                "paragraph_open",
            ):
            state.content_text = ""
        elif token.type in ("bullet_list_open", "ordered_list_open"):
            state.list_items.clear()

    def _handle_inline(self, token: Token, state: MarkdownParserState):
            if self._inside_list(state):
                state.current_list_item = token.children[0].content
                return
            text = ""
            for child in token.children:
                if child.content:
                    text += child.content
            state.content_text = text

    def _handle_close(self, token: Token, state: MarkdownParserState):
        if (
                state.block_stack
                and
                token.type == OPEN_CLOSE_MAPPING[state.block_stack[-1]]
        ):
            if token.type == "list_item_close":
                state.list_items.append(state.current_list_item)
                state.block_stack.pop()
                return
            elif  token.type == "paragraph_close" and self._inside_list(state):
                state.block_stack.pop()
                return
            elif token.type in (
                "bullet_list_close",
                "ordered_list_close",
            ):
                self._emit_content(OPEN_TOKEN_TO_CONTENT_TYPE[state.block_stack[-1]], "\n".join(state.list_items), state)
            else:
                self._emit_content(OPEN_TOKEN_TO_CONTENT_TYPE[state.block_stack[-1]], state.content_text, state)
            state.block_stack.pop()

    def _handle_fence(self, token: Token, state: MarkdownParserState):
        self._emit_content("code", token.content, state)

    @staticmethod
    def _emit_content(content_type: str,  text: str, state: MarkdownParserState):
        content = Content(
            type=content_type,
            text=text,
            order=state.order
        )
        state.order += 1
        state.contents.append(content)

    @staticmethod
    def _inside_list(state: MarkdownParserState):
        return (
                "bullet_list_open" in state.block_stack
                or
                "ordered_list_open" in state.block_stack
        )

def dummy_markdown():
    print("testing markdown-it-py")
    sample_markdown = dedent("""
    # Hello

    ```python
    print("Hi")
    ```
    """)
    md = MarkdownIt()
    tokens = md.parse(sample_markdown)
    order = 1
    contents: List[Content] = []
    block_stack = []
    content_text = ""
    list_items = []
    current_list_item = ""
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
        if token.type in OPEN_TOKEN_TO_CONTENT_TYPE:
            block_stack.append(token.type)
            content_text = ""
            if token.type == "list_item_open":
                current_list_item = ""
            continue
        if token.type == "inline":
            if (
                    "bullet_list_open" in block_stack
                    or
                    "ordered_list_open" in block_stack
            ):
                current_list_item = token.children[0].content
                continue
            # TODO: Handle multiple inline children (bold, italic, links, etc.)
            content_text = token.children[0].content
            continue
        if block_stack and block_stack[-1] in OPEN_CLOSE_MAPPING and token.type == OPEN_CLOSE_MAPPING[block_stack[-1]]:
            if token.type == "list_item_close":
                list_items.append(current_list_item)
                block_stack.pop()
                continue
            elif  token.type == "paragraph_close" and ("bullet_list_open" in block_stack or "ordered_list_open" in block_stack):
                block_stack.pop()
                continue
            elif token.type in (
                        "bullet_list_close",
                        "ordered_list_close",
                ):
                content = Content(
                    type=OPEN_TOKEN_TO_CONTENT_TYPE[block_stack[-1]],
                    text="\n".join(list_items),
                    order=order
                )
                list_items = []
            else:
                content = Content(
                    type=OPEN_TOKEN_TO_CONTENT_TYPE[block_stack[-1]],
                    text=content_text,
                    order=order
                )
            order += 1
            contents.append(content)
            block_stack.pop()
            content_text = ""

    print("testing completed")

if __name__ == "__main__":
    dummy_markdown()