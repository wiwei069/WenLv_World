import asyncio
import json
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models import Project, Source, SocialMention, AnalysisReport
from app.schemas import AnalysisReportResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/projects", tags=["analysis"])

_analysis_task_store: dict[str, dict] = {}


async def _run_analysis(project_id: str, task_id: str):
    """Background task for AI analysis."""
    async with async_session() as db:
        try:
            project_stmt = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_stmt)
            project = project_result.scalar_one_or_none()

            if not project:
                _analysis_task_store[task_id] = {"status": "error", "error": "项目不存在"}
                return

            source_stmt = select(Source).where(Source.project_id == project_id)
            source_result = await db.execute(source_stmt)
            sources = source_result.scalars().all()

            mention_stmt = select(SocialMention).where(SocialMention.project_id == project_id)
            mention_result = await db.execute(mention_stmt)
            mentions = mention_result.scalars().all()

            service = AnalysisService()
            report_data = await service.generate_report(project, sources, mentions)

            report = AnalysisReport(
                id=str(uuid4()),
                project_id=project_id,
                report_type="full",
                summary=report_data.get("summary", ""),
                analysis=report_data.get("analysis", ""),
                confidence_score=report_data.get("confidence_score", 0.0),
                key_findings=json.dumps(report_data.get("key_findings", []), ensure_ascii=False),
                recommendations=json.dumps(report_data.get("recommendations", []), ensure_ascii=False),
                model_version=report_data.get("model_version", ""),
                tokens_used=report_data.get("tokens_used", 0),
            )
            db.add(report)
            await db.commit()

            _analysis_task_store[task_id] = {"status": "complete", "report_id": report.id}

        except Exception as e:
            _analysis_task_store[task_id] = {"status": "error", "error": str(e)}


@router.post("/{project_id}/analyze")
async def analyze_project(project_id: str):
    """Trigger AI analysis for a project."""
    task_id = str(uuid4())
    _analysis_task_store[task_id] = {"status": "running"}

    asyncio.create_task(_run_analysis(project_id, task_id))

    return {"task_id": task_id, "status": "running"}


@router.get("/{project_id}/analysis/status/{task_id}")
async def analysis_status(project_id: str, task_id: str):
    """Poll analysis task status."""
    if task_id not in _analysis_task_store:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    return _analysis_task_store[task_id]


@router.get("/{project_id}/analysis", response_model=AnalysisReportResponse)
async def get_analysis_report(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get the latest analysis report for a project."""
    stmt = (
        select(AnalysisReport)
        .where(AnalysisReport.project_id == project_id)
        .order_by(desc(AnalysisReport.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="尚未生成分析报告")

    return AnalysisReportResponse(
        id=report.id,
        project_id=report.project_id,
        summary=report.summary or "",
        analysis=report.analysis or "",
        confidence_score=report.confidence_score or 0.0,
        key_findings=json.loads(report.key_findings) if report.key_findings and report.key_findings != "[]" else [],
        recommendations=json.loads(report.recommendations) if report.recommendations and report.recommendations != "[]" else [],
        model_version=report.model_version or "",
        tokens_used=report.tokens_used or 0,
        created_at=report.created_at,
    )
