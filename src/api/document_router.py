from fastapi import APIRouter, UploadFile, File

from src.services.s3_service import S3Service

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

s3_service = S3Service()

@router.post("/")
async def upload_document(
    file: UploadFile = File(...)
):
    filename = file.filename
    f = f"test/{filename}"
    s3_service.upload_document(
        file=file.file,
        object_name=f,
    )

    return {
        "message": "Upload successful",
        "object_name": filename,
    }