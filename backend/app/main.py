
from fastapi import FastAPI

# Create the main FastAPI application
app = FastAPI(
    title="CICADA Smart Observability Platform",
    description="Secure AIOps observability backend",
    version="0.1.0"
)


# Root endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to CICADA Smart Observability Platform",
        "status": "running"
    }


# Health-check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CICADA Backend"
    }
