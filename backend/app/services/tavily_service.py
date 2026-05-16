import asyncio
import json
import re
from typing import Optional
from tavily import TavilyClient
from app.config import settings
from app.utils.text_utils import (
    extract_project_name,
    normalize_location,
    detect_construction_status,
    extract_visitor_count,
    extract_revenue,
)


# 政府及权威信息来源
GOVERNMENT_DOMAINS = [
    "gov.cn",
    "mct.gov.cn",       # 文化和旅游部
    "cnki.net",
    "xinhuanet.com",
    "people.com.cn",
    "ce.cn",
    "china.com.cn",
    "chinanews.com",
]

# 行业研究及口碑平台
INDUSTRY_DOMAINS = [
    "meadin.com",       # 迈点研究院
    "ctrip.com",        # 携程
    "mafengwo.cn",      # 马蜂窝
    "dianping.com",     # 大众点评
    "qunar.com",        # 去哪儿
    "tuniu.com",        # 途牛
    "fliggy.com",       # 飞猪
    "lvmama.com",       # 驴妈妈
]

SOCIAL_DOMAINS = [
    "xiaohongshu.com",
    "douyin.com",
    "weixin.qq.com",
    "mp.weixin.qq.com",
    "weibo.com",
]

# 学术研究机构
ACADEMIC_DOMAINS = [
    "cnki.net",
    "cass.cn",          # 中国社会科学院
    "ac.cn",            # 中国科学院
    "edu.cn",           # 教育网
]

# 旅游行业官网
TRAVEL_DOMAINS = [
    "ctrip.com",
    "qunar.com",
    "tuniu.com",
    "lvmama.com",
    "fliggy.com",
    "mafengwo.cn",
    "trip.com",
    "ly.com",           # 同程旅行
]

# 关键词前缀 - 用于判断是否为真正相关的项目内容
RELEVANCE_KEYWORDS = [
    "景区", "旅游", "文旅", "度假", "乐园", "小镇", "古城",
    "项目", "运营", "游客", "投资", "开业", "门票", "收入",
    "游客量", "客流量", "品牌", "传播力", "排名",
    "行业", "指数", "数据", "接待", "增长率", "同比",
    "规划", "建设", "发展", "文化", "体验", "服务",
]


