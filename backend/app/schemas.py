from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ---- Project ----
class ProjectBase(BaseModel):
    name: str = ""
    chinese_name: str
    location: str = ""
    project_type: str = ""
    investors: list[str] = []
    planning_firms: list[str] = []
    construction_status: str = "unknown"
    operational_data: dict = {}
    visitor_count: str = ""
    annual_revenue: str = ""
    summary: str = ""
    operation_mode: str = ""
    cooperation_model: str = ""
    equity_structure: str = ""
    operation_features: str = ""
    annual_visitor_analysis: str = ""
    image_urls: list[str] = []


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListItem(BaseModel):
    id: str
    chinese_name: str
    name: str
    location: str
    project_type: str
    construction_status: str
    visitor_count: str
    annual_revenue: str
    summary: str
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectListItem]
    total: int
    page: int
    per_page: int


# ---- Source ----
class SourceResponse(BaseModel):
    id: str
    project_id: str
    url: str
    title: str
    source_type: str
    platform: str
    snippet: str
    fetch_status: str
    fetched_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Social Mention ----
class SocialMentionResponse(BaseModel):
    id: str
    platform: str
    author: str
    content: str
    sentiment: float
    likes_count: int
    comments_count: int
    posted_at: Optional[datetime] = None
    fetched_at: datetime

    class Config:
        from_attributes = True


# ---- Analysis Report ----
class AnalysisReportResponse(BaseModel):
    id: str
    project_id: str
    summary: str
    analysis: str
    confidence_score: float
    key_findings: list[str] = []
    recommendations: list[str] = []
    model_version: str
    tokens_used: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Search ----
class SearchRequest(BaseModel):
    query: str
    project_type: Optional[str] = None


class SearchResponse(BaseModel):
    task_id: str
    status: str


class SearchStatusResponse(BaseModel):
    status: str
    projects_found: int
    error_message: Optional[str] = None


# ---- Project Images ----
class ProjectImageResponse(BaseModel):
    id: str
    project_id: str
    url: str
    alt_text: str
    source_url: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Project Detail ----
class ProjectDetailResponse(BaseModel):
    project: ProjectResponse
    sources: list[SourceResponse] = []
    social_mentions: list[SocialMentionResponse] = []
    analysis_report: Optional[AnalysisReportResponse] = None
    images: list[ProjectImageResponse] = []


# ---- Export ----
class ExportPayload(BaseModel):
    project: ProjectResponse
    sources: list[SourceResponse] = []
    social_mentions: list[SocialMentionResponse] = []
    report: Optional[AnalysisReportResponse] = None
    all_urls: list[str] = []


# ---- Hot Rankings ----
class HotRankingResponse(BaseModel):
    id: str
    project_name: str
    project_type: str
    rank: int
    month: str
    source: str
    score: float
    url: str = ""
    created_at: datetime


class HolidayTourismItem(BaseModel):
    holiday_name: str
    period: str
    total_visitors: str
    total_revenue: str
    avg_spend: str
    source: str


class HotRankingListResponse(BaseModel):
    rankings: list[HotRankingResponse]
    month: str
    total: int
    holiday_data: list[HolidayTourismItem] = []


# ---- Generic ----
class HealthResponse(BaseModel):
    status: str
    version: str


class ErrorResponse(BaseModel):
    error: dict
