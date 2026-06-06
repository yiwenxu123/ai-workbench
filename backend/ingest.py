"""
AI 内容提取服务
通过 LLM 将网页文章/粘贴文本自动解析为结构化的案例、知识库或模板条目，并追加到对应 JSON 文件。
支持智能去重对比：本地候选匹配 + LLM 质量对比。
"""

import json
import re
import httpx
import ipaddress
import socket
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from json_store import load_json_list, write_json_atomic

DATA_DIR = Path(__file__).parent / "data"

FILE_MAP = {
    "cases": "cases.json",
    "knowledge": "knowledge.json",
    "templates": "templates.json",
}

ALLOWED_FETCH_SCHEMES = {"http", "https"}
ALLOWED_CONTENT_TYPES = {"text/html", "text/plain", "application/xhtml+xml"}
MAX_FETCH_BYTES = 2_000_000

# ── 各类数据的 JSON Schema（作为 prompt 的范例） ────────────────────────

CASE_SCHEMA_EXAMPLE = """{
  "id": "short-kebab-id",
  "name": "案例标题",
  "category": "product|ecommerce|brand|drama|animation|film|social",
  "description": "一句话描述",
  "prompt": "完整的提示词",
  "negativePrompt": "负面提示词（可选）",
  "model": "推荐模型名称（如 可灵 V1、Seedance 2.0）",
  "parameters": { "size": "1080p", "duration": "5秒", "style": "风格描述" },
  "tips": ["技巧1", "技巧2"],
  "tags": ["标签1", "标签2"],
  "author": "原作者（可选）"
}"""

KNOWLEDGE_SCHEMA_EXAMPLE = """{
  "id": "term-kebab-id",
  "name": "术语名称",
  "nameEn": "English Name",
  "category": "style|lighting|composition|color|material|mood|technique",
  "description": "详细解释",
  "usage": "使用建议",
  "examples": ["用法示例1", "用法示例2"],
  "relatedTerms": ["相关术语1"],
  "tips": "使用技巧"
}"""

TEMPLATE_SCHEMA_EXAMPLE = """{
  "id": "template-kebab-id",
  "name": "模板名称",
  "category": "product|brand|education|culture|social|portrait",
  "description": "模板描述",
  "prompt": "提示词模板，可使用 {变量名} 占位符",
  "negativePrompt": "负面提示词（可选）",
  "fields": [
    {
      "key": "变量名",
      "label": "显示标签",
      "placeholder": "输入提示",
      "required": true,
      "options": ["选项1", "选项2"]
    }
  ],
  "tips": ["使用提示1"]
}"""


# ═══════════════════════════════════════════════════════════════════════
#  1. 提取
# ═══════════════════════════════════════════════════════════════════════

def _build_system_prompt(target_type: str) -> str:
    """根据目标类型构建 system prompt。"""
    schema_map = {
        "cases": ("优秀案例（包含完整提示词、参数、技巧）", CASE_SCHEMA_EXAMPLE),
        "knowledge": ("AI绘图/视频术语知识条目（包含解释、用法、示例）", KNOWLEDGE_SCHEMA_EXAMPLE),
        "templates": ("提示词模板（包含可填充变量的提示词模板）", TEMPLATE_SCHEMA_EXAMPLE),
    }
    desc, schema = schema_map.get(target_type, schema_map["cases"])

    return f"""你是一位专业的 AI 绘图/视频方法论整理助手。
你的任务：从用户提供的文章或文本中，提取出有价值的内容并整理为**{desc}**。

输出要求：
1. 直接输出一个 JSON 数组，每个元素符合以下结构（可提取多条）：
{schema}
2. id 必须是全小写英文、用短横线分隔的唯一标识，不要用中文。
3. 从文章中尽量提取**所有**可用的案例/知识/模板，不要遗漏。
4. 如果原文有提示词(prompt)，务必完整保留，不要截断或概括。
5. 只输出合法 JSON 数组，不要输出任何多余文字、markdown 代码块标记或解释。"""


def _build_user_prompt(content: str, source_url: Optional[str] = None) -> str:
    """构建用户消息。"""
    parts = []
    if source_url:
        parts.append(f"来源网址：{source_url}")
    parts.append(f"请从以下内容中提取所有可用条目：\n\n{content[:15000]}")
    return "\n".join(parts)


