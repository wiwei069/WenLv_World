import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Project, Source, SocialMention, AnalysisReport
from app.schemas import (
    ProjectResponse,
    SourceResponse,
    SocialMentionResponse,
    AnalysisReportResponse,
    ExportPayload,
)
from app.services.export_service import assemble_export_markdown, assemble_urls_text
from app.services.pdf_service import generate_report_pdf

router = APIRouter(prefix="/api/projects", tags=["export"])


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
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("/{project_id}/export", response_model=ExportPayload)
async def export_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get full export payload for NotebookLM."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    source_stmt = select(Source).where(Source.project_id == project_id)
    source_result = await db.execute(source_stmt)
    sources = source_result.scalars().all()

    mention_stmt = select(SocialMention).where(SocialMention.project_id == project_id).limit(20)
    mention_result = await db.execute(mention_stmt)
    mentions = mention_result.scalars().all()

    report_stmt = (
        select(AnalysisReport)
        .where(AnalysisReport.project_id == project_id)
        .order_by(desc(AnalysisReport.created_at))
        .limit(1)
    )
    report_result = await db.execute(report_stmt)
    report = report_result.scalar_one_or_none()

    all_urls = [s.url for s in sources]

    return ExportPayload(
        project=_project_to_response(project),
        sources=[SourceResponse(
            id=s.id, project_id=s.project_id, url=s.url, title=s.title or "",
            source_type=s.source_type or "news", platform=s.platform or "tavily",
            snippet=(s.snippet or (s.content or "")[:200]),
            fetch_status=s.fetch_status or "pending", fetched_at=s.fetched_at,
            created_at=s.created_at,
        ) for s in sources],
        social_mentions=[SocialMentionResponse(
            id=m.id, platform=m.platform or "", author=m.author or "",
            content=(m.content or "")[:500], sentiment=m.sentiment or 0.0,
            likes_count=m.likes_count or 0, comments_count=m.comments_count or 0,
            posted_at=m.posted_at, fetched_at=m.fetched_at,
        ) for m in mentions],
        report=AnalysisReportResponse(
            id=report.id, project_id=report.project_id,
            summary=report.summary or "", analysis=report.analysis or "",
            confidence_score=report.confidence_score or 0.0,
            key_findings=json.loads(report.key_findings) if report.key_findings and report.key_findings != "[]" else [],
            recommendations=json.loads(report.recommendations) if report.recommendations and report.recommendations != "[]" else [],
            model_version=report.model_version or "",
            tokens_used=report.tokens_used or 0,
            created_at=report.created_at,
        ) if report else None,
        all_urls=all_urls,
    )


@router.get("/{project_id}/export/markdown", response_class=PlainTextResponse)
async def export_project_markdown(project_id: str, db: AsyncSession = Depends(get_db)):
    """Export project as plain markdown for NotebookLM."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    source_stmt = select(Source).where(Source.project_id == project_id)
    source_result = await db.execute(source_stmt)
    sources = source_result.scalars().all()

    mention_stmt = select(SocialMention).where(SocialMention.project_id == project_id).limit(20)
    mention_result = await db.execute(mention_stmt)
    mentions = mention_result.scalars().all()

    report_stmt = (
        select(AnalysisReport)
        .where(AnalysisReport.project_id == project_id)
        .order_by(desc(AnalysisReport.created_at))
        .limit(1)
    )
    report_result = await db.execute(report_stmt)
    report = report_result.scalar_one_or_none()

    markdown = assemble_export_markdown(project, sources, mentions, report)
    return PlainTextResponse(markdown, media_type="text/plain; charset=utf-8")


@router.get("/{project_id}/export/urls", response_class=PlainTextResponse)
async def export_project_urls(project_id: str, db: AsyncSession = Depends(get_db)):
    """Export all source URLs as text file."""
    stmt = select(Source).where(Source.project_id == project_id)
    result = await db.execute(stmt)
    sources = result.scalars().all()

    if not sources:
        raise HTTPException(status_code=404, detail="没有来源链接")

    return PlainTextResponse(assemble_urls_text(sources), media_type="text/plain; charset=utf-8")


@router.get("/{project_id}/export/pdf")
async def export_project_pdf(project_id: str, db: AsyncSession = Depends(get_db)):
    """Export analysis report as PDF."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    source_stmt = select(Source).where(Source.project_id == project_id)
    source_result = await db.execute(source_stmt)
    sources = source_result.scalars().all()

    report_stmt = (
        select(AnalysisReport)
        .where(AnalysisReport.project_id == project_id)
        .order_by(desc(AnalysisReport.created_at))
        .limit(1)
    )
    report_result = await db.execute(report_stmt)
    report = report_result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="暂无分析报告，请先生成 AI 分析")

    STATUS_LABELS = {
        "planned": "规划中", "under_construction": "建设中",
        "operating": "运营中", "closed": "已关闭",
    }

    pdf_bytes = generate_report_pdf(
        project_name=project.chinese_name,
        project_info={
            "location": project.location,
            "project_type": project.project_type,
            "construction_status": STATUS_LABELS.get(project.construction_status, project.construction_status),
            "visitor_count": project.visitor_count,
            "annual_revenue": project.annual_revenue,
            "operation_mode": project.operation_mode,
            "investors": json.loads(project.investors) if project.investors and project.investors != "[]" else [],
        },
        analysis_text=report.analysis,
        recommendations=json.loads(report.recommendations) if report.recommendations and report.recommendations != "[]" else [],
        model_version=report.model_version,
        confidence_score=report.confidence_score,
        created_at=report.created_at,
        sources=[{"title": s.title, "url": s.url} for s in sources],
    )

    filename = f"{project.chinese_name}_分析报告.pdf"
    # URL-encode the filename for Content-Disposition
    from urllib.parse import quote
    encoded = quote(filename)

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
        },
    )
