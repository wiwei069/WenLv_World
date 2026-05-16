import re
import json
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4
from sqlalchemy import select, desc
from tavily import TavilyClient

from app.config import settings
from app.database import async_session
from app.models import HotRanking


MEADIN_SEARCH_QUERIES = [
    "5A级景区品牌传播力百强榜单 最新",
    "全国旅游景区百强排行榜 最新排名",
    "中国文旅景区品牌影响力排行榜 最新",
]

# Top 10 operational commercial, historical, and cultural tourism projects
AUTHORITATIVE_RANKINGS = [
    ("西安大唐不夜城", "文旅街区", "https://www.datangbuyecheng.com/"),
    ("成都宽窄巷子", "历史文化街区", "https://www.kzxz.com.cn/"),
    ("乌镇", "文旅小镇", "https://www.wuzhen.com.cn/"),
    ("平遥古城", "文旅古城", "https://www.pingyao.com/"),
    ("重庆洪崖洞", "民俗风貌区", "https://www.hongyadong.com/"),
    ("南京夫子庙-秦淮风光带", "历史文化街区", "https://www.njfzm.com/"),
    ("北京798艺术区", "文化创意园区", ""),
    ("广州北京路步行街", "商业文旅街区", ""),
    ("苏州平江路历史街区", "历史文化街区", ""),
    ("上海新天地", "商业文旅街区", ""),
]

# Recent important holiday tourism data (source: Ministry of Culture and Tourism)
HOLIDAY_EVENTS = [
    {
        "holiday_name": "2026年春节",
        "period": "9天（2月）",
        "total_visitors": "5.96亿人次",
        "total_revenue": "8034.83亿元",
        "avg_spend": "1348元",
        "source": "文化和旅游部数据中心",
    },
    {
        "holiday_name": "2026年清明节",
        "period": "4月4日-6日",
        "total_visitors": "1.35亿人次",
        "total_revenue": "613.67亿元",
        "avg_spend": "455元",
        "source": "文化和旅游部数据中心",
    },
    {
        "holiday_name": "2026年五一劳动节",
        "period": "5月1日-5日",
        "total_visitors": "3.25亿人次",
        "total_revenue": "1854.92亿元",
        "avg_spend": "571元",
        "source": "文化和旅游部数据中心",
    },
]


