from fastapi import APIRouter
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Project, Source, AnalysisReport, HotRanking
from fastapi import Depends

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_projects = await db.scalar(select(func.count(Project.id)))
    total_sources = await db.scalar(select(func.count(Source.id)))
    total_reports = await db.scalar(select(func.count(AnalysisReport.id)))

    # Source breakdown by platform
    platform_counts = await db.execute(
        select(Source.platform, func.count(Source.id)).group_by(Source.platform)
    )
    sources_by_platform = {row[0] or "other": row[1] for row in platform_counts}

    # Source breakdown by source_type
    type_counts = await db.execute(
        select(Source.source_type, func.count(Source.id)).group_by(Source.source_type)
    )
    sources_by_type = {row[0] or "other": row[1] for row in type_counts}

    # Report stats
    latest_reports = await db.execute(
        select(AnalysisReport).order_by(AnalysisReport.created_at.desc()).limit(10)
    )
    recent_reports = [
        {
            "id": r.id,
            "project_id": r.project_id,
            "summary": r.summary[:200] if r.summary else "",
            "confidence_score": r.confidence_score,
            "model_version": r.model_version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in latest_reports.scalars().all()
    ]

    # Basic project stats
    project_status_counts = await db.execute(
        select(Project.construction_status, func.count(Project.id)).group_by(Project.construction_status)
    )
    projects_by_status = {row[0] or "unknown": row[1] for row in project_status_counts}

    project_type_counts = await db.execute(
        select(Project.project_type, func.count(Project.id)).group_by(Project.project_type)
    )
    projects_by_type = {row[0] or "其他": row[1] for row in project_type_counts}

    return {
        "total_projects": total_projects or 0,
        "total_sources": total_sources or 0,
        "total_reports": total_reports or 0,
        "sources_by_platform": sources_by_platform,
        "sources_by_type": sources_by_type,
        "recent_reports": recent_reports,
        "projects_by_status": projects_by_status,
        "projects_by_type": projects_by_type,
    }