class TavilyService:
    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None

    def is_available(self) -> bool:
        return self.client is not None and bool(settings.tavily_api_key)

    async def search_projects(self, query: str, max_results: int = None) -> tuple[list[dict], list[str]]:
        """Search for cultural tourism projects with multi-dimensional queries.
        Returns (results, collected_image_urls)."""
        if not self.is_available():
            return self._mock_search(query), []

        max_results = max_results or settings.tavily_max_results
        all_results = []
        all_images: list[str] = []

        def _collect_images(response: dict) -> list[str]:
            """Extract top-level images from Tavily response."""
            imgs = response.get("images", [])
            urls = []
            if imgs and isinstance(imgs, list):
                for img in imgs:
                    if isinstance(img, str):
                        if img.startswith("http"):
                            urls.append(img)
                    elif isinstance(img, dict):
                        url = img.get("url") or img.get("image") or ""
                        if url.startswith("http"):
                            urls.append(url)
            return urls

        # 1. Main search - government & information domains
        main_response = await self._search(
            query=query,
            search_depth=settings.tavily_search_depth,
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
            include_images=True,
            include_domains=GOVERNMENT_DOMAINS,
            language="zh",
        )
        for r in main_response.get("results", []):
            all_results.append(self._format_result(r, self._classify_source(r.get("url", "")), "tavily"))
        all_images.extend(_collect_images(main_response))

        # 2. Industry data search - operational metrics
        industry_queries = [
            f"{query} 运营数据 游客量 收入",
            f"{query} 运营模式 合作模式",
        ]
        for iq in industry_queries:
            try:
                ir = await self._search(
                    query=iq,
                    search_depth="basic",
                    max_results=5,
                    include_images=True,
                    include_domains=INDUSTRY_DOMAINS,
                    language="zh",
                )
                for r in ir.get("results", []):
                    all_results.append(self._format_result(r, self._classify_source(r.get("url", "")), "tavily"))
                all_images.extend(_collect_images(ir))
            except Exception:
                pass

        # 3. Official data service search (文化和旅游部数据服务)
        try:
            gov_query = f"site:mct.gov.cn {query} 景区 数据"
            gov_r = await self._search(
                query=gov_query,
                search_depth="basic",
                max_results=5,
                include_images=True,
                language="zh",
            )
            for r in gov_r.get("results", []):
                all_results.append(self._format_result(r, "government", "tavily"))
            all_images.extend(_collect_images(gov_r))
        except Exception:
            pass

        # 4. Social platforms search
        social_query = f"{query} 旅游 评价"
        try:
            social_response = await self._search(
                query=social_query,
                search_depth="basic",
                max_results=5,
                include_images=True,
                include_domains=SOCIAL_DOMAINS,
                language="zh",
            )
            for r in social_response.get("results", []):
                all_results.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "source_type": "social",
                    "platform": self._detect_social_platform(r.get("url", "")),
                })
            all_images.extend(_collect_images(social_response))
        except Exception:
            pass

        # 5. Travel platform search - 门票价格、游客评价、运营数据
        travel_queries = [
            f"{query} 门票 价格 开放时间",
            f"{query} 游客评价 口碑",
            f"{query} 游玩攻略 推荐",
        ]
        for tq in travel_queries:
            try:
                tr = await self._search(
                    query=tq,
                    search_depth="basic",
                    max_results=5,
                    include_images=True,
                    include_domains=TRAVEL_DOMAINS,
                    language="zh",
                )
                for r in tr.get("results", []):
                    all_results.append(
                        self._format_result(r, self._classify_source(r.get("url", "")), "tavily")
                    )
                all_images.extend(_collect_images(tr))
            except Exception:
                pass

        # 6. Academic / research search
        try:
            academic_query = f"{query} 文旅 研究 分析 报告"
            ar = await self._search(
                query=academic_query,
                search_depth="basic",
                max_results=3,
                include_images=True,
                include_domains=ACADEMIC_DOMAINS,
                language="zh",
            )
            for r in ar.get("results", []):
                all_results.append(
                    self._format_result(r, "academic", "tavily")
                )
            all_images.extend(_collect_images(ar))
        except Exception:
            pass

        # 7. Dedicated image search - find project promotional images and real photos
        try:
            image_queries = [
                f"{query} 实景图 宣传照 官方",
                f"{query} 景区照片 风景 风光",
            ]
            for iq in image_queries:
                img_resp = await self._search(
                    query=iq,
                    search_depth="basic",
                    max_results=4,
                    include_images=True,
                    language="zh",
                )
                all_images.extend(_collect_images(img_resp))
        except Exception:
            pass

        # Deduplicate images
        seen = set()
        deduped_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                deduped_images.append(img)

        # Filter images for relevance to the query
        deduped_images = self._filter_images(deduped_images, query)

        # Filter results for relevance to the query
        all_results = self._filter_relevant(all_results, query)

        return all_results, deduped_images

    def _filter_relevant(self, results: list[dict], query: str) -> list[dict]:
        """Strict filtering: only keep results directly about the specific project query.

        Key improvement: Instead of checking single-character tokens (which causes
        false matches like "贵州" matching any content about Guizhou), this method
        requires 3+ consecutive characters from the query to appear in content.
        """
        query_lower = query.lower().strip()

        # Build set of all 3+ consecutive-char segments of the query
        # e.g. "贵州阿云朵仓" → {"贵州阿","州阿云","阿云朵","云朵仓"}
        # Content must contain at least one of these to be relevant
        if len(query_lower) >= 3:
            query_segments = set(query_lower[i:i+3] for i in range(len(query_lower) - 2))
        else:
            query_segments = {query_lower}

        # Content mentioning these topics is NOT about tourism projects
        IRRELEVANT_TOPICS = [
            "反诈", "诈骗", "电信诈骗", "网络诈骗", "杀猪盘",
            "招聘", "求职", "征婚", "交友", "相亲",
            "彩票", "赌博", "色情", "网贷", "催收",
            "维权", "投诉", "车祸", "事故", "死亡", "疾病",
        ]

        # Quality domains - content from these is more reliable for tourism
        QUALITY_DOMAINS = [
            "gov.cn", "edu.cn", "ac.cn",
            "meadin", "ctrip", "mafengwo", "dianping",
            "qunar", "tuniu", "fliggy", "lvmama",
            "xiaohongshu", "douyin", "weixin", "weibo",
            "xinhuanet", "people.com.cn",
        ]

        filtered = []
        for r in results:
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "").lower()
            combined = (content + " " + title).lower()

            # 1. Skip very short content
            if len(content) < 60:
                continue

            # 2. Skip non-content pages
            if any(p in url for p in ["login", "register", "signup", "captcha", "password"]):
                continue

            # 3. Skip content about clearly irrelevant topics
            if any(pat in combined for pat in IRRELEVANT_TOPICS):
                continue

            # 4. CORE CHECK: A 3+ char continuous segment of query must appear in content
            # This prevents "贵州" alone from matching when query is "贵州阿云朵仓"
            has_segment = any(seg in combined for seg in query_segments)
            if not has_segment:
                continue

            # 5. Quality scoring
            score = 0
            if any(kw in combined for kw in RELEVANCE_KEYWORDS):
                score += 1
            if any(d in url for d in QUALITY_DOMAINS):
                score += 2
            if len(re.findall(r'\d+[万千亿]|\d{4}年|\d+[%％]', content)) >= 2:
                score += 1

            if score >= 1:
                filtered.append(r)

        # Fallback: if too aggressive, relax but still require segment match
        if not filtered and results:
            relaxed = []
            for r in results:
                content = r.get("content", "")
                title = r.get("title", "")
                combined = (content + " " + title).lower()
                if len(content) < 40:
                    continue
                if any(seg in combined for seg in query_segments):
                    relaxed.append(r)
            return relaxed if relaxed else results[:5]

        return filtered

    def _filter_images(self, images: list[str], query: str) -> list[str]:
        """Filter image URLs to keep only those likely relevant to the project."""
        # Known image hosting domains used by tourism/social platforms
        IMAGE_HOST_DOMAINS = [
            "qpic.cn", "alicdn.com", "meadin.com",
            "ctrip.com", "mafengwo.cn", "dianping.com",
            "qunar.com", "xiaohongshu.com", "douyin.com",
            "weibo.com", "xinhuanet.com", "people.com.cn",
        ]

        query_lower = query.lower().strip()
        # Build 3-char query segments for URL matching
        url_segments = set()
        for i in range(max(1, len(query_lower) - 2)):
            url_segments.add(query_lower[i:i+3])

        filtered = []
        for img_url in images:
            url_lower = img_url.lower()
            # Keep images from known quality domains
            if any(d in url_lower for d in IMAGE_HOST_DOMAINS):
                filtered.append(img_url)
                continue
            # Keep images whose URL contains a query-related segment
            if any(seg in url_lower for seg in url_segments):
                filtered.append(img_url)

        # Never return empty if we had images - return originals as fallback
        return filtered if filtered else images[:10]

    def _format_result(self, result: dict, source_type: str, platform: str) -> dict:
        return {
            "url": result.get("url", ""),
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "source_type": source_type,
            "platform": platform,
        }

    def parse_project_from_results(self, results: list[dict], keyword: str, additional_images: list[str] = None) -> Optional[dict]:
        """Parse search results to extract comprehensive project entity data."""
        all_text = " ".join(r.get("content", "") for r in results)
        all_text += " " + " ".join(r.get("title", "") for r in results)

        name = extract_project_name(all_text, keyword)
        if not name:
            name = keyword.strip()

        location = normalize_location(all_text)
        status = detect_construction_status(all_text)
        visitors = extract_visitor_count(all_text)
        revenue = extract_revenue(all_text)

        # Investors
        investor_pattern = re.findall(r'([一-鿿]{2,10}(?:集团|投资|地产|文旅|控股))', all_text)
        investors = list(set(investor_pattern))[:5]

        # Planning firms
        planner_pattern = re.findall(r'([一-鿿]{2,10}(?:设计|规划|建筑|工程|咨询)(?:院|所|公司|集团)?)', all_text)
        planners = list(set(planner_pattern))[:3]

        # Operation mode detection
        operation_mode = self._extract_operation_mode(all_text)
        cooperation_model = self._extract_cooperation_model(all_text)
        equity_structure = self._extract_equity_structure(all_text)
        operation_features = self._extract_operation_features(all_text)
        annual_visitor_analysis = self._extract_annual_visitor_analysis(all_text)

        # Collect all image URLs from search results + additional top-level images
        all_images = list(additional_images or [])
        for r in results:
            imgs = r.get("images", [])
            if imgs:
                all_images.extend(imgs)

        # Deduplicate images
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)

        summary_text = results[0].get("content", "")[:500] if results else ""

        return {
            "chinese_name": name,
            "location": location,
            "construction_status": status,
            "investors": investors,
            "planning_firms": planners,
            "visitor_count": visitors,
            "annual_revenue": revenue,
            "summary": summary_text,
            "operation_mode": operation_mode,
            "cooperation_model": cooperation_model,
            "equity_structure": equity_structure,
            "operation_features": operation_features,
            "annual_visitor_analysis": annual_visitor_analysis,
            "image_urls": unique_images[:20],
        }

    def _extract_operation_mode(self, text: str) -> str:
        """Extract operation mode information."""
        patterns = [
            r'(自营|委托运营|合资运营|合作运营|联合运营|自主运营)',
            r'(运营模式[：:]\s*[^。\n]+)',
            r'(由[^。\n]{1,50}(?:运营|管理|经营)[^。\n]{0,30})',
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(0).strip()
        return ""

    def _extract_cooperation_model(self, text: str) -> str:
        """Extract cooperation model information."""
        patterns = [
            r'(合作模式[：:]\s*[^。\n]+)',
            r'(PPP|BOT|TOT|ROT|DBFOT|EPC)',
            r'((?:政企|公私|政府与[^。\n]{0,20})合作)',
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(0).strip()
        return ""

    def _extract_equity_structure(self, text: str) -> str:
        """Extract equity structure information."""
        patterns = [
            r'(股权[：:]\s*[^。\n]+)',
            r'(持股[：:]\s*[^。\n]+)',
            r'(控股[^。\n]{0,50})',
            r'(占比[：:]\s*[^。\n]+)',
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(0).strip()
        return ""

    def _extract_operation_features(self, text: str) -> str:
        """Extract operation features."""
        patterns = [
            r'(运营特色[：:]\s*[^。\n]+)',
            r'(项目特色[：:]\s*[^。\n]+)',
            r'(业态[：:]\s*[^。\n]{0,100})',
            r'(主打[^。\n]{0,50})',
        ]
        features = []
        for p in patterns:
            match = re.search(p, text)
            if match:
                features.append(match.group(0).strip())
        return "；".join(features[:3])

    def _extract_annual_visitor_analysis(self, text: str) -> str:
        """Extract annual visitor analysis data."""
        patterns = [
            r'(全年[^。\n]{0,100}(?:游客|客流|接待)[^。\n]{0,100})',
            r'(月度[^。\n]{0,100}(?:游客|客流)[^。\n]{0,100})',
            r'(旺季[^。\n]{0,100}(?:游客|客流)[^。\n]{0,100})',
            r'(淡季[^。\n]{0,100}(?:游客|客流)[^。\n]{0,100})',
        ]
        analyses = []
        for p in patterns:
            match = re.search(p, text)
            if match:
                analyses.append(match.group(0).strip())
        return "；".join(analyses[:3])

    def _classify_source(self, url: str) -> str:
        if any(d in url for d in ["gov.cn", "mct.gov.cn"]):
            return "government"
        if any(d in url for d in ["meadin", "ctrip", "mafengwo", "dianping"]):
            return "industry"
        if any(d in url for d in SOCIAL_DOMAINS):
            return "social"
        if any(d in url for d in ["company", "corp"]):
            return "company"
        return "news"

    def _detect_social_platform(self, url: str) -> str:
        if "xiaohongshu" in url:
            return "xiaohongshu"
        if "douyin" in url:
            return "douyin"
        if "weixin" in url or "weixin.qq" in url:
            return "weixin"
        if "weibo" in url:
            return "weibo"
        return "tavily"

    async def _search(self, **kwargs) -> dict:
        """Run synchronous TavilyClient.search in a thread to avoid blocking the event loop."""
        return await asyncio.to_thread(self.client.search, **kwargs)

    def _mock_search(self, query: str) -> list[dict]:
        mock_data = {
            "成都融创文旅城": [
                {
                    "url": "https://www.cdrc.gov.cn/projects/sunac",
                    "title": "成都融创文旅城项目概况",
                    "content": "成都融创文旅城位于四川省成都市都江堰市，由融创中国投资建设，总投资约550亿元。项目涵盖融创乐园、融创雪世界、融创水世界、高端酒店群、国际会议中心等多种业态，于2020年正式开业运营。年均接待游客超过1000万人次，年旅游收入约50亿元。运营模式为自营+部分委托运营。",
                },
            ],
        }

        for key, results in mock_data.items():
            if key in query or query in key:
                return results

        return [
            {
                "url": "https://example.com/project",
                "title": f"{query} - 文旅项目相关信息",
                "content": f"关于{query}的文旅项目信息。该项目位于亚洲区域，是一个集旅游、文化、商业为一体的综合文旅项目。项目投资规模较大，目前正在运营中，为当地旅游经济带来显著效益。",
            },
        ]
