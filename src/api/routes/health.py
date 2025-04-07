from fastapi import APIRouter, status

# Create router
health_router = APIRouter(prefix="/health", tags=["Health"])

@health_router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"} 