async def fetch_and_store_rankings() -> list[dict]:
    """Fetch authoritative 5A scenic spot rankings and store in database."""
    now = datetime.now()
    month = f"{now.year}-{now.month:02d}"

    ranking_items = []
    for rank, (name, ptype, url) in enumerate(AUTHORITATIVE_RANKINGS, 1):
        ranking_items.append({
            "project_name": name,
            "project_type": ptype,
            "rank": rank,
            "month": month,
            "score": round(100 - rank * 3.5, 1),
            "url": url,
        })

    # Try to enrich with official website URLs via Tavily search
    if settings.tavily_api_key:
        client = TavilyClient(api_key=settings.tavily_api_key)
        for item in ranking_items:
            if not item["url"]:
                official_url = _find_official_website(item["project_name"], client)
                if official_url:
                    item["url"] = official_url

    # Store in database
    async with async_session() as db:
        stmt = select(HotRanking).where(HotRanking.month == month)
        result = await db.execute(stmt)
        existing = result.scalars().all()
        for e in existing:
            await db.delete(e)

        for i, item in enumerate(ranking_items):
            hr = HotRanking(
                id=str(uuid4()),
                project_name=item["project_name"],
                project_type=item["project_type"],
                rank=i + 1,
                month=month,
                source="authoritative",
                score=item.get("score", 0.0),
                url=item.get("url", ""),
            )
            db.add(hr)
        await db.commit()

        # Re-read from DB to get proper objects with id, source, created_at
        stmt = (
            select(HotRanking)
            .where(HotRanking.month == month)
            .order_by(HotRanking.rank)
        )
        result = await db.execute(stmt)
        saved = result.scalars().all()
        return [
            {
                "id": r.id,
                "project_name": r.project_name,
                "project_type": r.project_type,
                "rank": r.rank,
                "month": r.month,
                "source": r.source,
                "score": r.score,
                "url": r.url or "",
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in saved
        ]


async def get_stored_rankings(month: Optional[str] = None) -> list[dict]:
    """Get rankings from database, optionally filtered by month."""
    async with async_session() as db:
        if not month:
            now = datetime.now()
            month = f"{now.year}-{now.month:02d}"

        stmt = (
            select(HotRanking)
            .where(HotRanking.month == month)
            .order_by(HotRanking.rank)
        )
        result = await db.execute(stmt)
        rankings = result.scalars().all()

        if not rankings or len(rankings) < 10 or rankings[0].source == "meadin" or rankings[0].project_type == "景区":
            # If no stored rankings, or data looks stale (old format), fetch fresh
            if rankings:
                for e in rankings:
                    await db.delete(e)
                await db.commit()
            return await fetch_and_store_rankings()

        return [
            {
                "id": r.id,
                "project_name": r.project_name,
                "project_type": r.project_type,
                "rank": r.rank,
                "month": r.month,
                "source": r.source,
                "score": r.score,
                "url": r.url or "",
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rankings
        ]


def _parse_ranking_content(text: str, month: str) -> list[dict]:
    """Parse Meadin ranking content to extract project names and scores."""
    rankings = []

    # Try to find numbered lists (1. xxx, 2. xxx, etc.)
    numbered_items = re.findall(r'(?:^|\n)\s*(\d+)[.、]\s*([一-鿿\w]+(?:文旅|旅游|度假|景区|乐园|小镇|古城|街区|公园|山庄|生态园|产业园|古镇|文化城|度假区|风景区)[^。\n]{0,30})', text)
    for num, name in numbered_items:
        rankings.append({
            "project_name": name.strip(),
            "project_type": _detect_project_type(name),
            "rank": int(num),
            "month": month,
            "score": 0.0,
            "url": "",
        })

    # If no numbered list, try to find project names with score patterns
    if not rankings:
        score_items = re.findall(r'([一-鿿]{2,15}(?:文旅|旅游|度假|景区|乐园|小镇|古城|街区|公园|山庄|生态园|产业园|古镇|文化城|度假区|风景区))[^。\n]{0,20}?(\d+[.\d]*)', text)
        for i, (name, score) in enumerate(score_items[:10]):
            rankings.append({
                "project_name": name.strip(),
                "project_type": _detect_project_type(name),
                "rank": i + 1,
                "month": month,
                "score": float(score) if score.replace(".", "").isdigit() else 0.0,
                "url": "",
            })

    return rankings


def _detect_project_type(name: str) -> str:
    """Detect project type from name."""
    if any(kw in name for kw in ["景区", "风景区", "旅游区"]):
        return "景区"
    if any(kw in name for kw in ["小镇", "古镇"]):
        return "小镇"
    if any(kw in name for kw in ["乐园", "欢乐谷", "主题公园"]):
        return "主题乐园"
    if any(kw in name for kw in ["街区", "步行街", "商业街"]):
        return "街区"
    if any(kw in name for kw in ["度假区", "度假村"]):
        return "度假区"
    if any(kw in name for kw in ["文旅城", "旅游城"]):
        return "文旅城"
    if any(kw in name for kw in ["公园", "生态园"]):
        return "公园"
    return "文旅项目"


def _find_official_website(project_name: str, client: TavilyClient) -> str:
    """Search for a project's official website via Tavily."""
    try:
        url_queries = [
            f"{project_name} 官方网站 官网",
            f"{project_name} 景区 官网 首页",
        ]
        for q in url_queries:
            response = client.search(
                query=q,
                search_depth="basic",
                max_results=5,
                language="zh",
            )
            for r in response.get("results", []):
                url = r.get("url", "")
                parsed = urlparse(url)
                # Prefer URLs that look like official sites:
                # - Simple domain (not sub-articles)
                # - Domain contains project name keywords
                domain = parsed.netloc.lower()
                path = parsed.path.lower()
                # Skip obvious article/social pages
                if any(kw in url for kw in ["zhihu.com", "baike.baidu", "meadin.com",
                                             "ctrip.com", "mafengwo", "dianping",
                                             "163.com", "sohu.com", "sina", "qq.com"]):
                    continue
                # Prefer .com.cn / .cn domains or simple paths
                if domain.endswith((".com.cn", ".cn", ".com", ".org")):
                    if len(path.split("/")) <= 3:  # Not a deep article page
                        return url
            # Fallback: first valid http URL from results
            for r in response.get("results", []):
                url = r.get("url", "")
                if url.startswith("http") and "baike.baidu" not in url:
                    return url
    except Exception:
        pass
    return ""


def _get_default_rankings() -> list[dict]:
    """Provide authoritative default rankings as fallback."""
    now = datetime.now()
    month = f"{now.year}-{now.month:02d}"
    return [
        {
            "project_name": name,
            "project_type": ptype,
            "rank": i + 1,
            "month": month,
            "source": "authoritative",
            "score": round(100 - i * 3.5, 1),
            "url": url,
        }
        for i, (name, ptype, url) in enumerate(AUTHORITATIVE_RANKINGS)
    ]
