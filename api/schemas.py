from pydantic import BaseModel, EmailStr
import uuid
from typing import List

# --- API Key Schemas ---
class ApiKey(BaseModel):
    key: str
    class Config:
        from_attributes = True

# --- User Schemas ---
class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    api_keys: List[ApiKey] = []
    class Config:
        from_attributes = True

# --- Auth Schemas ---
class AuthInitiateRequest(BaseModel):
    email: EmailStr

class AuthVerifyRequest(BaseModel):
    email: EmailStr
    code: str

# This response is used when login/registration is successful
class AuthSuccessResponse(BaseModel):
    email: EmailStr
    api_key: str
    is_new_user: bool


# --- Mgret API Schemas ---
class IndexRequest(BaseModel):
    project_name: str
    file_path: str
    file_content: str

class IndexFileRequest(BaseModel):
    """For uploading binary files (images, documents)"""
    project_name: str
    file_path: str
    # file_bytes will be sent as multipart/form-data

class SearchRequest(BaseModel):
    query: str
    project_name: str = None
    top_k: int = 5