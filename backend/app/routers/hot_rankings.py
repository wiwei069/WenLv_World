from datetime import datetime
from fastapi import APIRouter, Query

from app.schemas import HotRankingListResponse, HotRankingResponse, HolidayTourismItem
from app.services.meadin_service import get_stored_rankings, HOLIDAY_EVENTS

router = APIRouter(prefix="/api/hot-rankings", tags=["hot-rankings"])


@router.get("", response_model=HotRankingListResponse)
async def get_hot_rankings(month: str = Query("", description="月份，格式：2026-05")):
    """Get top 10 operational commercial/historical/cultural tourism project rankings."""
    rankings = await get_stored_rankings(month if month else None)
    current_month = month if month else f"{datetime.now().year}-{datetime.now().month:02d}"

    return HotRankingListResponse(
        rankings=[
            HotRankingResponse(**r) for r in rankings
        ],
        month=current_month,
        total=len(rankings),
        holiday_data=[
            HolidayTourismItem(**h) for h in HOLIDAY_EVENTS
        ],
    )
