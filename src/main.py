from fastapi import FastAPI
import uvicorn

from api import process_router
from src.api.document_router import router as document_router
from src.api.process_router import router as process_router
app = FastAPI()

@app.get("/home")
def home():
    return {"message": "Hello World!"}

app.include_router(document_router)
app.include_router(process_router)

if __name__=='__main__':
    uvicorn.run(
        "main:app",  # Module name : FastAPI app object
        host="127.0.0.1",
        port=8000,
        reload=False  # Auto-reload when code changes
    )