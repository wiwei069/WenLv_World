import json
from typing import Optional
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings
from app.models import Project, Source, SocialMention


ANALYSIS_SYSTEM_PROMPT = """你是文旅大视界的AI分析专家，专注亚洲文旅项目深度分析。

## 核心原则 - 每个数据点必须标注来源
1. 基于收集到的真实网络数据进行分析
2. **每一条具体数据、数字、引文必须在括号内标注来源出处**，格式：`（来源：[平台/网站名]）`
3. 例如：年接待游客1000万人次（来源：携程口碑榜）、MBI指数548.07（来源：文旅部官网转载）
4. 对运营数据做同比、环比分析
5. 输出要包含具体数字和引用，拒绝空泛描述
6. 不确定的数据需标注"据信息推测"或"信息待核实"

## 输出格式 - 严格按以下结构

## 项目概况
- 项目名称、所在地、类型
- 投资方及投资规模
- 运营模式与合作模式（自营/委托运营/合资等）
- 股权结构与资产方信息（如有数据）
- 项目定位与核心理念

## 运营特色
- 核心业态与产品组合
- 运营模式特色
- 客群定位与市场营销
- 季节性运营策略

## 运营数据
- 年接待游客量及同比增长
- 年营业收入及构成
- 客单价与二次消费率
- 运营成本结构
- 入驻商户/品牌情况
- 全年游客量月度分布分析

## 社交媒体评价分析
- 总体口碑概况（正面/负面比例）
- 正面评价关键词与高频词汇
- 负面评价关键词与改进方向
- 典型用户评价摘录（标注平台来源）
- 网络热度趋势

## 行业地位与竞争力
- 在同类项目中的排名/定位
- 品牌传播力指数（如有数据）
- 主要OTA平台评分（携程、飞猪、马蜂窝等）
- 差异化竞争优势
- 潜在风险与挑战

## 综合研判与建议
- 项目总体评估（含置信度）
- 发展潜力判断
- 优化建议"""


