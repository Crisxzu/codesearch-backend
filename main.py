from fastapi import FastAPI
from .api import auth, mgrep

app = FastAPI(title="CodeSearch API")

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(mgrep.router, prefix="/api", tags=["mgrep"])

@app.get("/")
def read_root():
    return {"message": "Welcome to mgrep API"}