async def call_llm(
    content: str,
    target_type: str,
    llm_endpoint: str,
    llm_api_key: str,
    llm_model: str,
    source_url: Optional[str] = None,
) -> list[dict]:
    """调用 LLM 提取结构化数据。"""
    system_prompt = _build_system_prompt(target_type)
    user_prompt = _build_user_prompt(content, source_url)

    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 8000,
    }

    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(llm_endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()

    raw_text = result["choices"][0]["message"]["content"]
    return _parse_json_from_text(raw_text)


def _parse_json_from_text(text: str) -> list[dict]:
    """从 LLM 回复中健壮地解析 JSON 数组。"""
    text = text.strip()

    # 去掉 markdown 代码块标记
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"LLM 返回内容无法解析为 JSON:\n{text[:500]}")


# ═══════════════════════════════════════════════════════════════════════
#  2. 智能去重对比
# ═══════════════════════════════════════════════════════════════════════

def _load_existing(target_type: str) -> list[dict]:
    """加载指定类型的现有数据。"""
    filename = FILE_MAP.get(target_type)
    if not filename:
        return []
    return load_json_list(DATA_DIR / filename)


def _text_similarity(a: str, b: str) -> float:
    """简易 Jaccard 相似度（基于字符 bigram）。"""
    if not a or not b:
        return 0.0
    a_lower, b_lower = a.lower(), b.lower()
    if a_lower == b_lower:
        return 1.0
    # 子串包含
    if a_lower in b_lower or b_lower in a_lower:
        return 0.8
    # bigram Jaccard
    def bigrams(s):
        return set(s[i:i+2] for i in range(len(s) - 1))
    a_bg, b_bg = bigrams(a_lower), bigrams(b_lower)
    if not a_bg or not b_bg:
        return 0.0
    inter = len(a_bg & b_bg)
    union = len(a_bg | b_bg)
    return inter / union if union else 0.0


def _tags_overlap(tags_a: list, tags_b: list) -> float:
    """标签重叠率。"""
    if not tags_a or not tags_b:
        return 0.0
    set_a = set(str(t).lower() for t in tags_a)
    set_b = set(str(t).lower() for t in tags_b)
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


def find_candidates(new_item: dict, existing: list[dict], threshold: float = 0.35) -> list[dict]:
    """
    为一个新条目在现有数据中找出可能重复的候选项。
    综合 id、name、tags、description 多维匹配。
    """
    new_id = new_item.get("id", "")
    new_name = new_item.get("name", "")
    new_tags = new_item.get("tags", [])
    new_desc = new_item.get("description", "")
    new_prompt = new_item.get("prompt", "")

    candidates = []
    for ex in existing:
        ex_id = ex.get("id", "")
        ex_name = ex.get("name", "")
        ex_tags = ex.get("tags", [])
        ex_desc = ex.get("description", "")
        ex_prompt = ex.get("prompt", "")

        # 1) id 完全匹配 → 极高概率重复
        if new_id and ex_id and new_id == ex_id:
            candidates.append({"existing": ex, "score": 1.0, "match_reason": "ID 完全相同"})
            continue

        # 2) 计算多维相似度
        name_sim = _text_similarity(new_name, ex_name)
        tag_sim = _tags_overlap(new_tags, ex_tags)
        desc_sim = _text_similarity(new_desc, ex_desc)
        prompt_sim = _text_similarity(new_prompt[:200], ex_prompt[:200]) if new_prompt and ex_prompt else 0.0

        # 加权综合分（名称权重最高）
        total = name_sim * 0.4 + tag_sim * 0.2 + desc_sim * 0.2 + prompt_sim * 0.2

        if total >= threshold:
            reason_parts = []
            if name_sim >= 0.5:
                reason_parts.append(f"名称相似({name_sim:.0%})")
            if tag_sim >= 0.3:
                reason_parts.append(f"标签重叠({tag_sim:.0%})")
            if prompt_sim >= 0.4:
                reason_parts.append(f"提示词相似({prompt_sim:.0%})")
            if desc_sim >= 0.4:
                reason_parts.append(f"描述相似({desc_sim:.0%})")

            candidates.append({
                "existing": ex,
                "score": round(total, 3),
                "match_reason": "、".join(reason_parts) or f"综合相似度 {total:.0%}",
            })

    # 按分数降序，只保留 top-3
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:3]