class AnalysisService:
    def __init__(self):
        self.claude_client: Optional[AsyncAnthropic] = None
        self.deepseek_client: Optional[AsyncOpenAI] = None

        if settings.anthropic_api_key:
            self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        if settings.deepseek_api_key:
            self.deepseek_client = AsyncOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
            )

    def is_available(self) -> bool:
        return self.deepseek_client is not None

    def get_model_name(self) -> str:
        if self.deepseek_client:
            return settings.deepseek_model
        if self.claude_client:
            return settings.anthropic_model
        return "mock-analysis"

    async def generate_report(
        self,
        project: Project,
        sources: list[Source],
        social_mentions: list[SocialMention],
    ) -> dict:
        project_info = self._build_project_info(project)
        source_info = self._build_source_info(sources)
        social_info = self._build_social_info(social_mentions)

        user_prompt = f"""请对以下亚洲文旅项目进行全面深度分析：

## 项目基本信息
{project_info}

## 网络信息来源
以下是从各大网站（包括政府网站、新闻媒体、行业研究等渠道）收集到的项目相关信息：

{source_info}

## 社交媒体评价
以下是从社交媒体平台收集到的用户真实评价：

{social_info}

请基于以上信息，生成一份完整的项目深度分析报告。要求引用具体数据来源，进行量化分析。"""

        if self.deepseek_client:
            return await self._call_deepseek(user_prompt)
        elif self.claude_client:
            return await self._call_claude(user_prompt)
        else:
            return self._mock_report(project_info, source_info, social_info)

    async def _call_deepseek(self, user_prompt: str) -> dict:
        response = await self.deepseek_client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=settings.analysis_max_tokens,
            temperature=0.7,
        )

        analysis_text = response.choices[0].message.content or ""
        summary = self._extract_summary(analysis_text)
        key_findings = self._extract_key_findings(analysis_text)
        recommendations = self._extract_recommendations(analysis_text)

        return {
            "summary": summary,
            "analysis": analysis_text,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "confidence_score": 0.75,
            "model_version": f"deepseek-{settings.deepseek_model}",
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        }

    async def _call_claude(self, user_prompt: str) -> dict:
        response = await self.claude_client.messages.create(
            model=settings.anthropic_model,
            max_tokens=settings.analysis_max_tokens,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        analysis_text = response.content[0].text
        summary = self._extract_summary(analysis_text)
        key_findings = self._extract_key_findings(analysis_text)
        recommendations = self._extract_recommendations(analysis_text)

        return {
            "summary": summary,
            "analysis": analysis_text,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "confidence_score": 0.75,
            "model_version": settings.anthropic_model,
            "tokens_used": response.usage.output_tokens if response.usage else 0,
        }

    def _build_project_info(self, project: Project) -> str:
        lines = [
            f"- 项目名称：{project.chinese_name}",
            f"- 所在地：{project.location or '信息收集中'}",
            f"- 项目类型：{project.project_type or '信息收集中'}",
            f"- 建设状态：{project.construction_status}",
        ]
        if project.investors and project.investors != "[]":
            inv = json.loads(project.investors)
            lines.append(f"- 投资方：{'、'.join(inv)}")
        if project.planning_firms and project.planning_firms != "[]":
            pf = json.loads(project.planning_firms)
            lines.append(f"- 规划设计：{'、'.join(pf)}")
        if project.visitor_count:
            lines.append(f"- 年接待游客：{project.visitor_count}")
        if project.annual_revenue:
            lines.append(f"- 年收入：{project.annual_revenue}")
        if project.operation_mode:
            lines.append(f"- 运营模式：{project.operation_mode}")
        if project.cooperation_model:
            lines.append(f"- 合作模式：{project.cooperation_model}")
        if project.equity_structure:
            lines.append(f"- 股权结构：{project.equity_structure}")
        if project.operation_features:
            lines.append(f"- 运营特色：{project.operation_features}")
        if project.annual_visitor_analysis:
            lines.append(f"- 全年游客分析：{project.annual_visitor_analysis}")
        if project.summary:
            lines.append(f"- 简介：{project.summary[:300]}")
        return "\n".join(lines)

    def _build_source_info(self, sources: list[Source]) -> str:
        if not sources:
            return "暂无网络来源数据。"
        lines = []
        for i, s in enumerate(sources, 1):
            title = s.title or "无标题"
            snippet = (s.snippet or s.content or "")[:300]
            source_tag = ""
            if "mct.gov.cn" in s.url:
                source_tag = "【文化和旅游部官网】"
            elif "meadin" in s.url:
                source_tag = "【迈点研究院】"
            elif "ctrip" in s.url:
                source_tag = "【携程】"
            elif "qunar" in s.url:
                source_tag = "【去哪儿】"
            elif "mafengwo" in s.url:
                source_tag = "【马蜂窝】"
            elif "dianping" in s.url:
                source_tag = "【大众点评】"
            elif "tuniu" in s.url:
                source_tag = "【途牛】"
            elif "lvmama" in s.url:
                source_tag = "【驴妈妈】"
            elif "xiaohongshu" in s.url:
                source_tag = "【小红书】"
            elif "douyin" in s.url:
                source_tag = "【抖音】"
            elif "weixin" in s.url:
                source_tag = "【微信】"
            elif "weibo" in s.url:
                source_tag = "【微博】"
            elif "gov.cn" in s.url:
                source_tag = "【政府网站】"
            elif "edu.cn" in s.url or "ac.cn" in s.url:
                source_tag = "【学术机构】"
            elif "xinhuanet" in s.url or "people.com" in s.url:
                source_tag = "【官方媒体】"
            elif "zhihu" in s.url:
                source_tag = "【知乎】"
            lines.append(f"来源{i}：{source_tag}{title}\nURL：{s.url}\n摘要：{snippet}\n")
        return "\n".join(lines)

    def _build_social_info(self, mentions: list[SocialMention]) -> str:
        if not mentions:
            return "暂无社交媒体评价数据。"
        lines = []
        for m in mentions:
            lines.append(
                f"[{m.platform}] {m.author or '匿名用户'}：{m.content[:200]} "
                f"(情感:{m.sentiment:.1f} 赞:{m.likes_count} 评论:{m.comments_count})"
            )
        return "\n".join(lines)

    def _extract_summary(self, text: str) -> str:
        paragraphs = text.split("\n\n")
        for p in paragraphs:
            p = p.strip()
            if p and len(p) > 20:
                return p[:300]
        return text[:300]

    def _extract_key_findings(self, text: str) -> list[str]:
        findings = []
        in_section = False
        for line in text.split("\n"):
            if "综合研判" in line or "关键发现" in line or "竞争力" in line:
                in_section = True
                continue
            if in_section and line.startswith("##"):
                break
            if in_section and line.strip().startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")):
                findings.append(line.strip().lstrip("- *123456789.").strip())
        return findings or ["分析报告已生成，请查看完整内容获取关键发现。"]

    def _extract_recommendations(self, text: str) -> list[str]:
        recommendations = []
        in_section = False
        for line in text.split("\n"):
            if "建议" in line or "优化建议" in line:
                in_section = True
                continue
            if in_section and line.startswith("##"):
                break
            if in_section and line.strip().startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")):
                recommendations.append(line.strip().lstrip("- *123456789.").strip())
        return recommendations or ["请查看完整分析报告获取详细建议。"]

    def _mock_report(self, project_info: str, source_info: str, social_info: str) -> dict:
        report = f"""## 项目概况

基于收集到的信息，对项目进行了初步分析。

{project_info}

## 网络来源分析

已收集到相关网络信息来源，涵盖政府网站、新闻媒体、行业研究等多个渠道。

## 社交媒体评价

社交媒体平台上有关于该项目的讨论，正面评价主要集中在项目规模和业态丰富度上，负面评价主要涉及价格和交通便利性等方面。

## 综合研判与建议

该项目作为亚洲文旅项目具有一定的市场影响力。建议持续关注其运营数据和用户反馈，进行更深入的跟踪分析。

---
*注：此为自动生成的初步分析报告。如需更深入的AI深度分析，请配置 DeepSeek API 密钥。*
"""
        return {
            "summary": "项目初步分析完成。已收集项目基本信息、网络来源和社交媒体评价数据，可供进一步研判。",
            "analysis": report,
            "key_findings": ["项目基本信息已收集完成", "网络来源数据已整合", "社交媒体评价已汇总"],
            "recommendations": ["配置 DeepSeek API 密钥以获得AI深度分析", "补充更多来源数据进行交叉验证", "持续跟踪项目运营动态"],
            "confidence_score": 0.5,
            "model_version": "mock-analysis",
            "tokens_used": 0,
        }
