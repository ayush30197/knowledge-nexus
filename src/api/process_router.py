from fastapi import APIRouter, HTTPException
from fastapi.params import Query

from models.Document import Document
from registry.DocumentProcessorRegistry import DocumentProcessorRegistry

registry = DocumentProcessorRegistry()
router = APIRouter(
    prefix="/process",
    tags=["Process"],
)


@router.post("/")
async def process_document(
        key: str = Query(..., description="Key for the MinIO object")
) -> Document:
    try:
        processor_class = registry.resolve_processor(key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    processor = processor_class()
    return processor.process(key)
