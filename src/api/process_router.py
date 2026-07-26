from fastapi import APIRouter
from fastapi.params import Query

from models.Document import Document
from services.processor.TxtDocumentProcessor import TxtDocumentProcessor

router = APIRouter(
    prefix="/process",
    tags=["Process"],
)

@router.post("/")
async def process_document(
    key: str = Query(..., description="Key for the MinIO object")
) -> Document:
    svc = TxtDocumentProcessor()
    doc = svc.process(key)

    return doc