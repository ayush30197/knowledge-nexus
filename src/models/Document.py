from typing import List, Optional

from pydantic import BaseModel


class Metadata(BaseModel):
    name: str
    content_type: str
    size: int
    author: Optional[str] = None


class Content(BaseModel):
    type: str
    text: str
    order: int


class Document(BaseModel):
    id: str
    contents: List[Content]
    metadata: Metadata
