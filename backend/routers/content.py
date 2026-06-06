"""
内容管理路由：案例、模板、知识库、提示词优化
"""
import re
import time

import httpx
from fastapi import APIRouter
from config import DATA_DIR
from json_store import load_json_list, write_json_atomic
from models import (
    CreateCaseRequest, KnowledgeEntry, KnowledgeSearchRequest,
    KnowledgeSearchResponse, OptimizePromptRequest,
)

router = APIRouter()


# ── JSON 文件辅助 ──────────────────────────────────────────────────────


def _load_json(filename: str) -> list:
    return load_json_list(DATA_DIR / filename)


# ── Cases ──────────────────────────────────────────────────────────────


@router.get("/api/cases", summary="获取精选案例库 (Skill)")
async def get_cases():
    return _load_json("cases.json")


@router.post("/api/cases", summary="添加用户创作案例")
async def create_case(request: CreateCaseRequest):
    cases = _load_json("cases.json")
    now = time.strftime("%Y-%m-%d")
    new_case = {
        "id": f"case-user-{int(time.time())}",
        "name": request.title,
        "category": "general",
        "description": f"用户创作 - {request.title}",
        "prompt": request.prompt,
        "negativePrompt": request.negativePrompt,
        "model": request.model or "",
        "parameters": {},
        "tips": request.tips,
        "tags": request.tags,
        "sourceUrl": "",
        "author": "用户创作",
        "createdAt": now,
        "updatedAt": now,
        "lastVerifiedAt": now,
        "reviewStatus": "pending",
        "qualityScore": None,
    }
    if request.size:
        new_case["parameters"]["size"] = request.size
    cases.append(new_case)
    write_json_atomic(DATA_DIR / "cases.json", cases)
    return {"success": True, "case": new_case, "message": "案例已收录"}


# ── Templates ──────────────────────────────────────────────────────────


@router.get("/api/templates")
async def get_templates():
    return _load_json("templates.json")


@router.get("/api/unified-templates", summary="获取统一模板库")
async def get_unified_templates():
    unified = []

    for filename, src_name, item_type in [
        ("templates.json", "templates", "image"),
        ("work_templates.json", "work_templates", "image"),
        ("festival_templates.json", "festival_templates", "image"),
        ("video_templates.json", "video_templates", "video"),
    ]:
        for item in _load_json(filename):
            unified.append({
                "id": item.get("id", ""),
                "type": item_type,
                "taskType": item.get("category", "通用"),
                "audience": item.get("audience", "小白"),
                "requiredFields": item.get("requiredFields", []),
                "promptTemplate": item.get("prompt", ""),
                "negativePrompt": item.get("negativePrompt", ""),
                "recommendedModels": item.get("recommendedModels", []),
                "examples": item.get("examples", []),
                "source": src_name,
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "updatedAt": item.get("updatedAt", "2026-05-07"),
            })

    return unified


@router.get("/api/video-templates")
async def get_video_templates():
    return _load_json("video_templates.json")


@router.get("/api/work-templates")
async def get_work_templates():
    return _load_json("work_templates.json")


@router.get("/api/festival-templates")
async def get_festival_templates():
    return _load_json("festival_templates.json")


# ── Knowledge ──────────────────────────────────────────────────────────


@router.get("/api/knowledge")
async def get_knowledge():
    return _load_json("knowledge.json")


@router.get("/api/knowledge/terms", summary="获取术语词典")
async def get_knowledge_terms():
    entries = _load_json("knowledge.json")
    return [e for e in entries if e.get("type") == "term"]


@router.get("/api/knowledge/formulas", summary="获取提示词公式库")
async def get_knowledge_formulas():
    entries = _load_json("knowledge.json")
    return [e for e in entries if e.get("type") == "formula"]


@router.get("/api/knowledge/industries", summary="获取行业知识")
async def get_knowledge_industries():
    entries = _load_json("knowledge.json")
    return [e for e in entries if e.get("type") == "industry"]


@router.post("/api/knowledge/search", summary="知识库智能检索")
async def search_knowledge(request: KnowledgeSearchRequest):
    entries: list[dict] = _load_json("knowledge.json")
    query = request.query.lower().strip()
    scene = request.scene or "general"
    model_type = request.modelType or ""
    limit = request.limit or 10
    type_filter = [t.lower() for t in request.types] if request.types else []

    def _score(entry: dict) -> float:
        score = 0.0
        query_terms = query.split()
        search_text = (
            (entry.get("title", "") + " ") +
            (entry.get("content", "") + " ") +
            " ".join(entry.get("tags", [])) + " " +
            entry.get("category", "")
        ).lower()

        match_count = sum(1 for t in query_terms if t in search_text)
        score += match_count * 2.0

        scene_rel = entry.get("sceneRelevance", {})
        if isinstance(scene_rel, dict):
            score += scene_rel.get(scene, 0) * 5.0
            if scene != "general" and scene_rel.get(scene, 0) > 0.5:
                score += 2.0

        score += (entry.get("quality", 1.0) - 0.5) * 1.0
        return score

    filtered = []
    for entry in entries:
        etype = entry.get("type", "")
        if type_filter and etype not in type_filter:
            continue
        filtered.append(entry)

    scored = [(e, _score(e)) for e in filtered]
    scored.sort(key=lambda x: -x[1])
    top = [e for e, s in scored if s > 0][:limit]

    return KnowledgeSearchResponse(
        success=True,
        items=[KnowledgeEntry(**e) for e in top],
        total=len(top),
        query=request.query,
        scene=scene,
    )


