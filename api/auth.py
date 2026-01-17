from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..db import models
from ..db.database import SessionLocal, engine
from . import schemas
from ..auth import security

from .dependencies import get_db

router = APIRouter()

# Dependency to get DB session is now imported

@router.post("/initiate", status_code=status.HTTP_200_OK)
def initiate_auth(request: schemas.AuthInitiateRequest, db: Session = Depends(get_db)):
    """
    Initiates login/registration. Generates a code and saves it to the user record.
    """
    # For now, per user request, we don't need a real code.
    # In a real scenario, we would do this:
    # verification_code = security.generate_verification_code()
    # expires_at = datetime.utcnow() + timedelta(minutes=10)
    #
    # user = db.query(models.User).filter(models.User.email == request.email).first()
    # if not user:
    #     user = models.User(email=request.email)
    #     db.add(user)
    #
    # user.verification_code = verification_code
    # user.verification_code_expires_at = expires_at
    # db.commit()
    #
    # # In a real scenario, you would email the code here.
    # # For testing, we can return it.
    # return {"message": "Verification code sent.", "test_code": verification_code}

    # Simplified flow as requested: "on peut mettre n'importe quel code"
    return {"message": "Please proceed to verify with any code."}


@router.post("/verify", response_model=schemas.AuthSuccessResponse)
def verify_auth(request: schemas.AuthVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies the code and returns the user's API key.
    Creates the user if they don't exist.
    """
    # Simplified flow: since any code is valid, we just find or create the user.
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    is_new = False
    if not user:
        is_new = True
        user = models.User(email=request.email)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Check if user has an API key, if not, create one
    if not user.api_keys:
        api_key_str = security.generate_api_key()
        new_api_key = models.ApiKey(key=api_key_str, user_id=user.id)
        db.add(new_api_key)
        db.commit()
        db.refresh(new_api_key)
        api_key_to_return = api_key_str
    else:
        api_key_to_return = user.api_keys[0].key

    return schemas.AuthSuccessResponse(
        email=user.email,
        api_key=api_key_to_return,
        is_new_user=is_new
    )
