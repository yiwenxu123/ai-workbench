"""
AI绘图工作台 - 后端API代理服务
功能：代理前端请求到AI绘图/视频平台
支持：前端传入密钥 或 后端默认配置
安全：速率限制、输入验证
"""
import json
import os
import time
from collections import defaultdict

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import RATE_LIMITED_PATHS, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
from models import FetchUrlRequest, IngestExtractRequest, IngestSaveRequest
from routers.generation import router as generation_router
from routers.content import router as content_router

load_dotenv()

from knowledge_db import init_db as init_knowledge_db

app = FastAPI(
    title="AI绘图工作台 API",
    description="API代理服务 - 支持图像生成、视频生成、图片编辑",
    version="2.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5345",
        "http://127.0.0.1:5345",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiting ────────────────────────────────────────────────────

rate_limit_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    rate_limit_store[client_ip] = [ts for ts in rate_limit_store[client_ip] if ts > window_start]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    rate_limit_store[client_ip].append(now)
    return True


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in RATE_LIMITED_PATHS and request.method == "POST":
        client_ip = request.client.host or "unknown"
        if not check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "请求过于频繁，请稍后再试"},
            )
    return await call_next(request)


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    errors = []
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            field = '.'.join(str(loc) for loc in error.get('loc', []))
            message = error.get('msg', '验证失败')
            errors.append(f"{field}: {message}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "; ".join(errors) if errors else "输入验证失败",
        },
    )


# ── Health ────────────────────────────────────────────────────────────


@app.get("/")
async def root():
    return {"status": "ok", "message": "AI绘图工作台API运行中", "version": "2.2.0"}


# ── Include Routers ──────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_knowledge_db()
    # 启动 embedding 后台 worker
    import asyncio
    from embedding_worker import run_worker
    asyncio.create_task(run_worker())

app.include_router(generation_router)
app.include_router(content_router)


# ── Content Ingestion ────────────────────────────────────────────────


@app.post("/api/ingest/fetch-url", summary="抓取网页内容")
async def api_fetch_url(request: FetchUrlRequest):
    from ingest import fetch_url_content
    try:
        text = await fetch_url_content(request.url)
        return {"success": True, "content": text[:20000], "length": len(text)}
    except Exception as e:
        return {"success": False, "error": f"抓取失败: {str(e)}"}


@app.post("/api/ingest/extract", summary="AI 提取结构化内容 (Skill)", tags=["Skills"], operation_id="extractContent")
async def api_ingest_extract(request: IngestExtractRequest):
    if request.target_type not in ("cases", "knowledge", "templates"):
        return {"success": False, "error": "target_type 仅支持 cases / knowledge / templates"}

    from ingest import call_llm, compare_with_existing
    try:
        items = await call_llm(
            content=request.content, target_type=request.target_type,
            llm_endpoint=request.llm_endpoint, llm_api_key=request.llm_api_key,
            llm_model=request.llm_model, source_url=request.source_url,
        )
        now = time.strftime("%Y-%m-%d")
        for item in items:
            item.setdefault("sourceUrl", request.source_url)
            item.setdefault("updatedAt", now)
            item.setdefault("lastVerifiedAt", now)
            item.setdefault("reviewStatus", "pending")
            item.setdefault("qualityScore", None)

        items_with_comparison = await compare_with_existing(
            items=items, target_type=request.target_type,
            llm_endpoint=request.llm_endpoint, llm_api_key=request.llm_api_key,
            llm_model=request.llm_model,
        )

        stats = {"new": 0, "replace": 0, "duplicate": 0, "keep_both": 0}
        for item in items_with_comparison:
            verdict = item.get("_comparison", {}).get("verdict", "new")
            stats[verdict] = stats.get(verdict, 0) + 1

        return {"success": True, "items": items_with_comparison, "count": len(items_with_comparison), "stats": stats}
    except Exception as e:
        return {"success": False, "error": f"提取失败: {str(e)}"}


@app.post("/api/ingest/save", summary="保存提取的内容到数据库")
async def api_ingest_save(request: IngestSaveRequest):
    if request.target_type not in ("cases", "knowledge", "templates"):
        return {"success": False, "error": "target_type 仅支持 cases / knowledge / templates"}

    from ingest import save_items
    try:
        result = save_items(request.target_type, request.items, request.replace_ids)
        total = result["added"] + result["replaced"]
        msg_parts = []
        if result["added"]:
            msg_parts.append(f"新增 {result['added']} 条")
        if result["replaced"]:
            msg_parts.append(f"替换 {result['replaced']} 条")
        message = "、".join(msg_parts) if msg_parts else "无变更"
        return {"success": True, **result, "message": f"操作完成：{message}"}
    except Exception as e:
        return {"success": False, "error": f"保存失败: {str(e)}"}


# ── Skills OpenAPI ───────────────────────────────────────────────────


@app.get("/skills/openapi.json", summary="获取 Skills OpenAPI 描述", tags=["System"])
def get_skills_openapi():
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title="AI绘图/视频助手 Tools",
        version="2.2.0",
        description="用于第三方智能体平台（Agent）调用的工具集，包含AI生图、生视频、内容抓取与智能结构化提取等功能。",
        routes=app.routes,
    )

    filtered_paths = {}
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if "Skills" in operation.get("tags", []):
                if path not in filtered_paths:
                    filtered_paths[path] = {}
                filtered_paths[path][method] = operation

    openapi_schema["paths"] = filtered_paths
    if "tags" in openapi_schema:
        del openapi_schema["tags"]
    return openapi_schema


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