async def compare_items_with_llm(
    pairs: list[dict],
    target_type: str,
    llm_endpoint: str,
    llm_api_key: str,
    llm_model: str,
) -> list[dict]:
    """
    调用 LLM 对新旧条目进行质量对比。
    pairs: [{ "new": {...}, "existing": {...}, "match_reason": "..." }, ...]
    返回: [{ "index": 0, "verdict": "replace|duplicate|keep_both", "reason": "..." }, ...]
    """
    if not pairs:
        return []

    pair_descriptions = []
    for i, pair in enumerate(pairs):
        new_item = pair["new"]
        ex_item = pair["existing"]
        pair_descriptions.append(
            f"--- 对比 #{i} ---\n"
            f"匹配原因: {pair.get('match_reason', '未知')}\n"
            f"【新条目】\n{json.dumps(new_item, ensure_ascii=False, indent=2)}\n"
            f"【已有条目】\n{json.dumps(ex_item, ensure_ascii=False, indent=2)}"
        )

    type_label = {"cases": "案例", "knowledge": "知识库条目", "templates": "模板"}.get(target_type, "条目")

    system_prompt = f"""你是 AI 绘图内容库的质量审核员。
你需要对比每一对新旧{type_label}，评估内容质量并给出决策。

评估维度：
- 提示词/内容的**详细程度**和**专业性**
- 技巧/建议的**实用性**和**完整度**
- 描述的**清晰度**和**信息量**
- 是否有**独特的新视角**或**更先进的方法论**

决策说明：
- "replace"：新条目在上述多个维度明显优于已有条目，建议替换
- "duplicate"：新旧内容本质相同或质量接近，无需重复添加
- "keep_both"：虽然主题相似但各有侧重点，建议同时保留

输出要求：
直接输出 JSON 数组，每个元素格式如下：
{{"index": 对比编号, "verdict": "replace|duplicate|keep_both", "reason": "一句话解释原因"}}
只输出合法 JSON 数组，不要输出其他文字。"""

    user_prompt = "\n\n".join(pair_descriptions)

    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(llm_endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()

    raw_text = result["choices"][0]["message"]["content"]
    return _parse_json_from_text(raw_text)


async def compare_with_existing(
    items: list[dict],
    target_type: str,
    llm_endpoint: str,
    llm_api_key: str,
    llm_model: str,
) -> list[dict]:
    """
    对提取出的条目进行智能去重对比。

    返回带有 _comparison 字段的条目列表：
    {
      ...原始字段...,
      "_comparison": {
        "verdict": "new" | "replace" | "duplicate" | "keep_both",
        "reason": "...",
        "matched_existing": { ... } | null,
        "match_reason": "..." | null,
        "similarity_score": 0.0~1.0
      }
    }
    """
    existing = _load_existing(target_type)

    if not existing:
        # 库里没有数据，全部标记为 new
        for item in items:
            item["_comparison"] = {
                "verdict": "new",
                "reason": "知识库为空，全部为新内容",
                "matched_existing": None,
                "match_reason": None,
                "similarity_score": 0.0,
            }
        return items

    # Phase 1: 本地候选匹配
    pairs_for_llm = []  # 需要 LLM 深度对比的
    item_candidate_map = {}  # index → best candidate

    for i, item in enumerate(items):
        candidates = find_candidates(item, existing)
        if candidates:
            best = candidates[0]
            item_candidate_map[i] = best
            pairs_for_llm.append({
                "new": {k: v for k, v in item.items() if not k.startswith("_")},
                "existing": best["existing"],
                "match_reason": best["match_reason"],
                "item_index": i,
            })

    # Phase 2: LLM 对比（仅对有候选的条目）
    llm_verdicts = {}
    if pairs_for_llm:
        try:
            verdicts = await compare_items_with_llm(
                pairs_for_llm, target_type,
                llm_endpoint, llm_api_key, llm_model,
            )
            for v in verdicts:
                idx = v.get("index", -1)
                if 0 <= idx < len(pairs_for_llm):
                    original_index = pairs_for_llm[idx]["item_index"]
                    llm_verdicts[original_index] = v
        except Exception as e:
            # LLM 对比失败不影响主流程，降级为仅本地匹配
            print(f"LLM comparison failed, falling back to local: {e}")

    # Phase 3: 组装结果
    for i, item in enumerate(items):
        if i in item_candidate_map:
            best = item_candidate_map[i]
            llm_v = llm_verdicts.get(i)

            if llm_v:
                verdict = llm_v.get("verdict", "duplicate")
                reason = llm_v.get("reason", "")
            else:
                # 无 LLM 结果时，根据分数做简单判断
                score = best["score"]
                if score >= 0.8:
                    verdict = "duplicate"
                    reason = f"本地匹配度很高({score:.0%})，疑似重复"
                else:
                    verdict = "keep_both"
                    reason = f"有一定相似度({score:.0%})，但无法确定是否重复"

            item["_comparison"] = {
                "verdict": verdict,
                "reason": reason,
                "matched_existing": best["existing"],
                "match_reason": best["match_reason"],
                "similarity_score": best["score"],
            }
        else:
            item["_comparison"] = {
                "verdict": "new",
                "reason": "未发现相似的已有内容",
                "matched_existing": None,
                "match_reason": None,
                "similarity_score": 0.0,
            }

    return items


# ═══════════════════════════════════════════════════════════════════════
#  3. URL 抓取
# ═══════════════════════════════════════════════════════════════════════

async def fetch_url_content(url: str) -> str:
    """抓取 URL 的文本内容。"""
    _validate_fetch_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        async with client.stream("GET", url, headers=headers) as resp:
            _validate_fetch_url(str(resp.url))
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if content_type and content_type not in ALLOWED_CONTENT_TYPES and not content_type.startswith("text/"):
                raise ValueError(f"不支持抓取该内容类型: {content_type}")

            body = bytearray()
            async for chunk in resp.aiter_bytes():
                body.extend(chunk)
                if len(body) > MAX_FETCH_BYTES:
                    raise ValueError("抓取内容超过大小限制")

            html = bytes(body).decode(resp.encoding or "utf-8", errors="replace")

    # 简易 HTML → 纯文本
    text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _validate_fetch_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_FETCH_SCHEMES:
        raise ValueError("仅支持抓取 http/https URL")
    if not parsed.hostname:
        raise ValueError("URL 缺少有效域名")

    try:
        addr_infos = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("无法解析 URL 域名") from exc

    for info in addr_infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local or
            ip.is_multicast or ip.is_reserved or ip.is_unspecified
        ):
            raise ValueError("不允许抓取内网、本机或保留地址")


