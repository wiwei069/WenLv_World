import json
from app.models import Project, Source, SocialMention, AnalysisReport


_SENTIMENT_LABELS = {
    0: "😐 中性",
    1: "😊 正面",
    -1: "😟 负面",
}


def _sentiment_label(score: float) -> str:
    if score > 0.2:
        return "😊 正面"
    elif score < -0.2:
        return "😟 负面"
    return "😐 中性"


def _status_label(status: str) -> str:
    labels = {
        "planned": "规划中",
        "under_construction": "建设中",
        "operating": "运营中",
        "closed": "已关闭",
    }
    return labels.get(status, status)


def assemble_export_markdown(
    project: Project,
    sources: list[Source],
    social_mentions: list[SocialMention],
    report: AnalysisReport | None,
) -> str:
    """Assemble a complete markdown document for NotebookLM export."""
    lines = []

    # Title
    lines.append(f"# {project.chinese_name} - 文旅大视界项目分析报告")
    lines.append("")

    # Project Info
    lines.append("## 项目信息")
    lines.append(f"- **项目名称**: {project.chinese_name or '待确认'}")
    if project.name:
        lines.append(f"- **英文名称**: {project.name}")
    lines.append(f"- **所在地**: {project.location or '信息收集中'}")
    lines.append(f"- **项目类型**: {project.project_type or '信息收集中'}")
    lines.append(f"- **建设状态**: {_status_label(project.construction_status)}")
    if project.investors and project.investors != "[]":
        inv = json.loads(project.investors)
        lines.append(f"- **投资方**: {'、'.join(inv)}")
    if project.planning_firms and project.planning_firms != "[]":
        pf = json.loads(project.planning_firms)
        lines.append(f"- **规划设计**: {'、'.join(pf)}")
    if project.visitor_count:
        lines.append(f"- **年接待游客**: {project.visitor_count}")
    if project.annual_revenue:
        lines.append(f"- **年收入**: {project.annual_revenue}")
    if project.operational_data and project.operational_data != "{}":
        od = json.loads(project.operational_data)
        for key, val in od.items():
            lines.append(f"- **{key}**: {val}")
    lines.append("")

    # Source Links - formatted for NotebookLM auto-recognition
    lines.append("## 来源链接")
    lines.append("")
    for i, s in enumerate(sources, 1):
        title = s.title or "来源"
        lines.append(f"{i}. {title}")
        lines.append(f"   {s.url}")
        lines.append("")

    # Social Mentions
    if social_mentions:
        lines.append("## 社交媒体评价")
        lines.append("以下为社交媒体平台收集的用户评价：")
        lines.append("")
        for m in social_mentions:
            content_preview = (m.content or "")[:200]
            lines.append(f"- **[{m.platform}]** {m.author or '匿名用户'}: {content_preview}")
            lines.append(f"  - 情感倾向: {_sentiment_label(m.sentiment)} | ❤️ {m.likes_count} | 💬 {m.comments_count}")
        lines.append("")

    # Analysis Report
    if report:
        lines.append("## AI 分析报告")
        lines.append("")
        lines.append(report.analysis)
        lines.append("")
        lines.append("---")
        lines.append(f"*报告生成时间: {report.created_at.strftime('%Y-%m-%d %H:%M') if report.created_at else 'N/A'}*")
        lines.append(f"*置信度: {report.confidence_score * 100:.0f}%*")
        lines.append(f"*分析模型: {report.model_version}*")

    return "\n".join(lines)


def assemble_urls_text(sources: list[Source]) -> str:
    """Assemble a simple text file with all source URLs."""
    lines = ["# 来源链接汇总", ""]
    for i, s in enumerate(sources, 1):
        title = s.title or "无标题"
        lines.append(f"{i}. {title}")
        lines.append(f"   {s.url}")
        lines.append("")
    return "\n".join(lines)
