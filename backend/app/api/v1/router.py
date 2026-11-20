from fastapi import APIRouter

# Import the three API routers
from app.api.v1.endpoints.collectors import router as collectors_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.metrics import router as metrics_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.aiops import router as aiops_router


# Main API router
api_router = APIRouter()


# Collector authentication
api_router.include_router(
    collectors_router,
    prefix="/collectors",
    tags=["Collectors"],
)


# Administrator and tenant management
api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Administration"],
)


# Telemetry metrics ingestion
api_router.include_router(
    metrics_router,
    prefix="/metrics",
    tags=["Telemetry"],
)

api_router.include_router(
    events_router,
    prefix="/events",
    tags=["Events"],
)
# Internal AIOps integration
api_router.include_router(
    aiops_router,
    prefix="/aiops",
    tags=["AIOps"],
)