# ═══════════════════════════════════════════════════════════════════════
#  4. 持久化
# ═══════════════════════════════════════════════════════════════════════

def save_items(target_type: str, items: list[dict], replace_ids: list[str] = None) -> dict:
    """
    将提取的条目保存到对应 JSON 文件。
    - 纯新增的条目直接追加
    - replace_ids 中的 id 会替换已有同 id 条目
    返回 {"added": n, "replaced": n}
    """
    filename = FILE_MAP.get(target_type)
    if not filename:
        raise ValueError(f"不支持的目标类型: {target_type}")

    filepath = DATA_DIR / filename

    # 读取现有数据
    existing = load_json_list(filepath)

    # 清理 _comparison 元数据
    clean_items = []
    for item in items:
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        clean_items.append(clean)

    replace_id_set = set(replace_ids or [])
    existing_id_map = {item.get("id"): idx for idx, item in enumerate(existing)}

    added = 0
    replaced = 0

    for item in clean_items:
        item_id = item.get("id")
        if item_id in replace_id_set and item_id in existing_id_map:
            # 替换已有条目
            existing[existing_id_map[item_id]] = item
            replaced += 1
        elif item_id not in existing_id_map:
            # 新增
            existing.append(item)
            added += 1
        # else: 已存在且不在替换列表中，跳过

    if added > 0 or replaced > 0:
        write_json_atomic(filepath, existing)

    return {"added": added, "replaced": replaced}
