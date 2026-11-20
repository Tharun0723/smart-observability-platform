from fastapi import APIRouter

from app.api.v1.endpoints.collectors import router as collectors_router


api_router = APIRouter()

api_router.include_router(
    collectors_router,
    prefix="/collectors",
    tags=["Collectors"],
)