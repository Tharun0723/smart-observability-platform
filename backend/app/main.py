from fastapi import FastAPI

from app.api.v1.router import api_router


app = FastAPI(
    title="CICADA Smart Observability Platform",
    description="Secure AIOps observability backend",
    version="0.1.0"
)


# Existing root endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to CICADA Smart Observability Platform",
        "status": "running"
    }


# Existing health-check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CICADA Backend"
    }


# Version 1 API routes
app.include_router(api_router, prefix="/api/v1")