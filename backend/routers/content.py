"""
内容管理路由：案例、模板、知识库、提示词优化
数据源：SQLite (knowledge.db) — 替代原 JSON 文件
"""
import json
import re
import time

import httpx
from fastapi import APIRouter
from knowledge_db import (
    knowledge_list_all, knowledge_search, knowledge_upsert,
    templates_list_all, templates_list_by_task,
    cases_list_all, cases_upsert,
)
from models import (
    CreateCaseRequest, KnowledgeEntry, KnowledgeSearchRequest,
    KnowledgeSearchResponse, OptimizePromptRequest,
    EvaluateKnowledgeRequest, DeduplicateKnowledgeRequest,
)

router = APIRouter()


# ── Cases ──────────────────────────────────────────────────────────────


@router.get("/api/cases", summary="获取精选案例库 (Skill)")
async def get_cases():
    return cases_list_all()


@router.post("/api/cases", summary="添加用户创作案例")
async def create_case(request: CreateCaseRequest):
    now = time.strftime("%Y-%m-%d")
    new_case = {
        "id": f"case-user-{int(time.time())}",
        "name": request.title,
        "category": "general",
        "description": f"用户创作 - {request.title}",
        "prompt": request.prompt,
        "negativePrompt": request.negativePrompt,
        "model": request.model or "",
        "size": request.size or "",
        "tips": request.tips,
        "tags": request.tags,
        "author": "用户创作",
        "createdAt": now,
    }
    cases_upsert(new_case)
    return {"success": True, "case": new_case, "message": "案例已收录"}


# ── Templates ──────────────────────────────────────────────────────────


@router.get("/api/templates")
async def get_templates():
    return templates_list_all()


@router.get("/api/unified-templates", summary="获取统一模板库")
async def get_unified_templates():
    all_templates = templates_list_all()
    unified = []
    for item in all_templates:
        unified.append({
            "id": item.get("id", ""),
            "type": item.get("taskType", "image"),
            "taskType": item.get("category", "通用"),
            "audience": item.get("audience", "小白"),
            "requiredFields": item.get("requiredFields", []),
            "promptTemplate": item.get("prompt", ""),
            "negativePrompt": item.get("negativePrompt", ""),
            "recommendedModels": [],
            "examples": [],
            "source": item.get("source", ""),
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "updatedAt": item.get("updatedAt", ""),
            "shotSettings": item.get("shotSettings"),
            "recommendedDuration": item.get("recommendedDuration"),
            "recommendedResolution": item.get("recommendedResolution"),
            "tips": item.get("tips", []),
            "tags": item.get("tags", []),
        })
    return unified


@router.get("/api/video-templates")
async def get_video_templates():
    return templates_list_by_task("video")


@router.get("/api/work-templates")
async def get_work_templates():
    # 兼容旧接口：返回 source 为 work_templates 的模板
    return [t for t in templates_list_all() if t.get("source") == "work_templates"]


@router.get("/api/festival-templates")
async def get_festival_templates():
    return [t for t in templates_list_all() if t.get("source") == "festival_templates"]


# ── Knowledge ──────────────────────────────────────────────────────────


@router.get("/api/knowledge")
async def get_knowledge():
    return knowledge_list_all()


@router.get("/api/knowledge/terms", summary="获取术语词典")
async def get_knowledge_terms():
    return [e for e in knowledge_list_all() if e.get("type") == "term"]


@router.get("/api/knowledge/formulas", summary="获取提示词公式库")
async def get_knowledge_formulas():
    return [e for e in knowledge_list_all() if e.get("type") == "formula"]


@router.get("/api/knowledge/industries", summary="获取行业知识")
async def get_knowledge_industries():
    return [e for e in knowledge_list_all() if e.get("type") == "industry"]


@router.get("/api/knowledge/shot-language", summary="获取镜头语言知识库")
async def get_knowledge_shot_language():
    return [e for e in knowledge_list_all() if e.get("type") == "shot_language"]


