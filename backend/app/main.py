from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import search, projects, analysis, export, hot_rankings, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="亚洲文旅项目搜索与情报平台",
    description="CulTour Intelligence - Asian Cultural Tourism Project Search & Analysis Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://frontend-alpha-seven-18.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": str(exc)}},
    )


# Register routers
app.include_router(search.router)
app.include_router(projects.router)
app.include_router(analysis.router)
app.include_router(export.router)
app.include_router(hot_rankings.router)
app.include_router(stats.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
