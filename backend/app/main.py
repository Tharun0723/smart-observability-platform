from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.db.database import Base, engine
from app import models as _models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="NEXORA Smart Observability Platform",
    description="Secure AIOps observability backend",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "message": "Welcome to NEXORA Smart Observability Platform",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NEXORA Backend",
    }


app.include_router(api_router, prefix="/api/v1")