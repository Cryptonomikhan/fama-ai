from fastapi import APIRouter

from src.api.routes.modeling import modeling_router
from src.api.routes.health import health_router
from src.api.routes.session import session_router

# Create v1 router
v1_router = APIRouter(prefix="/api/v1")

# Include sub-routers
v1_router.include_router(modeling_router)
v1_router.include_router(health_router)
v1_router.include_router(session_router) 