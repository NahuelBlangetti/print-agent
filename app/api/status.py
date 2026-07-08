from fastapi import APIRouter

from app.core.config import settings
from app.schemas.print_schemas import StatusResponse

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    return StatusResponse(status="online", version=settings.version)
