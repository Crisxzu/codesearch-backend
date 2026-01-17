from fastapi import Security, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..db import models
from ..api.dependencies import get_db

api_key_header = APIKeyHeader(name="X-API-Key")

def get_user_by_api_key(db: Session, api_key: str):
    return db.query(models.User).join(models.ApiKey).filter(models.ApiKey.key == api_key).first()

def get_current_user(api_key: str = Security(api_key_header), db: Session = Depends(get_db)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An API key is required."
        )
    
    user = get_user_by_api_key(db, api_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key."
        )
    return user