@router.post("/api/knowledge/search", summary="知识库智能检索 (FTS5)")
async def search_knowledge(request: KnowledgeSearchRequest):
    query = request.query.strip()
    scene = request.scene or "general"
    limit = request.limit or 10
    type_filter = [t.lower() for t in request.types] if request.types else None

    results = knowledge_search(query=query, scene=scene, type_filter=type_filter, limit=limit)

    return KnowledgeSearchResponse(
        success=True,
        items=[KnowledgeEntry(**e) for e in results],
        total=len(results),
        query=request.query,
        scene=scene,
    )


@router.post("/api/knowledge/evaluate", summary="评估知识条目质量")
async def evaluate_knowledge(request: EvaluateKnowledgeRequest):
    """用 LLM 从专业性、实用性、创新性、详细度四维度评估知识质量"""
    system_prompt = """你是 AI 绘图知识库的质量评审员。
请从以下四个维度评估知识条目质量，每个维度 1-10 分：
1. 专业性：术语使用是否准确，内容是否专业
2. 实用性：对实际 AI 绘图是否有指导价值
3. 创新性：是否有独特视角或新颖见解
4. 详细度：描述是否足够详细具体

输出 JSON 格式：
{
  "score": 总分(1-10，四维度平均),
  "scores": {"专业性": n, "实用性": n, "创新性": n, "详细度": n},
  "reason": "一句话评估理由",
  "suggestions": ["改进建议1", "改进建议2"]
}"""

    payload = {
        "model": request.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请评估以下{request.type}类型的知识条目：\n\n{request.content}"},
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    headers = {"Authorization": f"Bearer {request.llm_api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(request.llm_endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
        raw_text = result["choices"][0]["message"]["content"]
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if json_match:
            parsed = json.loads(json_match.group())
            return {"success": True, **parsed}
        return {"success": False, "error": "无法解析 LLM 输出"}
    except Exception as e:
        return {"success": False, "error": f"评估失败: {str(e)}"}


@router.post("/api/knowledge/deduplicate", summary="知识去重检查")
async def deduplicate_knowledge(request: DeduplicateKnowledgeRequest):
    """检查新知识条目是否与已有知识重复，返回决策建议"""
    from ingest import find_candidates, compare_items_with_llm

    existing = knowledge_list_all()
    candidates = find_candidates(request.item, existing)

    if not candidates:
        return {
            "success": True,
            "decision": "new",
            "reason": "未发现相似的已有内容",
            "candidates": [],
        }

    # 如果提供了 LLM 配置，用 LLM 深度对比
    if request.llm_endpoint and request.llm_api_key:
        pairs = [{
            "new": request.item,
            "existing": c["existing"],
            "match_reason": c["match_reason"],
        } for c in candidates[:3]]
        try:
            verdicts = await compare_items_with_llm(
                pairs, request.target_type,
                request.llm_endpoint, request.llm_api_key, request.llm_model,
            )
            if verdicts:
                v = verdicts[0]
                return {
                    "success": True,
                    "decision": v.get("verdict", "duplicate"),
                    "reason": v.get("reason", ""),
                    "candidates": [{
                        "id": c["existing"].get("id"),
                        "title": c["existing"].get("title") or c["existing"].get("name"),
                        "score": c["score"],
                        "match_reason": c["match_reason"],
                    } for c in candidates],
                }
        except Exception:
            pass  # LLM 失败时降级为本地匹配

    # 仅本地匹配结果
    best = candidates[0]
    decision = "duplicate" if best["score"] >= 0.8 else "keep_both"
    return {
        "success": True,
        "decision": decision,
        "reason": f"本地匹配度 {best['score']:.0%}，{best['match_reason']}",
        "candidates": [{
            "id": c["existing"].get("id"),
            "title": c["existing"].get("title") or c["existing"].get("name"),
            "score": c["score"],
            "match_reason": c["match_reason"],
        } for c in candidates],
    }


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

    # 1. 使用 FTS5 搜索知识库
    top_kb = knowledge_search(query=request.prompt, scene=request.scene, limit=10)

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


# ── Embedding 管理 ────────────────────────────────────────────────────


@router.get("/api/embedding/stats", summary="查看 Embedding 状态统计")
async def get_embedding_stats():
    from embedding_worker import get_embedding_stats
    return get_embedding_stats()


@router.post("/api/embedding/process", summary="手动触发 Embedding 生成")
async def trigger_embedding_process():
    from embedding_worker import process_all_pending
    result = await process_all_pending()
    return {"success": True, **result}
