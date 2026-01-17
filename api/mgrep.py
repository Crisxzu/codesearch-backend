from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File, Form

from ..services.indexing_service import IndexingService
from ..services.search_service import search as search_service
from ..services.es_manager import clean_index as clean_service
from ..api import schemas
from ..auth.api_key import get_current_user
from ..db import models

router = APIRouter()

# Initialize services
indexing_service = IndexingService()

@router.post("/index", status_code=status.HTTP_202_ACCEPTED)
def index_file(
    request: schemas.IndexRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Accepts file content (text/code) and metadata to be indexed.
    For text-based files like Python code.
    """
    try:
        indexing_service.index_file_content(
            user_id=str(current_user.id),
            project_name=request.project_name,
            file_path=request.file_path,
            file_content=request.file_content
        )
        return {"status": "success", "message": f"File '{request.file_path}' is being processed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/file", status_code=status.HTTP_202_ACCEPTED)
async def index_binary_file(
    project_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload and index binary files (images, PDFs, DOCX, etc.)
    Uses multipart/form-data for file upload.
    """
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        # Use the smart indexing method that auto-detects file type
        indexing_service.index_file(
            user_id=str(current_user.id),
            project_name=project_name,
            file_path=file.filename,
            file_bytes=file_bytes
        )
        
        return {
            "status": "success", 
            "message": f"File '{file.filename}' is being processed.",
            "file_size": len(file_bytes),
            "content_type": file.content_type
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
def search_code(
    request: schemas.SearchRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Performs a search query for the authenticated user.
    """
    results = search_service(
        user_id=str(current_user.id),
        project_name=request.project_name,
        query_string=request.query,
        top_k=request.top_k
    )
    if results is None:
        raise HTTPException(status_code=500, detail="Search failed.")
    return results

@router.post("/clean")
def clean_user_index(
    project_name: str = Body(None, embed=True),
    current_user: models.User = Depends(get_current_user)
):
    """
    Cleans all documents for a specific project for the authenticated user.
    """
    if not project_name:
         raise HTTPException(status_code=400, detail="Project name must be provided.")

    result = clean_service(
        user_id=str(current_user.id),
        project_name=project_name
    )
    return result
