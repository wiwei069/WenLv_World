import asyncio
import re
from typing import Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page

from app.config import settings
from app.utils.rate_limiter import TokenBucket, RATE_LIMITERS


# Lazily initialize rate limiters
def _get_limiter(platform: str, rate: int) -> TokenBucket:
    if platform not in RATE_LIMITERS:
        RATE_LIMITERS[platform] = TokenBucket(rate_per_minute=rate, burst=1)
    return RATE_LIMITERS[platform]


class SocialScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self._playwright = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        return self

    async def __aexit__(self, *args):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def new_context(self):
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        return context

    async def search_xiaohongshu(self, keyword: str, max_results: int = 5) -> list[dict]:
        """Search Xiaohongshu for project mentions."""
        limiter = _get_limiter("xiaohongshu", settings.rate_limit_xiaohongshu)
        await limiter.acquire()

        results = []
        context = await self.new_context()
        page = await context.new_page()

        try:
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}%20旅游"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=settings.scrape_timeout_seconds * 1000)
            await asyncio.sleep(3)

            content = await page.content()
            soup = BeautifulSoup(content, "lxml")

            # Try to extract visible post snippets
            text = soup.get_text(separator="\n", strip=True)
            lines = [l for l in text.split("\n") if len(l) > 20 and re.search(r'[一-鿿]', l)]

            for line in lines[:max_results]:
                results.append({
                    "platform": "小红书",
                    "author": "",
                    "content": line[:500],
                    "sentiment": self._estimate_sentiment(line),
                    "likes_count": 0,
                    "comments_count": 0,
                })

        except Exception as e:
            # Non-fatal: mark as failed and return empty results
            pass
        finally:
            await page.close()
            await context.close()

        return results

    async def search_douyin(self, keyword: str, max_results: int = 5) -> list[dict]:
        """Search Douyin for project mentions."""
        limiter = _get_limiter("douyin", settings.rate_limit_douyin)
        await limiter.acquire()

        results = []
        context = await self.new_context()
        page = await context.new_page()

        try:
            search_url = f"https://www.douyin.com/search/{keyword}%20旅游"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=settings.scrape_timeout_seconds * 1000)
            await asyncio.sleep(3)

            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l for l in text.split("\n") if len(l) > 20 and re.search(r'[一-鿿]', l)]

            for line in lines[:max_results]:
                results.append({
                    "platform": "抖音",
                    "author": "",
                    "content": line[:500],
                    "sentiment": self._estimate_sentiment(line),
                    "likes_count": 0,
                    "comments_count": 0,
                })

        except Exception as e:
            pass
        finally:
            await page.close()
            await context.close()

        return results

    async def search_weixin(self, keyword: str, max_results: int = 5) -> list[dict]:
        """Search WeChat public accounts via Sogou search."""
        limiter = _get_limiter("weixin", settings.rate_limit_weixin)
        await limiter.acquire()

        results = []
        import httpx
        try:
            search_url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}%20旅游"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                resp = await client.get(search_url, headers=headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    items = soup.select(".news-box .news-list li")
                    for item in items[:max_results]:
                        title_el = item.select_one("h3 a")
                        desc_el = item.select_one(".txt-info")
                        title = title_el.get_text(strip=True) if title_el else ""
                        desc = desc_el.get_text(strip=True) if desc_el else ""
                        content = f"{title} {desc}"
                        if content and re.search(r'[一-鿿]', content):
                            results.append({
                                "platform": "微信",
                                "author": "",
                                "content": content[:500],
                                "sentiment": self._estimate_sentiment(content),
                                "likes_count": 0,
                                "comments_count": 0,
                            })

        except Exception:
            pass

        return results

    async def search_all(self, project_name: str, keyword: str) -> list[dict]:
        """Search all social platforms concurrently."""
        tasks = [
            self.search_xiaohongshu(keyword),
            self.search_douyin(keyword),
            self.search_weixin(keyword),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_mentions = []
        for r in results:
            if isinstance(r, list):
                all_mentions.extend(r)
        return all_mentions

    def _estimate_sentiment(self, text: str) -> float:
        """Simple keyword-based sentiment estimation (-1.0 to 1.0)."""
        positive_words = ["好评", "推荐", "值得", "不错", "喜欢", "很棒", "好玩", "精彩", "满意", "推荐"]
        negative_words = ["差评", "失望", "不好", "太差", "无聊", "坑", "不值", "后悔", "糟糕", "骗人"]

        score = 0.0
        for w in positive_words:
            if w in text:
                score += 0.2
        for w in negative_words:
            if w in text:
                score -= 0.2

        return max(-1.0, min(1.0, score))