# ── Prompt Optimization ────────────────────────────────────────────────


@router.post("/api/optimize-prompt", summary="知识增强型提示词优化 (Skill)", tags=["Skills"], operation_id="optimizePrompt")
async def optimize_prompt(request: OptimizePromptRequest):
    scene_map = {
        "product": "电商产品展示图，白底或简洁背景，突出产品细节，商业摄影风格",
        "marketing": "社交媒体营销宣传图，视觉冲击力强，适合小红书/抖音/公众号封面",
        "presentation": "PPT演示文稿配图，简洁专业，留有文字排版空间",
        "portrait": "人物肖像/形象照，专业布光，干净背景",
        "illustration": "商业插画/创意设计，独特的艺术风格",
        "general": "通用场景，根据用户描述自动适配",
    }
    style_map = {
        "general": "通用风格，根据内容自动适配",
        "professional": "专业商务风格，简洁大气",
        "minimalist": "极简风格，留白充足，构图干净",
        "creative": "创意风格，独特视角",
        "corporate": "企业风格，稳重专业",
        "casual": "轻松风格，亲切自然",
    }
    scene_desc = scene_map.get(request.scene, scene_map["general"])
    style_desc = style_map.get(request.style, style_map["general"])

    # 1. 搜索知识库
    entries = _load_json("knowledge.json")
    query_terms = request.prompt.lower().split()

    def kb_score(e):
        s = 0.0
        text = (e.get("title", "") + " " + e.get("content", "") + " " + " ".join(e.get("tags", []))).lower()
        s += sum(1 for t in query_terms if t in text) * 2.0
        s += e.get("sceneRelevance", {}).get(request.scene, 0) * 5.0
        s += (e.get("quality", 1.0) - 0.5)
        return s

    scored = [(e, kb_score(e)) for e in entries]
    scored.sort(key=lambda x: -x[1])
    top_kb = [e for e, s in scored if s > 0][:10]

    # 2. 构建 system prompt
    kb_parts = []
    groups: dict = {}
    for e in top_kb:
        t = e.get("type", "other")
        groups.setdefault(t, []).append(e)

    if "industry" in groups:
        kb_parts.append("【行业知识】")
        for e in groups["industry"]:
            kb_parts.append(f"- {e.get('content', '')}")
    if "term" in groups:
        kb_parts.append("【推荐术语】")
        for e in groups["term"]:
            title = e.get("title", "")
            examples = e.get("examples", [])
            usage = f"（例: {'、'.join(examples[:2])}）" if examples else ""
            kb_parts.append(f"- {title}{usage}")
    if "formula" in groups:
        kb_parts.append("【提示词结构公式】")
        for e in groups["formula"]:
            content = e.get("content", "")
            ex = e.get("examples", [])
            kb_parts.append(f"- {content}")
            if ex:
                kb_parts.append(f"  示例: {ex[0]}")
    if "case" in groups:
        kb_parts.append("【优秀案例参考】")
        for e in groups["case"][:3]:
            prompt = e.get("prompt", "")
            kb_parts.append(f"- {e.get('title', '')}")
            if prompt:
                kb_parts.append(f"  提示词: {prompt[:200]}")
    if "negative_pack" in groups:
        merged = ", ".join(e.get("negativePrompt", "") for e in groups["negative_pack"] if e.get("negativePrompt"))
        if merged:
            kb_parts.append(f"【负面词参考】\n- {merged}")

    knowledge_context = "\n".join(kb_parts)
    ctx_block = f"以下是与当前场景相关的专业知识，请充分运用在优化中：\n\n{knowledge_context}\n\n" if knowledge_context else ""

    system_prompt = f"""你是一个专业的 AI 绘图提示词优化助手。
你的任务：优化用户输入的提示词，使其更适合 AI 图像生成模型。

{ctx_block}优化原则：
1. 保持用户原始意图不变，转化为更专业、更具画面感的描述
2. 补充必要的画质词和风格词
3. 确保输出适合{scene_desc}
4. 采用{style_desc}
5. 使用英文输出，用逗号分隔关键词
{"6. 目标模型为 " + request.modelType + "，注意该模型的能力特点" if request.modelType else ""}

请按以下 JSON 格式输出：
{{
  "optimized_prompt": "英文提示词，包含主体、场景、风格、光线、画质等要素",
  "optimized_prompt_cn": "中文翻译（对英文的直译），用逗号分隔，方便中文用户理解",
  "negative_prompt": "负面提示词建议（英文），用逗号分隔，务必返回不要留空",
  "explanation": "用中文一段话解释优化思路，分别说明：主体选择、风格应用、构图考量、光线选择"
}}"""

    # 3. 调用 LLM
    payload = {
        "model": request.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请优化以下提示词：{request.prompt}"},
        ],
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {request.llm_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(request.llm_endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
        raw_text = result["choices"][0]["message"]["content"]

        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "success": True,
                "optimizedPrompt": parsed.get("optimized_prompt", ""),
                "optimizedPromptCN": parsed.get("optimized_prompt_cn", ""),
                "negativePrompt": parsed.get("negative_prompt", ""),
                "explanation": parsed.get("explanation", ""),
                "knowledgeRefs": top_kb[:6],
            }

        return {"success": False, "error": "无法解析 LLM 输出"}
    except Exception as e:
        return {"success": False, "error": f"优化失败: {str(e)}"}
