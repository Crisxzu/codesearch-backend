from ..db.database import SessionLocal

def get_db():
    """
    FastAPI dependency to provide a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
