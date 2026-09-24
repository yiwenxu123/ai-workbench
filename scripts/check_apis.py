#!/usr/bin/env python3
"""
API 兼容性巡检脚本
两层检查：
    1. backend/.env 的内容平台（图像/视频/编辑/向量）—— 发最小冒烟请求，不耗额度
    2. scripts/model_catalog.json 的生产模型（P0⑦，默认开启）—— 网关认证、
       网关在售清单核对、私有协议账号级判定；全部用零消耗探针

用法:
    python scripts/check_apis.py                    # 两层都查，输出表格
    python scripts/check_apis.py --json             # JSON 输出 (CI/定时任务友好)
    python scripts/check_apis.py --exit-code        # 任一检查失败时退出码为 1
    python scripts/check_apis.py --no-catalog       # 只查第 1 层
    python scripts/check_apis.py --deep             # 第 2 层再对 ¥0 TTS 真合成

判定规则 (与后端 /validate-api 一致):
    2xx / 400 / 422 → ✅ 端点可达 + 认证通过 (400 为参数校验, 不产生真实生成)
    401 → ❌ API 密钥无效或已过期
    403 → ❌ 无权限 (密钥权限不足或账户余额不足)
    404 → ❌ API 端点地址错误
    其他 4xx/5xx → ⚠️ 接口可能已变更, 需人工确认
    超时/连接错误  → ❌ 网络或端点不可达

第 2 层不看 HTTP 状态而看响应体错误码（欠费可能回 400 也可能回 200），
详见 _classify_probe 上方的实测记录。

巡检记录写入 docs/api-watch.md (见 --watch 选项)。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# dotenv 只服务第 1 层（backend/.env 的内容平台）。生产模型那条链跑在
# .venv-pyjd 里，那个 venv 不装 dotenv —— 装不上就降级成"第 1 层查不了"，
# 而不是整个脚本起不来，这样巡检才能用管线自己的解释器跑。
try:
    from dotenv import load_dotenv  # noqa: E402

    load_dotenv(BACKEND_DIR / ".env")
    ENV_AVAILABLE = True
except ImportError:
    ENV_AVAILABLE = False

TIMEOUT = 12.0


@dataclass
class CheckResult:
    provider: str
    capability: str
    status: str  # ok | fail | skip
    status_code: int
    detail: str


def _classify(response: httpx.Response) -> tuple[str, str]:
    code = response.status_code
    if code in (200, 201, 400, 422):
        return "ok", "端点可达 + 认证通过"
    if code == 401:
        return "fail", "API密钥无效或已过期"
    if code == 403:
        return "fail", "无权限（密钥权限/账户余额）"
    if code == 404:
        return "fail", "API端点地址错误"
    return "fail", f"接口可能已变更，HTTP {code}: {response.text[:120]}"


def _smoke(label: str, capability: str, endpoint: str, api_key: str,
           payload: dict, results: list[CheckResult]) -> None:
    if not endpoint or not api_key:
        results.append(CheckResult(label, capability, "skip", 0, "未配置 (backend/.env 缺少密钥或端点)"))
        return
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
        status, detail = _classify(resp)
        results.append(CheckResult(label, capability, status, resp.status_code, detail))
    except httpx.TimeoutException:
        results.append(CheckResult(label, capability, "fail", 0, "连接超时"))
    except httpx.ConnectError:
        results.append(CheckResult(label, capability, "fail", 0, "无法连接到端点（网络/DNS）"))
    except Exception as e:  # noqa: BLE001
        results.append(CheckResult(label, capability, "fail", 0, f"异常: {e}"))


def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = []

    if not ENV_AVAILABLE:
        results.append(CheckResult("backend/.env", "platform", "skip", 0,
                                   f"解释器无 python-dotenv（{sys.executable}），第 1 层未查"))

    image_endpoint = os.getenv("API_ENDPOINT", "")
    image_key = os.getenv("API_KEY", "")
    if image_endpoint and "multimodal-generation" in image_endpoint:
        image_payload = {
            "model": "qwen-image-2.0-pro",
            "input": {"messages": [{"role": "user", "content": [{"text": "test"}]}]},
            "parameters": {"size": "1024*1024", "n": 1},
        }
    else:
        image_payload = {"prompt": "test", "model": "default", "size": "256x256", "n": 1}
    _smoke("豆包/通义图像", "image", image_endpoint, image_key, image_payload, results)

    _smoke("可灵", "video",
           os.getenv("KLING_API_ENDPOINT", ""),
           os.getenv("KLING_API_KEY", ""),
           {"prompt": "test", "model": "kling-v1", "duration": 3, "resolution": "720p"},
           results)

    _smoke("即梦", "video",
           os.getenv("JIMENG_API_ENDPOINT", ""),
           os.getenv("JIMENG_API_KEY", ""),
           {"prompt": "test", "model": "jimeng-v1", "duration": 3, "resolution": "720p"},
           results)

    _smoke("Runway", "video",
           os.getenv("RUNWAY_API_ENDPOINT", ""),
           os.getenv("RUNWAY_API_KEY", ""),
           {"prompt": "test", "model": "runway-gen3", "duration": 3, "resolution": "720p"},
           results)

    edit_endpoint = os.getenv("ALIYUN_EDIT_API_ENDPOINT", "")
    edit_key = os.getenv("ALIYUN_API_KEY", "")
    if edit_endpoint:
        edit_payload = {
            "model": "wanx2.1-imageedit",
            "input": {
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "instruction": "test",
            },
        }
    else:
        edit_payload = {}
    _smoke("阿里万相编辑", "edit", edit_endpoint, edit_key, edit_payload, results)

    embed_endpoint = os.getenv("DASHSCOPE_EMBEDDING_ENDPOINT", "")
    embed_key = os.getenv("DASHSCOPE_API_KEY", "")
    if embed_endpoint and "dashscope" in embed_endpoint:
        embed_payload = {"model": os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4"),
                         "input": {"texts": ["test"]}}
    else:
        embed_payload = {"model": "text-embedding-v4", "input": {"texts": ["test"]}}
    _smoke("DashScope向量", "embedding", embed_endpoint, embed_key, embed_payload, results)

    return results


# ── 模型目录巡检（P0⑦：网关认证 / 在售核对 / 账号级失效）──────────────────
# 与上面 backend/.env 那一段互补：那层管内容平台，这层管『脚本→成片』的生产模型。
# 这里**不复用 _classify** —— 它按「HTTP 400 = 参数校验 = 通过」判定，而实测三类
# 故障的状态码互不一致，沿用旧规则会把欠费的账号报成绿色：
#     百炼欠费        → HTTP 400 + code=Arrearage
#     MiniMax 欠费    → HTTP 200 + insufficient balance   （200 也可能是坏消息）
#     套餐不含该模型  → HTTP 404 + code=UnsupportedModel
# 所以判据一律取响应体里的错误码，HTTP 状态只作次要线索。

_ACCOUNT_CODES = ("arrearage", "insufficient balance", "overdue-payment",
                  "accessdenied", "unpurchased", "quota exceeded")
_RETIRED_CODES = ("model not exist", "unsupportedmodel", "model not supported",
                  "model_not_found", "does not support")
# 方舟 plan 端点不暴露 /models，只能靠逐条目探针证明认证与套餐覆盖。
_NO_LIST_GATEWAYS = ("ark-plan",)
# 这两个 provider 有专门的定性步骤（第 3 步账号级探针 / 第 4 步真合成），
# 第 2 步就跳过它们的条目，否则同一个模型会在报告里出现两遍且结论互相矛盾。
_ACCOUNT_PROBED_PROVIDERS = ("dashscope",)
_SMOKE_PROBED_PROVIDERS = ("edge",)
_DS_T2I = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"


def _brief(text: str, n: int = 150) -> str:
    return " ".join(str(text or "").split())[:n]


def _request(method: str, url: str, key: str,
             payload: dict | None = None) -> tuple[int, str]:
    """返回 (HTTP 状态, 响应体文本)；传输层失败时状态为 0、体为错误说明。"""
    headers = {"Authorization": f"Bearer {key}"}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode()
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.request(method, url, content=body, headers=headers)
        return r.status_code, r.text
    except httpx.TimeoutException:
        return 0, "连接超时"
    except httpx.ConnectError:
        return 0, "无法连接到端点（网络/DNS）"
    except Exception as e:  # noqa: BLE001
        return 0, f"异常: {e}"


def _classify_probe(status: int, text: str) -> tuple[str, str]:
    low = (text or "").lower()
    for code in _ACCOUNT_CODES:
        if code in low:
            return "fail", f"账号级失效（{code}）——去控制台查余额/资格：{_brief(text)}"
    for code in _RETIRED_CODES:
        if code in low:
            return "fail", f"模型已下架或不在套餐（{code}）：{_brief(text)}"
    if status == 0:
        return "fail", text
    if status == 401:
        return "fail", "API密钥无效或已过期"
    if status == 403:
        return "fail", f"HTTP 403 无权限：{_brief(text)}"
    if 200 <= status < 300:
        return "ok", "认证通过"
    return "ok", "认证通过（参数被拒＝探针未真正生成，零消耗）"


def run_catalog_checks(deep: bool = False) -> list[CheckResult]:
    """按 model_catalog.json 巡检生产模型：网关认证、在售清单核对、账号级失效。

    默认零消耗：/models 只读，方舟与百炼都用「有效模型名 + 必然越界的参数」换
    错误码 —— 认证与模型校验发生在计费之前，所以能定性而不会出图/不出任务。
    只有 --deep 才真合成音频（¥0 通道），用于确认端到端而非只看认证。
    """
    results: list[CheckResult] = []
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import providers as P
    except Exception as e:  # noqa: BLE001
        return [CheckResult("model_catalog", "gateway", "fail", 0, f"无法导入 providers: {e}")]
    P.record_cost = lambda *a, **k: None  # 巡检不进成本台账
    cat = P.load_model_catalog(force=True)
    gws = cat.get("gateways") or {}
    sections = {s: (cat.get(s) or []) for s in ("tts", "image", "video")}

    # 1) 网关：认证 + 拉在售清单
    on_sale: dict[str, set | None] = {}
    for gname, gw in gws.items():
        on_sale[gname] = None
        base = (gw.get("base_url") or "").rstrip("/")
        key = P._read_gateway_secret(gw)
        if not base:
            results.append(CheckResult(f"网关 {gname}", "gateway", "skip", 0,
                                       "base_url 未配置（model_catalog.json gateways）"))
            continue
        if not key:
            results.append(CheckResult(f"网关 {gname}", "gateway", "fail", 0,
                                       f"缺密钥 {gw.get('key_env')}"
                                       f"（~/.dsh/secrets/{gw.get('secret_file')}）"))
            continue
        if gname in _NO_LIST_GATEWAYS:
            continue
        status, text = _request("GET", base + "/models", key)
        if status == 200:
            try:
                on_sale[gname] = {m.get("id") for m in (json.loads(text).get("data") or [])}
                results.append(CheckResult(f"网关 {gname}", "gateway", "ok", 200,
                                           f"认证通过，在售模型 {len(on_sale[gname])} 个"))
            except Exception as e:  # noqa: BLE001
                results.append(CheckResult(f"网关 {gname}", "gateway", "fail", 200,
                                           f"清单解析失败: {e}"))
        else:
            ok, detail = _classify_probe(status, text)
            results.append(CheckResult(f"网关 {gname}", "gateway", ok, status, detail))

    # 2) 目录条目逐个定性
    for section, entries in sections.items():
        for e in entries:
            prov, model, gname = e.get("provider"), e.get("model"), e.get("gateway")
            label = f"{prov}/{model or e.get('label') or '无模型名'}"
            if prov in _ACCOUNT_PROBED_PROVIDERS or prov in _SMOKE_PROBED_PROVIDERS:
                continue  # 由第 3/4 步整体定性，这里不出行免得同一模型报两遍
            if not model:
                results.append(CheckResult(label, section, "skip", 0,
                                           "无模型名（本地/免费通道，不发请求）"))
                continue
            if gname in _NO_LIST_GATEWAYS:
                gw = gws[gname]
                base = (gw.get("base_url") or "").rstrip("/")
                key = P._read_gateway_secret(gw)
                if not key:
                    results.append(CheckResult(label, section, "fail", 0,
                                               f"缺密钥 {gw.get('key_env')}"))
                    continue
                # 越界 size 一定被参数校验拦下（该端点强制 ≥3,686,400 像素），
                # 既证明套餐含这个模型，又绝不会真的出图烧积分。
                status, text = _request("POST", base + "/images/generations", key,
                                        {"model": model, "prompt": "probe",
                                         "size": "100x100", "response_format": "url"})
                ok, detail = _classify_probe(status, text)
                results.append(CheckResult(label, section, ok, status,
                                           detail + "（越界 size 探针，未出图）"))
                continue
            ids = on_sale.get(gname) if gname else None
            if ids is None:
                results.append(CheckResult(label, section, "skip", 0,
                                           f"无在售清单可核对"
                                           f"（{'网关 ' + gname + ' 不可用' if gname else '私有协议，未挂网关'}）"))
                continue
            if model in ids:
                results.append(CheckResult(label, section, "ok", 200, "在网关在售清单中"))
            else:
                results.append(CheckResult(label, section, "fail", 0,
                                           f"目录登记的模型已不在 {gname} 清单里"
                                           f"（下架或改名，调用必然 4xx）"))

    # 3) 私有协议 provider：百炼这类账号的失效几乎都是**账号级**的，一次探针
    #    就能给它名下全部条目定性，不必逐个打；空 input 不会提交任务也不计费。
    ds = [e for s in ("tts", "image", "video") for e in sections[s]
          if e.get("provider") == "dashscope" and e.get("model")]
    if ds:
        key = P._read_secret("DASHSCOPE_API_KEY", getattr(P, "_DS_ENV", ""))
        probe_model = ds[0]["model"]
        if not key:
            results.append(CheckResult("dashscope（账号级）", "gateway", "fail", 0,
                                       "缺 DASHSCOPE_API_KEY"))
        else:
            status, text = _request("POST", _DS_T2I, key,
                                    {"model": probe_model, "input": {}})
            ok, detail = _classify_probe(status, text)
            results.append(CheckResult(f"dashscope（账号级探针 {probe_model}）",
                                       "gateway", ok, status, detail))
            if ok == "fail":
                for e in ds:
                    results.append(CheckResult(f"dashscope/{e['model']}",
                                               "tts" if e in sections["tts"] else
                                               ("image" if e in sections["image"] else "video"),
                                               "fail", 0, "随账号判定：不可用"))

    # 4) edge 是 TTS 降级链的最后一道，且没有密钥可查 —— 唯一的诚实检查就是真
    #    合成一句。它免费、约 2s、不碰任何计费端点，所以默认就查而不留到 --deep。
    P.init_catalog_providers()
    try:
        data, dur = P.TTS_PROVIDERS["edge"]["fn"]("巡检探针。", "zh-CN-YunjianNeural", 1.0)
        results.append(CheckResult("edge/无模型", "tts",
                                   "ok" if len(data) > 1000 else "fail", 200,
                                   f"真合成 {dur}s / {len(data)}B（免费兜底）"))
    except Exception as e:  # noqa: BLE001
        msg = _brief(str(e))
        # 依赖缺失不是服务故障：巡检按 ci.sh 用 backend/.venv 跑，而管线用
        # .venv-pyjd。用错解释器时报「兜底挂了」是假告警，得和真失败分开。
        if "edge-tts" in msg.lower() or "no module named" in msg.lower():
            results.append(CheckResult("edge/无模型", "tts", "skip", 0,
                                       f"当前解释器无 edge-tts（{sys.executable}）"
                                       f"——用管线的 venv 跑本脚本才能验到这条兜底"))
        else:
            results.append(CheckResult("edge/无模型", "tts", "fail", 0,
                                       f"降级链最后兜底也不可用: {msg}"))

    # 5) --deep：对登记价 ¥0 的 OpenAI 兼容 TTS 真合成，确认端到端而不只认证。
    #    生图不参与：方舟的 ¥0 是套餐积分，真出图就是真消耗。
    if deep:
        for e in sections["tts"]:
            if e.get("protocol") != "openai-audio" or float(e.get("price_per_wan") or 0) > 0:
                continue
            label = f"{e.get('provider')}/{e.get('model')} 真合成"
            try:
                fn = P.TTS_PROVIDERS[e["provider"]]["fn"]
                data, dur = fn("巡检探针。", e.get("default_voice"), 1.0, e["model"])
                results.append(CheckResult(label, "tts",
                                           "ok" if len(data) > 1000 else "fail", 200,
                                           f"{dur}s / {len(data)}B"))
            except Exception as ex:  # noqa: BLE001
                results.append(CheckResult(label, "tts", "fail", 0, _brief(str(ex))))

    return results


def _render_table(results: list[CheckResult]) -> str:
    lines = [f"# AI 绘图工作台 API 巡检报告 — {date.today().isoformat()}",
             "",
             "| 供应商 | 能力 | 状态 | HTTP | 详情 |",
             "|--------|------|------|------|------|"]
    for r in results:
        icon = {"ok": "✅", "fail": "❌", "skip": "⚠️"}[r.status]
        code = str(r.status_code) if r.status_code else "-"
        lines.append(f"| {r.provider} | {r.capability} | {icon} | {code} | {r.detail} |")
    lines.append("")
    active = [r for r in results if r.status != "skip"]
    passed = sum(1 for r in active if r.status == "ok")
    lines.append(f"**结果**: {passed}/{len(active)} 通过，跳过 {len(results) - len(active)} 项未配置")
    return "\n".join(lines)


def append_to_watch(results: list[CheckResult]) -> None:
    watch = ROOT / "docs" / "api-watch.md"
    section = ["", f"## {date.today().isoformat()}", ""]
    for r in results:
        icon = {"ok": "✅", "fail": "❌", "skip": "⚠️"}[r.status]
        section.append(f"- **{r.provider}** ({r.capability}): {icon} HTTP {r.status_code or '-'} — {r.detail}")
    if watch.exists():
        content = watch.read_text(encoding="utf-8")
        header, sep, rest = content.partition("---")
        if sep:
            content = f"{header}{sep}{rest}"
            insert_at = content.find("## ")
            content = content[:insert_at] + "\n".join(section).strip() + "\n" + content[insert_at:]
        else:
            content += "\n".join(section) + "\n"
    else:
        content = f"# API 变更巡检记录\n\n自动巡检追加在此。手动记录平台接口变更请按日期追加。\n" + "\n".join(section) + "\n"
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="API 兼容性巡检")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--exit-code", action="store_true", help="任一失败时退出码 1")
    parser.add_argument("--watch", action="store_true", help="追加巡检记录到 docs/api-watch.md")
    parser.add_argument("--no-catalog", action="store_true",
                        help="只查 backend/.env 的内容平台，跳过 model_catalog.json 生产模型")
    parser.add_argument("--deep", action="store_true",
                        help="对 ¥0 的 OpenAI 兼容 TTS 真合成（默认只查认证与在售，零消耗）")
    args = parser.parse_args()

    start = time.monotonic()
    results = run_checks()
    if not args.no_catalog:
        results += run_catalog_checks(deep=args.deep)
    elapsed = time.monotonic() - start

    if args.json:
        print(json.dumps({
            "date": date.today().isoformat(),
            "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_s": round(elapsed, 2),
            "checks": [asdict(r) for r in results],
            "passed": sum(1 for r in results if r.status == "ok"),
            "failed": sum(1 for r in results if r.status == "fail"),
            "skipped": sum(1 for r in results if r.status == "skip"),
            "total": len(results),
        }, ensure_ascii=False, indent=2))
    else:
        print(_render_table(results))
        print(f"耗时 {elapsed:.1f}s")

    if args.watch:
        append_to_watch(results)
        print(f"已追加记录: docs/api-watch.md")

    if args.exit_code:
        return 1 if any(r.status == "fail" for r in results) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
