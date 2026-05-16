import json
import asyncio
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import select

from app.database import async_session
from app.models import Project, Source, SocialMention, SearchTask, ProjectImage
from app.schemas import SearchRequest, SearchResponse, SearchStatusResponse
from app.services.tavily_service import TavilyService
from app.services.scraper_service import SocialScraper

router = APIRouter(prefix="/api/search", tags=["search"])

# In-memory task store for async task status
_task_store: dict[str, dict] = {}


async def _run_search(
    task_id: str,
    query: str,
    project_type: Optional[str],
):
    """Background task for searching and processing results."""
    async with async_session() as db:
        try:
            # Create search task record
            task = SearchTask(id=task_id, query=query, status="running")
            db.add(task)
            await db.commit()

            tavily = TavilyService()
            results, images = await tavily.search_projects(query)

            if not results:
                _task_store[task_id] = {"status": "complete", "projects_found": 0}
                stmt = select(SearchTask).where(SearchTask.id == task_id)
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                if task:
                    task.status = "complete"
                    task.projects_found = 0
                    task.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                return

            # Parse project from results
            project_data = tavily.parse_project_from_results(results, query, additional_images=images)
            if project_type:
                project_data["project_type"] = project_type

            # Check for existing project with same name
            stmt = select(Project).where(Project.chinese_name == project_data["chinese_name"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                project = existing
                for key, val in project_data.items():
                    if val and key != "chinese_name":
                        if isinstance(val, list):
                            setattr(project, key, json.dumps(val, ensure_ascii=False))
                        else:
                            setattr(project, key, val)
            else:
                project = Project(
                    id=str(uuid4()),
                    chinese_name=project_data.get("chinese_name", query),
                    location=project_data.get("location", ""),
                    project_type=project_data.get("project_type", ""),
                    investors=json.dumps(project_data.get("investors", []), ensure_ascii=False),
                    planning_firms=json.dumps(project_data.get("planning_firms", []), ensure_ascii=False),
                    construction_status=project_data.get("construction_status", "unknown"),
                    visitor_count=project_data.get("visitor_count", ""),
                    annual_revenue=project_data.get("annual_revenue", ""),
                    summary=project_data.get("summary", ""),
                    operation_mode=project_data.get("operation_mode", ""),
                    cooperation_model=project_data.get("cooperation_model", ""),
                    equity_structure=project_data.get("equity_structure", ""),
                    operation_features=project_data.get("operation_features", ""),
                    annual_visitor_analysis=project_data.get("annual_visitor_analysis", ""),
                    image_urls=json.dumps(project_data.get("image_urls", []), ensure_ascii=False),
                )
                db.add(project)
                await db.flush()

                # Save project images from search results
                img_urls = project_data.get("image_urls", [])
                if img_urls:
                    for img_url in img_urls[:20]:
                        img = ProjectImage(
                            id=str(uuid4()),
                            project_id=project.id,
                            url=img_url,
                            alt_text=f"{project.chinese_name} - 项目图片",
                            source_url="",
                        )
                        db.add(img)

            # Save sources
            for r in results:
                source = Source(
                    id=str(uuid4()),
                    project_id=project.id,
                    url=r.get("url", ""),
                    title=r.get("title", ""),
                    source_type=r.get("source_type", "news"),
                    platform=r.get("platform", "tavily"),
                    content=r.get("content", "")[:5000],
                    snippet=r.get("content", "")[:300],
                    fetch_status="success",
                    fetched_at=datetime.now(timezone.utc),
                )
                db.add(source)

            # Create social mention records from Tavily social results
            social_sources = [r for r in results if r.get("source_type") == "social"]
            for r in social_sources:
                mention = SocialMention(
                    id=str(uuid4()),
                    project_id=project.id,
                    platform=r.get("platform", "小红书"),
                    author="",
                    content=(r.get("content", "") or "")[:2000],
                    sentiment=0.0,
                    likes_count=0,
                    comments_count=0,
                )
                db.add(mention)

            await db.commit()

            # Social scraping disabled (OOM risk on Render free tier)
            # asyncio.create_task(_run_social_scraping(project.id, project.chinese_name, query))

            _task_store[task_id] = {"status": "complete", "projects_found": 1}
            stmt = select(SearchTask).where(SearchTask.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()
            if task:
                task.status = "complete"
                task.projects_found = 1
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()

        except Exception as e:
            _task_store[task_id] = {"status": "error", "error": str(e)}
            stmt = select(SearchTask).where(SearchTask.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()
            if task:
                task.status = "error"
                task.error_message = str(e)
                await db.commit()


async def _run_social_scraping(project_id: str, project_name: str, keyword: str):
    """Background social media scraping."""
    try:
        async with SocialScraper() as scraper:
            mentions = await scraper.search_all(project_name, keyword)

        async with async_session() as session:
            for m in mentions:
                mention = SocialMention(
                    id=str(uuid4()),
                    project_id=project_id,
                    platform=m.get("platform", ""),
                    author=m.get("author", ""),
                    content=m.get("content", "")[:2000],
                    sentiment=m.get("sentiment", 0.0),
                    likes_count=m.get("likes_count", 0),
                    comments_count=m.get("comments_count", 0),
                )
                session.add(mention)
            await session.commit()
    except Exception:
        pass  # Social scraping failure is non-fatal


@router.post("", response_model=SearchResponse)
async def search_projects(request: SearchRequest):
    """Start an async search for cultural tourism projects."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")

    task_id = str(uuid4())
    _task_store[task_id] = {"status": "running", "projects_found": 0}

    # Background task handles everything: DB write + search
    asyncio.create_task(_run_search(task_id, request.query, request.project_type))

    return SearchResponse(task_id=task_id, status="running")


@router.get("/status/{task_id}", response_model=SearchStatusResponse)
async def search_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """Poll search task status."""
    stmt = select(SearchTask).where(SearchTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="搜索任务不存在")

    return SearchStatusResponse(
        status=task.status,
        projects_found=task.projects_found,
        error_message=task.error_message,
    )
