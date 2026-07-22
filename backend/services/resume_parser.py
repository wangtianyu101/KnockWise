"""Resume parser — PDF text extraction + LLM structured extraction.

Two-step pipeline (each step is independently testable):
  1. extract_text_from_pdf(bytes) -> (text, page_count)
     - Uses pypdf. Empty result + multi-page = likely scanned PDF.
  2. extract_profile_from_text(text) -> dict
     - Calls DeepSeek V3 with a constrained JSON prompt.
     - Returns tech_stack / years_of_exp / current_level / skill_map.

The parsed JSON is NOT auto-saved to Profile — it goes back to the client
for review. The user clicks "save" only after editing. This keeps LLM
hallucinations from silently polluting the profile.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

logger = logging.getLogger("knockwise.resume_parser")

# Canonical tech list. LLM is constrained to pick from this list when
# possible; new terms it surfaces fall into "other" and the user can
# promote them. Same list is hard-coded in frontend ProfileChat.
KNOWN_TECHS = [
    "LangChain", "LangGraph", "RAG", "MCP",
    "Python", "Java", "Spring Boot", "Go", "TypeScript", "JavaScript",
    "React", "Vue", "Next.js",
    "K8s", "Docker", "AWS", "GCP", "Azure",
    "MySQL", "PostgreSQL", "Redis", "MongoDB", "Elasticsearch",
    "Kafka", "RabbitMQ",
    "LLM", "Agent", "Prompt Engineering", "RAGAS",
]

# Scanned-PDF heuristic: if pypdf returns < this many non-whitespace chars,
# the file is probably image-only and needs OCR.
SCAN_THRESHOLD_CHARS = 100


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, int]:
    """Extract plain text from a PDF byte blob.

    Returns (text, page_count). Text may be empty for scanned PDFs.
    """
    import io
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    chunks: list[str] = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception as e:
            logger.warning(f"page extract_text failed: {e}")
            chunks.append("")
    return "\n".join(chunks), len(reader.pages)


def render_pdf_pages_to_png(pdf_bytes: bytes, scale: float = 2.0) -> list[bytes]:
    """Render each PDF page to a PNG byte blob. Used as input for OCR.

    Uses pypdfium2 (faster than pdf2image, no system poppler needed).
    """
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_bytes)
    pngs: list[bytes] = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        pngs.append(buf.getvalue())
    return pngs


async def ocr_png_with_dashscope(png_bytes: bytes) -> str:
    """Run Alibaba DashScope qwen-vl-ocr on a single PNG.

    Returns extracted text. Empty string on any failure (logged).
    Falls back to local file path since the dashscope SDK accepts
    file:// style paths for multimodal inputs.
    """
    import os
    import tempfile
    from core.config import settings

    try:
        import dashscope
        from dashscope import MultiModalConversation

        dashscope.api_key = settings.dashscope_api_key
        if not dashscope.api_key:
            logger.warning("dashscope_api_key not set, OCR unavailable")
            return ""

        # DashScope SDK accepts file paths via the file:// scheme (and
        # also a local absolute path directly). Save the PNG to a temp
        # file and pass it as a file:// URL.
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_bytes)
            tmp_path = f.name

        try:
            response = MultiModalConversation.call(
                model="qwen-vl-ocr",
                messages=[{
                    "role": "user",
                    "content": [{"image": f"file://{tmp_path}"}],
                }],
            )

            if response.output and response.output.choices:
                msg = response.output.choices[0].message
                if msg and msg.content:
                    # OCR returns either a list of content parts or a
                    # string. Each part may be {"text": "..."} or have
                    # a nested structure for tables — we just collect
                    # any "text" fields we can find.
                    parts = msg.content if isinstance(msg.content, list) else [msg.content]
                    chunks: list[str] = []
                    for part in parts:
                        if isinstance(part, dict):
                            if "text" in part and part["text"]:
                                chunks.append(str(part["text"]))
                        elif isinstance(part, str):
                            chunks.append(part)
                    if chunks:
                        return "\n".join(chunks).strip()
            logger.warning(f"qwen-vl-ocr returned no text: {response}")
            return ""
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except ImportError:
        logger.warning("dashscope not installed, OCR unavailable")
        return ""
    except Exception as e:
        logger.error(f"OCR call failed: {type(e).__name__}: {e}")
        return ""


async def extract_text_from_pdf_via_ocr(pdf_bytes: bytes) -> tuple[str, int]:
    """Render + OCR fallback path for scanned/image-only PDFs.

    Returns (text, page_count). Empty text means OCR failed too —
    caller should fall back to manual fill-in.
    """
    try:
        pngs = render_pdf_pages_to_png(pdf_bytes)
    except Exception as e:
        logger.error(f"PDF render failed: {e}")
        # Still try to count pages via pypdf so we know what we missed
        _, page_count = extract_text_from_pdf(pdf_bytes)
        return "", page_count

    page_count = len(pngs)
    chunks: list[str] = []
    for i, png in enumerate(pngs):
        text = await ocr_png_with_dashscope(png)
        if text:
            chunks.append(f"[第 {i+1} 页]\n{text}")
        # Skip empty pages silently — could be a blank page or OCR failure

    return "\n\n".join(chunks), page_count


def is_likely_scanned(text: str, page_count: int) -> bool:
    """Heuristic: >1 page but <threshold non-whitespace chars = scanned."""
    non_ws = len(re.sub(r"\s+", "", text))
    return page_count > 1 and non_ws < SCAN_THRESHOLD_CHARS


def _make_llm():
    """Build the LLM client. Same wiring as evaluate_agent."""
    from langchain_openai import ChatOpenAI
    from core.config import settings
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.1,
    )


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first JSON object out of an LLM response.

    Models sometimes wrap the JSON in prose or markdown fences. We try the
    raw parse first, then progressively strip more wrappers.
    """
    text = text.strip()

    # Strip markdown fences if present
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)

    # Find the first balanced { ... } block
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return None
    return None


