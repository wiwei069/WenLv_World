import os
import re
import urllib.request
from pathlib import Path
from datetime import datetime
from fpdf import FPDF

_FONT_PATH = os.environ.get("PDF_FONT_PATH", "")

# A4 usable width with default 10mm margins
_PAGE_W = 190


def _find_font() -> str:
    """Find a usable CJK font on the system.

    Checks env var first, then common system paths, and finally downloads
    NotoSansSC from Google Fonts if no CJK font is found.
    """
    # 1. Check env var override
    if _FONT_PATH and os.path.exists(_FONT_PATH):
        return _FONT_PATH

    # 2. Check common system paths (Windows / Linux / macOS)
    candidates = [
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "data/fonts/NotoSansSC-Regular.ttf",
        "./data/fonts/NotoSansSC-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansSC-Regular.otf",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p

    # 3. Download Noto Sans SC (regular weight) from Google Fonts CDN
    font_dir = Path(os.environ.get("DATA_DIR", "./data")) / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    local_path = str(font_dir / "NotoSansSC-Regular.ttf")

    if not os.path.exists(local_path):
        url = (
            "https://fonts.gstatic.com/s/notosanssc/v40/"
            "k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYw.ttf"
        )
        try:
            urllib.request.urlretrieve(url, local_path)
        except Exception:
            pass  # will fall through to raise below

    if os.path.exists(local_path):
        return local_path

    raise RuntimeError(
        "No CJK font found. Set PDF_FONT_PATH env var to a .ttf/.otf/.ttc "
        "file that supports Chinese characters, or install fonts-noto-cjk."
    )


def _strip_md(text: str) -> str:
    """Light markdown stripping for clean text rendering."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"^###?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^-\s*", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"^(\d+)\.\s", r"\1. ", text, flags=re.MULTILINE)
    return text


def _multi_cell(pdf: FPDF, text: str, **kwargs):
    """Wrapper around multi_cell that resets x position to left margin."""
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(w=_PAGE_W, text=text, **kwargs)


def generate_report_pdf(
    project_name: str,
    project_info: dict,
    analysis_text: str,
    recommendations: list[str],
    model_version: str,
    confidence_score: float,
    created_at: datetime | None,
    sources: list[dict],
) -> bytes:
    """Generate a PDF report for a project analysis."""
    font_path = _find_font()
    pdf = FPDF()
    pdf.add_font("CJK", "", font_path)

    # === Page 1: Title & Project Info ===
    pdf.add_page()
    pdf.set_font("CJK", "", 22)
    _multi_cell(pdf, f"{project_name}")
    pdf.set_font("CJK", "", 14)
    _multi_cell(pdf, "文旅大视界 分析报告")
    pdf.ln(4)
    pdf.set_font("CJK", "", 9)
    pdf.set_x(pdf.l_margin)
    pdf.cell(text=f"报告生成时间: {created_at.strftime('%Y-%m-%d %H:%M') if created_at else 'N/A'}")
    pdf.ln(6)

    # Gold separator line
    pdf.set_draw_color(212, 162, 78)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + _PAGE_W, pdf.get_y())
    pdf.ln(6)

    # Project info section
    pdf.set_font("CJK", "", 12)
    pdf.set_x(pdf.l_margin)
    pdf.cell(text="项目信息")
    pdf.ln(8)

    pdf.set_font("CJK", "", 10)
    info_fields = [
        ("所在地", project_info.get("location", "")),
        ("项目类型", project_info.get("project_type", "")),
        ("建设状态", project_info.get("construction_status", "")),
        ("年接待游客", project_info.get("visitor_count", "")),
        ("年收入", project_info.get("annual_revenue", "")),
        ("运营模式", project_info.get("operation_mode", "")),
        ("投资方", project_info.get("investors", "")),
    ]
    for label, value in info_fields:
        if value:
            pdf.set_x(pdf.l_margin)
            display = value if isinstance(value, str) else "、".join(value)
            pdf.cell(text=f"{label}: {display}")
            pdf.ln(6)

    # Light separator
    pdf.ln(2)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + _PAGE_W, pdf.get_y())
    pdf.ln(4)

    # Confidence and model info
    pdf.set_font("CJK", "", 9)
    pdf.set_x(pdf.l_margin)
    pdf.cell(text=f"模型: {model_version}  |  置信度: {confidence_score * 100:.0f}%")
    pdf.ln(8)

    # === Analysis Report ===
    if analysis_text:
        pdf.add_page()
        pdf.set_font("CJK", "", 16)
        pdf.set_x(pdf.l_margin)
        pdf.cell(text="AI 分析报告")
        pdf.ln(12)

        pdf.set_font("CJK", "", 10)
        cleaned = _strip_md(analysis_text)
        paragraphs = cleaned.split("\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                pdf.ln(3)
                continue
            if len(para) < 60 and (para.endswith("：") or para.endswith(":") or para.isupper()):
                pdf.set_font("CJK", "", 11)
                _multi_cell(pdf, para)
                pdf.set_font("CJK", "", 10)
                pdf.ln(1)
            else:
                _multi_cell(pdf, para)
                pdf.ln(2)

    # === Source Links ===
    if sources:
        pdf.add_page()
        pdf.set_font("CJK", "", 14)
        pdf.set_x(pdf.l_margin)
        pdf.cell(text="来源链接")
        pdf.ln(10)

        pdf.set_font("CJK", "", 9)
        for i, src in enumerate(sources, 1):
            title = src.get("title", "") or "来源"
            url = src.get("url", "")
            _multi_cell(pdf, f"{i}. {title}")
            if url:
                pdf.set_text_color(100, 100, 100)
                _multi_cell(pdf, f"   {url}")
                pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

    result = pdf.output(dest="S")
    if isinstance(result, (bytes, bytearray)):
        return bytes(result)
    return result.encode("latin-1")
