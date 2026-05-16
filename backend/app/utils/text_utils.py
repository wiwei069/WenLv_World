import re
from typing import Optional


def extract_project_name(text: str, keyword: str) -> Optional[str]:
    """Extract likely project name from text using heuristic patterns."""
    text = text.strip()
    # Common Chinese tourism project suffixes
    patterns = [
        r'([一-鿿]{2,10}(?:文旅|旅游|度假|景区|乐园|小镇|古城|街区|公园|山庄|生态园|产业园|古镇|文化城|度假区|风景区))',
        r'([一-鿿]{2,10}(?:城|园|谷|湾|岛|山|海))',
    ]
    candidates = []
    for p in patterns:
        found = re.findall(p, text)
        candidates.extend(found)

    # Prefer names containing the search keyword
    if keyword:
        for c in candidates:
            if keyword[:2] in c:
                return c
    return candidates[0] if candidates else None


def normalize_location(text: str) -> str:
    """Normalize Chinese location string to province+city format."""
    match = re.search(r'([一-鿿]{2,4}(?:省|市|自治区|特别行政区))([一-鿿]{2,4}(?:市|区|县|州))?', text)
    if match:
        return match.group(0)
    return text[:20]


def detect_construction_status(text: str) -> str:
    """Detect construction status from text."""
    if any(kw in text for kw in ['已开业', '已运营', '正式开园', '投入运营', '已开放', '正式开业', '开业运营', '开园']):
        return 'operating'
    if any(kw in text for kw in ['建设中', '在建', '施工中', '在建中', '动工']):
        return 'under_construction'
    if any(kw in text for kw in ['规划中', '已签约', '即将开工', '拟建', '筹备']):
        return 'planned'
    if any(kw in text for kw in ['已关闭', '已停业', '倒闭', '停业']):
        return 'closed'
    return 'unknown'


def extract_visitor_count(text: str) -> str:
    """Extract visitor count figure from text."""
    match = re.search(r'(\d+[.\d]*(?:万|亿)?(?:\s*)?人次)', text)
    return match.group(1) if match else ''


def extract_revenue(text: str) -> str:
    """Extract annual revenue figure from text."""
    match = re.search(r'(\d+[.\d]*(?:万|亿)?(?:\s*)?元)', text)
    return match.group(1) if match else ''


def truncate_text(text: str, max_length: int = 2000) -> str:
    """Truncate text to max_length, preserving whole sentences at the boundary."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_period = max(truncated.rfind('。'), truncated.rfind('.'), truncated.rfind('\n'))
    if last_period > max_length // 2:
        return truncated[:last_period + 1]
    return truncated
