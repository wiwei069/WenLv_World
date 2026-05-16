import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=True)
    chinese_name = Column(String, nullable=False, index=True)
    location = Column(String, default="")
    project_type = Column(String, default="", index=True)
    investors = Column(Text, default="[]")  # JSON array
    planning_firms = Column(Text, default="[]")  # JSON array
    construction_status = Column(String, default="unknown")  # planned|under_construction|operating|closed|unknown
    operational_data = Column(Text, default="{}")  # JSON dict
    visitor_count = Column(String, default="")
    annual_revenue = Column(String, default="")
    summary = Column(Text, default="")
    operation_mode = Column(Text, default="")  # 运营模式（自营/委托/合资等）
    cooperation_model = Column(Text, default="")  # 合作模式
    equity_structure = Column(Text, default="")  # 股权结构
    operation_features = Column(Text, default="")  # 运营特色
    annual_visitor_analysis = Column(Text, default="")  # 全年游客量分析
    image_urls = Column(Text, default="[]")  # 相关图片URL列表（JSON数组）
    created_at = Column(TIMESTAMP, default=_now)
    updated_at = Column(TIMESTAMP, default=_now, onupdate=_now)

    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan")
    social_mentions = relationship("SocialMention", back_populates="project", cascade="all, delete-orphan")
    analysis_reports = relationship("AnalysisReport", back_populates="project", cascade="all, delete-orphan")
    images = relationship("ProjectImage", back_populates="project", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, default="")
    source_type = Column(String, default="news")  # government|company|news|social
    platform = Column(String, default="tavily")  # tavily|xiaohongshu|douyin|weixin
    content = Column(Text, default="")
    snippet = Column(Text, default="")
    fetch_status = Column(String, default="pending")  # pending|success|failed
    fetched_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=_now)

    project = relationship("Project", back_populates="sources")

    __table_args__ = (
        Index("idx_sources_project", "project_id"),
        Index("idx_sources_platform", "platform"),
    )


class SocialMention(Base):
    __tablename__ = "social_mentions"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String, nullable=False)  # 小红书|抖音|微信
    platform_post_id = Column(String, default="")
    author = Column(String, default="")
    content = Column(Text, default="")
    sentiment = Column(Float, default=0.0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    posted_at = Column(TIMESTAMP, nullable=True)
    fetched_at = Column(TIMESTAMP, default=_now)

    project = relationship("Project", back_populates="social_mentions")

    __table_args__ = (
        Index("idx_social_mentions_project", "project_id"),
        Index("idx_social_mentions_platform", "platform"),
    )


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String, default="full")
    summary = Column(Text, default="")
    analysis = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)
    key_findings = Column(Text, default="[]")  # JSON array
    recommendations = Column(Text, default="[]")  # JSON array
    model_version = Column(String, default="")
    tokens_used = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=_now)

    project = relationship("Project", back_populates="analysis_reports")

    __table_args__ = (
        Index("idx_reports_project", "project_id"),
    )


class HotRanking(Base):
    __tablename__ = "hot_rankings"

    id = Column(String, primary_key=True, default=_uuid)
    project_name = Column(String, nullable=False)
    project_type = Column(String, default="")
    rank = Column(Integer, nullable=False)
    month = Column(String, nullable=False)  # e.g. "2026-05"
    source = Column(String, default="meadin")  # meadin|ctrip
    score = Column(Float, default=0.0)
    url = Column(String, default="")  # official website or related article URL
    created_at = Column(TIMESTAMP, default=_now)

    __table_args__ = (
        Index("idx_hot_rankings_month", "month"),
    )


class ProjectImage(Base):
    __tablename__ = "project_images"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    alt_text = Column(String, default="")
    source_url = Column(String, default="")
    created_at = Column(TIMESTAMP, default=_now)

    project = relationship("Project", back_populates="images")

    __table_args__ = (
        Index("idx_project_images_project", "project_id"),
    )



class SearchTask(Base):
    __tablename__ = "search_tasks"

    id = Column(String, primary_key=True, default=_uuid)
    query = Column(String, nullable=False)
    status = Column(String, default="running")  # running|complete|error
    projects_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=_now)
    completed_at = Column(TIMESTAMP, nullable=True)
