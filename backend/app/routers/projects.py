import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Project, Source, SocialMention, AnalysisReport, ProjectImage
from app.schemas import (
    ProjectResponse,
    ProjectListItem,
    ProjectListResponse,
    ProjectDetailResponse,
    SourceResponse,
    SocialMentionResponse,
    AnalysisReportResponse,
    ProjectImageResponse,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_to_list_item(p: Project) -> ProjectListItem:
    return ProjectListItem(
        id=p.id,
        chinese_name=p.chinese_name,
        name=p.name or "",
        location=p.location or "",
        project_type=p.project_type or "",
        construction_status=p.construction_status or "unknown",
        visitor_count=p.visitor_count or "",
        annual_revenue=p.annual_revenue or "",
        summary=(p.summary or "")[:150],
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _project_to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        chinese_name=p.chinese_name,
        name=p.name or "",
        location=p.location or "",
        project_type=p.project_type or "",
        investors=json.loads(p.investors) if p.investors and p.investors != "[]" else [],
        planning_firms=json.loads(p.planning_firms) if p.planning_firms and p.planning_firms != "[]" else [],
        construction_status=p.construction_status or "unknown",
        operational_data=json.loads(p.operational_data) if p.operational_data and p.operational_data != "{}" else {},
        visitor_count=p.visitor_count or "",
        annual_revenue=p.annual_revenue or "",
        summary=p.summary or "",
        operation_mode=p.operation_mode or "",
        cooperation_model=p.cooperation_model or "",
        equity_structure=p.equity_structure or "",
        operation_features=p.operation_features or "",
        annual_visitor_analysis=p.annual_visitor_analysis or "",
        image_urls=json.loads(p.image_urls) if p.image_urls and p.image_urls != "[]" else [],
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _image_to_response(img: ProjectImage) -> ProjectImageResponse:
    return ProjectImageResponse(
        id=img.id,
        project_id=img.project_id,
        url=img.url,
        alt_text=img.alt_text or "",
        source_url=img.source_url or "",
        created_at=img.created_at,
    )


def _source_to_response(s: Source) -> SourceResponse:
    return SourceResponse(
        id=s.id,
        project_id=s.project_id,
        url=s.url,
        title=s.title or "",
        source_type=s.source_type or "news",
        platform=s.platform or "tavily",
        snippet=(s.snippet or (s.content or "")[:200]),
        fetch_status=s.fetch_status or "pending",
        fetched_at=s.fetched_at,
        created_at=s.created_at,
    )


def _mention_to_response(m: SocialMention) -> SocialMentionResponse:
    return SocialMentionResponse(
        id=m.id,
        platform=m.platform or "",
        author=m.author or "",
        content=(m.content or "")[:500],
        sentiment=m.sentiment or 0.0,
        likes_count=m.likes_count or 0,
        comments_count=m.comments_count or 0,
        posted_at=m.posted_at,
        fetched_at=m.fetched_at,
    )


def _report_to_response(r: AnalysisReport) -> AnalysisReportResponse:
    return AnalysisReportResponse(
        id=r.id,
        project_id=r.project_id,
        summary=r.summary or "",
        analysis=r.analysis or "",
        confidence_score=r.confidence_score or 0.0,
        key_findings=json.loads(r.key_findings) if r.key_findings and r.key_findings != "[]" else [],
        recommendations=json.loads(r.recommendations) if r.recommendations and r.recommendations != "[]" else [],
        model_version=r.model_version or "",
        tokens_used=r.tokens_used or 0,
        created_at=r.created_at,
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query("", description="搜索项目名称关键字"),
    db: AsyncSession = Depends(get_db),
):
    """List all searched projects with pagination."""
    query = select(Project)

    if search:
        query = query.where(Project.chinese_name.contains(search))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page
    query = query.order_by(desc(Project.updated_at)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectListResponse(
        projects=[_project_to_list_item(p) for p in projects],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get full project detail with sources, social mentions, and analysis."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # Get sources
    source_stmt = select(Source).where(Source.project_id == project_id)
    source_result = await db.execute(source_stmt)
    sources = source_result.scalars().all()

    # Get social mentions
    mention_stmt = select(SocialMention).where(SocialMention.project_id == project_id)
    mention_result = await db.execute(mention_stmt)
    mentions = mention_result.scalars().all()

    # Get latest analysis report
    report_stmt = (
        select(AnalysisReport)
        .where(AnalysisReport.project_id == project_id)
        .order_by(desc(AnalysisReport.created_at))
        .limit(1)
    )
    report_result = await db.execute(report_stmt)
    report = report_result.scalar_one_or_none()

    # Get images
    image_stmt = select(ProjectImage).where(ProjectImage.project_id == project_id)
    image_result = await db.execute(image_stmt)
    images = image_result.scalars().all()

    return ProjectDetailResponse(
        project=_project_to_response(project),
        sources=[_source_to_response(s) for s in sources],
        social_mentions=[_mention_to_response(m) for m in mentions],
        analysis_report=_report_to_response(report) if report else None,
        images=[_image_to_response(img) for img in images],
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project and all its related data."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.delete(project)
    await db.commit()

    return {"status": "deleted"}