async def extract_profile_from_text(resume_text: str) -> dict:
    """Ask the LLM to extract structured profile fields.

    Returns a dict with: tech_stack, years_of_exp, current_level,
    skill_map, suggested_target_companies. Skill_map keys are
    intersected with KNOWN_TECHS to suppress hallucinated tech names —
    unknown ones land in tech_stack as-is (user can remove in review).
    """
    # Truncate to keep the prompt sane. 8000 chars covers a 3-page resume.
    truncated = resume_text[:8000]

    tech_list_str = ", ".join(KNOWN_TECHS)
    prompt = f"""你是一个简历解析助手。请从以下中文简历文本中提取结构化信息。

严格要求:
1. 只基于简历实际提到的内容判断，不要外推或编造简历中没写的技术。
2. tech_stack 优先从已知列表中匹配；如果简历提到了列表外的新技术，按原文保留。
3. years_of_exp 是所有工作年限的总和（多份工作累加；实习也算但权重低）。
4. current_level 根据年限和简历描述深度判断: junior (0-2年) / mid (2-5年) / senior (5年+)。
5. skill_map 是 {{技术: 熟练度}}，熟练度 1-5:
   1=听过/学过, 2=项目用过一次, 3=常用, 4=深入理解/能讲原理, 5=精通/主导过生产项目
   仅包含简历中能判断出熟练度的技术，不要给每项都给 5。
6. suggested_target_companies 是 0-3 个简历水平适合投递的公司类型，如"字节跳动"/"小红书"/"美团"。
   不要编造，写"未知"也可以。

已知技术列表: {tech_list_str}

简历文本:
{truncated}

严格按以下 JSON 格式输出，不要任何解释、不要 markdown 包裹:
{{
  "tech_stack": ["Python", "LangChain", ...],
  "years_of_exp": 5,
  "current_level": "senior",
  "skill_map": {{"Python": 4, "LangChain": 3, ...}},
  "suggested_target_companies": ["字节跳动", "美团"],
  "summary": "候选人画像 (200字以内, 第三人称, 中文): 5年后端工程师, 主导过千万级消息推送系统, 熟悉LangChain生态。技术深度集中在Python/分布式, 工程能力扎实, 适合中大型互联网公司高级岗。"
}}
"""

    llm = _make_llm()
    from langchain_core.messages import HumanMessage
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    raw = resp.content if hasattr(resp, "content") else str(resp)
    logger.info(f"resume LLM raw response (first 200): {raw[:200]}")

    parsed = _extract_json(raw)
    if parsed is None:
        logger.warning(f"could not parse JSON from LLM response: {raw[:500]}")
        return {
            "tech_stack": [],
            "years_of_exp": 0,
            "current_level": "mid",
            "skill_map": {},
            "suggested_target_companies": [],
            "_raw_response": raw[:500],
        }

    # Normalize fields
    tech_stack = parsed.get("tech_stack") or []
    if not isinstance(tech_stack, list):
        tech_stack = []
    tech_stack = [str(t).strip() for t in tech_stack if str(t).strip()]

    skill_map = parsed.get("skill_map") or {}
    if not isinstance(skill_map, dict):
        skill_map = {}

    # Clamp skill_map values to 1-5
    cleaned_skill_map: dict[str, int] = {}
    for tech, level in skill_map.items():
        try:
            lvl = max(1, min(5, int(level)))
        except (TypeError, ValueError):
            continue
        cleaned_skill_map[str(tech).strip()] = lvl

    years = parsed.get("years_of_exp", 0)
    try:
        years = int(years)
    except (TypeError, ValueError):
        years = 0
    years = max(0, min(50, years))

    level = parsed.get("current_level", "mid")
    if level not in ("junior", "mid", "senior"):
        level = "mid"

    companies = parsed.get("suggested_target_companies") or []
    if not isinstance(companies, list):
        companies = []
    companies = [str(c).strip() for c in companies if str(c).strip()][:3]

    # D2 · Phase 1d: LLM 真摘要 (200字以内候选人画像)
    summary = (parsed.get("summary") or "").strip()
    if len(summary) > 250:  # 留 buffer
        summary = summary[:250]
    if not summary:
        # 兜底: 从 extracted fields 自动拼一段, 避免 LLM 没返回 summary 时字段空
        summary = (
            f"{years}年{level}工程师, 技术栈: {', '.join(tech_stack[:5]) or '未识别'}。"
            f"建议目标公司: {', '.join(companies) or '未识别'}。"
        )[:250]

    return {
        "tech_stack": tech_stack,
        "years_of_exp": years,
        "current_level": level,
        "skill_map": cleaned_skill_map,
        "suggested_target_companies": companies,
        "summary": summary,
    }


def save_pdf_to_disk(pdf_bytes: bytes, user_id: str, upload_dir: str) -> tuple[str, str]:
    """Save PDF to disk under uploads/{user_id}/. Returns (file_path, file_name).

    Uses content-hash filename to avoid collisions and to deduplicate
    identical uploads. Old files are left in place for audit; a separate
    cleanup job (out of scope) can prune them.
    """
    import hashlib
    import os
    user_dir = os.path.join(upload_dir, user_id)
    os.makedirs(user_dir, exist_ok=True)
    digest = hashlib.sha256(pdf_bytes).hexdigest()[:16]
    file_name = f"resume_{digest}.pdf"
    file_path = os.path.join(user_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
    return file_path, file_name