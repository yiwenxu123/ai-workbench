#!/usr/bin/env python3
"""
视频链路端到端编排（A 线口播）

为什么需要（§20.3 评估）：
  配音/字幕/素材/草稿/成片各脚本都已验证可用，但它们是**散件**——
  每次都要手动敲 5~6 条命令。本脚本把散件串成一条命令，这才是"链路畅通"。

阶段（按序，可跳过；编号由 ALL_STAGES 动态生成）：
  1 validate    契约校验（storyboard_schema）
  2 voiceover   逐镜配音（generate_voiceover）→ 回填实测时长
  3 srt         字幕直出（generate_srt）
  4 compliance  合规闸（check_compliance：台词/字幕/标题敏感词，**花钱前拦下**；exit 5 阻断）
  5 reuse       素材复用检索（Eagle，命中则不生图）
  6 pexels      Pexels 免费素材兜底（无 key 优雅跳过）
  7 images      分镜生图（generate_images）→ 回填 source_ref
  8 eagle       素材入库 Eagle（**在 images 闸之后**，只有人确认过的图才入库）
  9 broll       动态 B-roll（可选，默认关）
 10 draft       剪映草稿（generate_draft，含字幕样式注入）
 11 video       降级直出 mp4（assemble_video）
 12 cover       封面/标题包（generate_cover：钩子帧优选 + 标题 A/B 候选；零成本，失败不阻断）
 13 qc          粗剪自检门禁（qc_checks；error 阻断→停 qc_failed，--only qc 可复跑）

退出码：0=完成/停闸　2=QC 阻断　3=自动化档非法　4=预算熔断　5=合规未过

用法：
  run_pipeline.py --storyboard sb.json --out-dir out/ \
      [--voice-id male-qn-qingse] [--style-preset warm_humanities] \
      [--bgm bgm.mp3] [--kenburns] \
      [--skip voiceover,images] [--skip draft,video 跳过草稿/粗剪] \
      [--automation manual|cruise|auto] [--budget 5.0] \
      [--video-id 2026-09-19-xxx]

视频类型线（v5.1 P3-2 品牌线/混剪线启用）：
  分镜里的 `content_type`（koubo|brand|mixcut，可被 --content-type 覆盖）决定**默认行为**：
  品牌片默认不压全片字幕、混剪默认不配音不打字幕且素材复用优先……
  这些规则**不在本文件写死** —— 启动时从内容中心拉 `GET /videos/content-types`
  （单一真相源：内容中心 `config/video-content-types.json`），**加类型线 = 改 JSON**。
  内容中心不可达时按「无类型目录」处理（等价口播全阶段）并打印警告。

自动化三档（v5.1 P2-1，越往后越贵故决策权前移到免费阶段）：
  manual（默认） 三闸全停：台词 → 分镜 → 素材，每道都等人确认；
  cruise        只留 images 闸（画面必须人看）+ QC，台词/分镜不拦；
  auto          全跳过跑到草稿；**仅 test 档**且**必须设 --budget**，超限自动熔断（exit 4）。

预算熔断：每个花钱阶段开始前按「已花 + 本阶段预估上限」预检，超限即停并回写
`budget_exceeded`；阶段结束后再复核实际已花。粒度=阶段级（子脚本是独立进程，无法中途打断）。

首次跑建议先加 --only voiceover 出样音确认音色（样音先行），再全量。
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
VENV_PY = os.path.join(PROJECT, ".venv-pyjd/bin/python")
PY = VENV_PY if os.path.exists(VENV_PY) else sys.executable

ALL_STAGES = ["validate", "voiceover", "srt", "compliance", "reuse", "pexels", "images",
              "eagle", "broll", "draft", "video", "cover", "qc"]

# 阶段中文名（编号由 ALL_STAGES 位置动态生成，新增阶段不再需要手改 10 处编号）
STAGE_CN = {
    "validate": "契约校验", "voiceover": "逐镜配音", "srt": "字幕直出",
    "compliance": "合规闸（先审后播）",
    "reuse": "素材复用检索", "pexels": "Pexels免费素材兜底", "images": "分镜生图",
    "eagle": "素材入库Eagle", "broll": "动态B-roll（可选）",
    "draft": "剪映草稿", "video": "降级直出", "cover": "封面/标题包",
    "qc": "QC粗剪自检",
}


def stage_title(name: str) -> str:
    return f"{ALL_STAGES.index(name) + 1}/{len(ALL_STAGES)} {STAGE_CN.get(name, name)}"


def fetch_content_type_catalog(api_base: str, timeout: int = 5) -> dict:
    """从内容中心拉视频类型目录（v5.1 P3-2）。

    为什么走 HTTP 而不是本地读 JSON：类型规则的**单一真相源在内容中心**
    （`config/video-content-types.json`，与 publish-platforms.json 同约定），
    引擎是执行方不是规则方；本地再放一份必然漂移。

    拉不到就返回 {}：调用方按「无类型目录」处理 —— 等价于口播全阶段的历史行为，
    并打印警告。**绝不因为中心抖动改变产线语义**（与 compliance 的降级口径一致）。
    """
    import urllib.request
    url = api_base.rstrip("/") + "/videos/content-types"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        types = ((payload or {}).get("data") or {}).get("types")
        if not types:
            raise RuntimeError("目录为空")
        return {t.get("key"): t for t in types if isinstance(t, dict) and t.get("key")}
    except Exception as e:
        print(f"⚠️  视频类型目录拉取失败（按默认口播行为继续）: {type(e).__name__}: {str(e)[:100]}",
              file=sys.stderr)
        return {}


# 门禁类退出码（与 qc_checks 的 2 / 预算熔断的 4 并列，便于上层区分停因）
EXIT_COMPLIANCE_BLOCKED = 5


def summarize_compliance(cj: dict) -> dict:
    """compliance.json → 内容中心 videos 表存的**摘要**。

    真相源纪律：逐条命中明细留在 out_dir/compliance.json，
    控制平面只存「过没过 + 最高级别 + 计数 + 前几条命中」这类能驱动 UI 的字段。
    """
    hits = cj.get("hits") or []
    return {
        "status": "degraded" if cj.get("degraded") else ("passed" if cj.get("passed") else "failed"),
        "severity": cj.get("severity") or "",
        "counts": cj.get("counts") or {},
        "blockedCount": cj.get("blockedCount", 0),
        "hitCount": cj.get("hitCount", 0),
        "sources": cj.get("sources") or [],
        "checkedAt": cj.get("checked_at") or "",
        "error": cj.get("error") or "",
        # 只带前 5 条阻断命中给卡片展示（完整明细看 compliance.json）
        "topHits": [
            {"source": h.get("source"), "label": h.get("label"), "word": h.get("word"),
             "severity": h.get("severity"), "snippet": h.get("snippet")}
            for h in hits if h.get("severity") in (cj.get("block_severities") or [])
        ][:5],
    }


# P1-c：main() 会把 report() 注入这里，让「阶段死于哪家/什么错」落到 videos.errors
# （此前所有死亡路径只打控制台/退出码，控制平面完全不可见）。
_stage_death_report = None


def run_stage(name, cmd):
    print(f"\n{'='*60}\n▶ {stage_title(name)}\n{'='*60}")
    # stderr 逐行透传的同时留末段尾巴，供回写 error 用（不牺牲实时性）
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, bufsize=1)
    tail = ""
    for line in proc.stderr:
        sys.stderr.write(line)
        sys.stderr.flush()
        tail = (tail + line)[-400:]
    rc = proc.wait()
    if rc != 0:
        msg = (f"阶段 {STAGE_CN.get(name, name)} 失败（退出码 {rc}）"
               f"；末段输出：{tail.strip()[:200] or '（子进程无 stderr）'}")
        print(f"❌ {msg}，已中止", file=sys.stderr)
        if _stage_death_report:
            try:
                # 只记 error 不标 failed：任务停在原阶段，人可用 --only-missing 续跑
                _stage_death_report(name, note="阶段失败中止（修好后可 --only-missing 续跑）",
                                    error=msg)
            except Exception:
                pass
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="视频链路端到端编排（A 线口播）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out-dir", required=True, help="产物根目录（配音/图片/SRT/草稿）")
    ap.add_argument("--voice-id", default=None,
                    help="覆盖项目配置音色；不填则取项目配置")
    ap.add_argument("--tts-provider", default=None,
                    help="TTS provider：edge(免费) / minimax / dashscope（默认取分镜配置）")
    ap.add_argument("--image-provider", default=None,
                    help="生图 provider：minimax / dashscope（默认取分镜配置）")
    ap.add_argument("--model", default=None,
                    help="覆盖项目配置模型；不填则取项目配置（按 provider）")
    ap.add_argument("--style-preset", help="生图风格预设（不填则取分镜 style.preset）")
    ap.add_argument("--image-model", default=None,
                    help="覆盖项目配置生图模型；不填则取项目配置")
    ap.add_argument("--bgm")
    ap.add_argument("--kenburns", action=argparse.BooleanOptionalAction, default=None,
                    help="Ken Burns 效果；不传则取项目配置 video.kenburns（--no-kenburns 强制关）")
    ap.add_argument("--draft-name", help="剪映草稿名（默认取分镜 video_id）")
    ap.add_argument("--skip", default="", help="逗号分隔要跳过的阶段")
    ap.add_argument("--only", default="", help="只跑这些阶段（逗号分隔）")
    ap.add_argument("--shots", default=None,
                    help="增量重生成：只处理这些镜号（逗号分隔），透传给配音与生图")
    ap.add_argument("--only-missing", action="store_true",
                    help="增量重生成：跳过「产物已存在且输入未变」的镜（配音/生图都生效）")
    ap.add_argument("--gate", default=None,
                    help="人工确认闸（逗号分隔）：script=台词 / storyboard=画面 / images=素材")
    ap.add_argument("--automation", choices=["manual", "cruise", "auto"], default="manual",
                    help="自动化档位（v5.1 P2-1）：manual=三闸全停（默认）；"
                         "cruise=跳过台词/分镜闸，保留 images 闸 + QC；"
                         "auto=全跳过跑到草稿（强制 test 档 + 预算熔断）")
    ap.add_argument("--budget", type=float, default=None,
                    help="本次预算上限（元）。阶段开始前按「已花 + 本阶段预估」预检，超限即熔断停下"
                         "（0 或不传=取项目配置 video.budget，再缺省=不限制）")
    ap.add_argument("--profile", choices=["test", "prod"], default="test",
                    help="test=免费优先（Edge TTS + 复用 + 不开 B-roll），"
                         "prod=用项目配置（克隆音色等）。默认 test")
    ap.add_argument("--approve", default=None,
                    help="批准通过某道闸并把 review 里的修改回写进分镜")
    ap.add_argument("--video-id", default=None,
                    help="内容中心 videos 表的任务标识（PB 记录 id 或 video_id slug）；"
                         "提供后每阶段进度自动回写 :3002（v4.0 P1-5）")
    ap.add_argument("--content-type", default=None,
                    help="覆盖分镜里的 content_type（koubo|brand|mixcut，v5.1 P3-2）；"
                         "类型决定默认跳过哪些阶段 / 素材策略 / 是否压字幕，规则见内容中心类型目录")
    args = ap.parse_args()

    sb_path = os.path.abspath(os.path.expanduser(args.storyboard))
    out = os.path.abspath(os.path.expanduser(args.out_dir))
    vo_dir = os.path.join(out, "voiceover")
    img_dir = os.path.join(out, "shots")
    srt_path = os.path.join(out, "subtitles.srt")
    os.makedirs(out, exist_ok=True)

    sb = json.load(open(sb_path, encoding="utf-8"))
    video_id = sb.get("video_id") or os.path.splitext(os.path.basename(sb_path))[0]
    draft_name = args.draft_name or f"{video_id}"
    # 命令行是否**显式**给了生图 provider（用于区分「人指定的」与「档位/项目配置给的」，
    # 混剪线的复用优先策略只覆盖后者）
    cli_image_provider = args.image_provider

    # ══ 视频类型线（v5.1 P3-2 品牌线/混剪线启用）══
    # 类型决定「默认跳过哪些阶段 / 要不要压字幕 / 素材从哪来」，规则来自内容中心类型目录
    # （单一真相源），不在本文件写死 —— 加类型线只改那边 JSON。
    content_type = args.content_type or sb.get("content_type") or "koubo"
    api_base = (os.environ.get("CONTENT_OPS_API_BASE") or "http://localhost:3002/api/v1").rstrip("/")
    type_catalog = fetch_content_type_catalog(api_base)
    cprofile = type_catalog.get(content_type) or {}
    if type_catalog and not cprofile:
        print(f"⚠️  类型 {content_type!r} 不在内容中心类型目录（允许 {sorted(type_catalog)}），"
              f"按默认（口播）行为继续", file=sys.stderr)
    # 类型侧的「要不要配音/字幕」以目录为准（而不是「本次跑没跑该阶段」）：
    # `--only qc` 复验时 stages 只有 qc，若按 stages 推断就会把口播任务的配音/字幕检查全跳过。
    expect_voiceover = bool(cprofile.get("voiceover", True))
    expect_subtitles = bool(cprofile.get("subtitle", True))

    stages = ALL_STAGES
    if args.only:
        stages = [s for s in ALL_STAGES if s in args.only.split(",")]
    elif args.skip:
        stages = [s for s in ALL_STAGES if s not in args.skip.split(",")]
    else:
        # 类型的默认跳阶段：**仅在未显式指定 --only/--skip 时生效**（命令行永远最高优先级）
        skip_by_type = [s for s in (cprofile.get("skip_stages") or []) if s in ALL_STAGES]
        if skip_by_type:
            stages = [s for s in ALL_STAGES if s not in skip_by_type]

    print(f"🎬 链路编排: {video_id}")
    print(f"   分镜: {sb_path}")
    print(f"   产物: {out}")
    print(f"   阶段: {' → '.join(stages)}")
    if cprofile:
        notes = []
        if (cprofile.get("skip_stages") or []):
            notes.append("默认跳过 " + ",".join(cprofile["skip_stages"]))
        notes.append("配音" + ("有" if expect_voiceover else "无")
                     + " / 字幕" + ("有" if expect_subtitles else "无"))
        if cprofile.get("image_policy") in ("reuse_first", "clip_first"):
            notes.append("素材=复用优先")
        if cprofile.get("aspect_ratio"):
            notes.append(f"建议比例 {cprofile['aspect_ratio']}")
        print(f"   类型: {cprofile.get('label') or content_type}（{content_type}）—— " + "；".join(notes))

    # ══ 成本核算：账本路径通过环境变量传给各子进程 ══
    cost_log = os.path.join(out, ".cost.jsonl")
    os.environ["VIDEO_COST_LOG"] = cost_log
    os.makedirs(out, exist_ok=True)

    P = lambda *a: [PY, os.path.join(HERE, a[0]), *a[1:]]

    # ══ 运行档位（默认 test：免费优先）══
    try:
        from providers import load_project_config as _lpc, unit_price as _up
        pcfg = _lpc(sb.get("project_id"))
    except Exception:
        pcfg = {}
        _up = lambda *a, **k: (0.0, True)
    tp = pcfg.get("test_profile") or {}
    if args.profile == "test":
        if not args.tts_provider:
            args.tts_provider = tp.get("tts_provider") or "edge"
        if not args.voice_id:
            args.voice_id = tp.get("voice_id") or "zh-CN-YunjianNeural"
        # v5.1：生图也必须零成本。缺省走本地占位图（reuse/pexels 命中的真实素材优先复用，
        # 只有两者都没命中的镜才出占位）；test_profile.image_provider 可指定便宜/免费图源。
        if not args.image_provider:
            args.image_provider = tp.get("image_provider") or "placeholder"
        if not args.image_model:
            args.image_model = tp.get("image_model")
        os.environ["VIDEO_PROFILE"] = "test"
        # 费用标签按真实单价显示 —— 「本次覆盖」允许在 test 档临时挂付费/未登记单价的模型，
        # 一律标 ¥0 会让人误以为免费（v5.1 P1-1 覆盖层引入后的口径修正）。
        def _price_tag(kind, provider, model):
            price, est = _up(kind, provider, model)
            if price > 0:
                return f"约¥{price * 10000:.2f}/万字" if kind == "tts" else f"约¥{price:.2f}/张"
            # est=True 表示单价未登记（不是「免费」，只是查不到）——不许谎报 ¥0
            return "单价未登记" if est else "¥0"

        tts_tag = _price_tag("tts", args.tts_provider, args.model)
        img_tag = _price_tag("image", args.image_provider, args.image_model)
        img_desc = ("出占位图" if args.image_provider == "placeholder"
                    else f"走{args.image_provider}") + f"，{img_tag}"
        print(f"🧪 档位=test（免费优先）: TTS={args.tts_provider}/{args.voice_id}（{tts_tag}）"
              f"，生图={args.image_provider}（Eagle/Pexels 优先复用，缺镜{img_desc}）"
              f"，B-roll 关闭；生产验收用 --profile prod")
    else:
        print("🚀 档位=prod：使用项目配置（克隆音色 / 付费模型）；占位图会被 QC 阻断")

    # ══ 决策时刻选型简报（v5.1 P1-7）══
    # 把「当前选了什么 / 花多少钱 / 还有哪些更省或更好的替代」在开跑前一次讲清，
    # 而不是让人翻文档。纯本地价格表推导，不联网、不校验 key。
    # 只在 prod 档打印：test 档已锁死免费组合，替代清单只会重复刷屏。
    if args.profile == "prod":
        try:
            from providers import selection_brief as _sb_brief, \
                resolve_tts_provider as _rts_prov, resolve_tts_params as _rtp, \
                resolve_image_provider as _rimg_prov, resolve_image_params as _rip
            # prod 档 args.tts_provider/image_provider 通常仍为 None（各阶段自己解析），
            # 这里用同一套 resolve_* 提前解析，保证简报与真正跑的选型完全一致。
            t_prov_name, _ = _rts_prov(args.tts_provider, sb, pcfg)
            t_voice, _, t_model, _ = _rtp(args.voice_id, args.model, sb, pcfg,
                                          prov=__import__("providers").TTS_PROVIDERS[t_prov_name])
            i_prov_name, _ = _rimg_prov(args.image_provider, sb, pcfg)
            i_model, _, _ = _rip(args.image_model, sb, pcfg,
                                 prov=__import__("providers").IMAGE_PROVIDERS[i_prov_name])
            _bc = _sb_brief(tts_prov=t_prov_name, tts_model=t_model, tts_voice=t_voice,
                            img_prov=i_prov_name, img_model=i_model,
                            profile=args.profile, project_cfg=pcfg)
            if _bc:
                print("💰 本次选型（决策时刻简报，改选型请比价后再跑）:")
                for ln in _bc:
                    print(ln)
        except Exception as _e:
            # 简报是「锦上添花」的自查信息，任何推导失败都不该阻断生产
            if os.environ.get("VIDEO_DEBUG"):
                print(f"⚠️  选型简报生成失败: {_e}", file=sys.stderr)

    # ══ 类型素材策略（v5.1 P3-2）：混剪线不默认烧 AI 生图 ══
    # 混剪的素材本质是「已有真实影像/实拍」，AI 生图既烧钱又不符合形态；故目录里
    # image_policy=reuse_first 时把生图档换成占位图（¥0）：Eagle/Pexels 命中的真实素材
    # 照常优先复用，只有都没命中的镜留占位，人再在剪映里替换。
    # 只在**命令行没显式 --image-provider** 时生效 —— 明确要 AI 生图就直说，别被悄悄覆盖。
    if cprofile.get("image_policy") in ("reuse_first", "clip_first") and not cli_image_provider:
        args.image_provider = "placeholder"
        print(f"🎞 类型={cprofile.get('label') or content_type}：素材策略=复用优先"
              f"（Eagle/Pexels 命中先用；缺镜出占位图 ¥0，请在剪映内替换为实拍素材）；"
              f"需 AI 生图请显式 --image-provider")

    # ══ kenburns / bgm：命令行 > 项目配置（v4.0 P0-3：配置字段必须生效）══
    vcfg = pcfg.get("video") or {}
    kenburns = bool(vcfg.get("kenburns")) if args.kenburns is None else args.kenburns
    bgm = args.bgm or vcfg.get("bgm") or None
    if args.kenburns is None and vcfg.get("kenburns"):
        print(f"🎬 kenburns=True（来自项目配置 video.kenburns）")
    if bgm and not args.bgm:
        print(f"🎵 BGM={os.path.basename(str(bgm))}（来自项目配置 video.bgm）")

    # ══ 人工确认闸（审计报告 P0-1）══
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import gates
    except ImportError:
        gates = None

    # ══ 进度回写内容中心（v4.0 P1-5：--video-id 提供即启用；失败仅警告不阻断）══
    import urllib.request

    def report(stage, *, status=None, note=None, error=None, fail=None, **extra):
        if not args.video_id:
            return
        base = os.environ.get("CONTENT_OPS_API_BASE", "http://localhost:3002/api/v1").rstrip("/")
        body = {"stage": stage}
        if status:
            body["status"] = status
        if note:
            body["note"] = note
        if error:
            body["error"] = error
        if fail is not None:
            body["fail"] = fail
        body.update(extra)
        headers = {"Content-Type": "application/json"}
        tok = os.environ.get("VIDEO_CALLBACK_TOKEN")
        if tok:
            headers["x-callback-token"] = tok
        try:
            req = urllib.request.Request(
                f"{base}/videos/{args.video_id}/progress",
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as r:
                r.read()
            print(f"📡 已回写进度: {stage}")
        except Exception as e:
            print(f"⚠️  进度回写失败（不影响管线）: {type(e).__name__}: {str(e)[:120]}")

    # P1-c：把回写口交给 run_stage，阶段死亡也能落 videos.errors
    global _stage_death_report
    _stage_death_report = report

    # ══ 预算熔断（v5.1 P2-1）══
    # 粒度=阶段级：各阶段是独立子进程，无法中途打断；故在「每个花钱阶段开始前」用
    # 「已花 + 本阶段上限预估」预检，超限即停。images 占单条成本约 94%，这里挡得住大头。
    budget = args.budget if args.budget and args.budget > 0 else float(vcfg.get("budget") or 0)

    def _spent():
        """本次已花（读 .cost.jsonl；子进程各自追加，跨进程可见）。"""
        try:
            from providers import load_cost_log, cost_report
            return float(cost_report(load_cost_log(cost_log)).get("total", 0.0))
        except Exception:
            return 0.0

    def _shot_id(shot, idx):
        return shot.get("shot_id", idx)

    def _shot_has_image(shot, idx):
        """该镜是否已有图（用于 --only-missing 下的成本预估）。"""
        vis = shot.get("visual") or {}
        ref = vis.get("source_ref") or {}
        for c in (vis.get("image_path"), ref.get("path"),
                  os.path.join(img_dir, f"shot_{_shot_id(shot, idx):03d}.jpg")):
            if c and os.path.exists(str(c)):
                return True
        return False

    def _pending_shots():
        """本次最多要跑的镜数（--shots 指定时按指定数量，否则全量）。"""
        shots = sb.get("shots") or []
        if args.shots:
            return min(len(shots), len([x for x in str(args.shots).replace("，", ",").split(",") if x.strip()]))
        return len(shots)

    def _stage_estimate(stage):
        """本阶段花费上限预估（元）；单价查不到按 0 计（宁可漏报也不虚报熔断）。

        P1-c：熔断要按**降级链全链**的最贵家算 —— 只算主选的话，主选挂了换贵的
        家继续烧，熔断线就成了摆设。
        """
        try:
            from providers import unit_price, fallback_chain
        except Exception:
            return 0.0

        def _chain_max_price(kind, primary, cli_model):
            try:
                import providers as _P
                reg = _P.TTS_PROVIDERS if kind == "tts" else _P.IMAGE_PROVIDERS
                names = fallback_chain(kind, primary, pcfg,
                                       free_only=(args.profile == "test"))
                best = 0.0
                for n in names:
                    model = cli_model if n == primary else reg[n].get("default_model")
                    price, _est = unit_price(kind, n, model)
                    best = max(best, price)
                return best
            except Exception:
                price, _ = unit_price(kind, primary, cli_model)
                return price

        shots = sb.get("shots") or []
        if stage == "voiceover":
            price = _chain_max_price("tts", args.tts_provider or "edge", args.model)
            if args.only_missing and not args.shots:
                chars = sum(len(str(s.get("script_line") or "")) for i, s in enumerate(shots, 1)
                            if not os.path.exists(os.path.join(vo_dir, f"shot_{_shot_id(s, i):03d}.mp3")))
            else:
                chars = sum(len(str(s.get("script_line") or "")) for s in shots)
            return chars * price
        if stage == "images":
            price = _chain_max_price("image", args.image_provider or "dashscope", args.image_model)
            if args.only_missing and not args.shots:
                n = sum(1 for i, s in enumerate(shots, 1) if not _shot_has_image(s, i))
            else:
                n = _pending_shots()
            return n * price
        if stage == "broll":
            price, _ = unit_price("video", "dashscope", None)
            return _pending_shots() * price
        return 0.0

    def _budget_stop(stage, spent, detail):
        msg = f"预算熔断：{detail}，已在「{STAGE_CN.get(stage, stage)}」停下"
        print(f"\n🛑 {msg}", file=sys.stderr)
        report("budget_exceeded", status="in_progress", note=msg,
               cost={"total": round(spent, 4)})
        sys.exit(4)

    def budget_guard(stage):
        """花钱前预检：已花 + 本阶段预估 > 上限 → 不开始，直接熔断。"""
        if not budget:
            return
        spent = _spent()
        est = _stage_estimate(stage)
        if spent + est > budget:
            _budget_stop(stage, spent,
                         f"已花 ¥{spent:.4f} + 本阶段预估上限 ¥{est:.4f} > 上限 ¥{budget:.2f}")
        print(f"💳 预算：已花 ¥{spent:.4f} / 上限 ¥{budget:.2f}（本阶段预估上限 ¥{est:.4f}）")

    def budget_watch(stage):
        """花钱后复核：实际已花超过上限 → 熔断，不再往下走。"""
        if not budget:
            return
        spent = _spent()
        if spent > budget:
            _budget_stop(stage, spent, f"实际已花 ¥{spent:.4f} > 上限 ¥{budget:.2f}")

    wanted_gates = [g.strip() for g in (args.gate or "").replace("，", ",").split(",") if g.strip()]

    # ══ 自动化档位（v5.1 P2-1）══
    # 越往后越贵，故决策权前移到免费阶段：manual 三闸全停；cruise 只留最贵的 images 闸
    # （画面必须人看）；auto 全跳过——**只允许 test 档**，无人值守 × 付费模型禁止。
    if args.automation != "manual":
        if args.automation == "auto":
            if args.profile != "test":
                print("❌ 全自动档禁止 prod 付费档（无人值守 × 付费模型 = 成本失控）。\n"
                      "   请改 --profile test，或降档为 --automation cruise / manual。", file=sys.stderr)
                sys.exit(3)
            if not budget:
                print("❌ 全自动档必须设置预算上限（--budget 或项目配置 video.budget），"
                      "否则无法熔断。", file=sys.stderr)
                sys.exit(3)
            wanted_gates = []
        else:  # cruise
            wanted_gates = ["images"]
        print(f"🤖 自动化档={args.automation}：闸位 → {'（全跳过）' if not wanted_gates else ','.join(wanted_gates)}")

    # ① 批准：先消费段落级意见（regen）→ 回写修改 → 标记通过（images 闸会把「重跑」的镜挑出来）
    # P1-b：意见未清空前**不给真批准**——regen 重写分镜后重停闸给人看效果。
    if args.approve and gates:
        for g in [x.strip() for x in args.approve.replace("，", ",").split(",") if x.strip()]:
            # 闸文件里的「意见:」行先收进本地镜像（界面提交的在服务端，union 去重兜底）
            _, _, _, fb_collected = gates.apply_review(out, g, sb)
            if fb_collected:
                added = gates.append_mirror_feedback(out, g, fb_collected)
                if added:
                    print(f"📝 从闸文件收集到 {len(added)} 条意见"
                          f"（{sorted({i['target'] for i in added})}），将自动重生成")
            pend, _src = (gates.fetch_pending_feedback(args.video_id, g, out)
                          if args.video_id
                          else (gates.read_mirror_feedback(out, g), "local"))
            if not pend and fb_collected:
                pend = fb_collected  # 纯离线（无 --video-id）时闸文件意见也要触发 regen
            if fb_collected and args.video_id and _src != "api":
                _sync_fb = json.dumps({"gate": g, "items": fb_collected},
                                      ensure_ascii=False).encode()
                try:
                    import urllib.request as _ur
                    _base = os.environ.get("CONTENT_OPS_API_BASE",
                                           "http://localhost:3002/api/v1").rstrip("/")
                    _rq = _ur.Request(f"{_base}/videos/{args.video_id}/feedback",
                                      data=_sync_fb, method="POST",
                                      headers={"Content-Type": "application/json"})
                    _tok = os.environ.get("CONTENT_OPS_API_TOKEN") or os.environ.get("AGENT_API_KEY")
                    if _tok:
                        _rq.add_header("Authorization", f"Bearer {_tok}")
                    with _ur.urlopen(_rq, timeout=8) as _r:
                        _r.read()
                    print("📡 闸文件意见已同步到内容中心（记录为准，regen 消费后统一清空）")
                except Exception as _e:
                    print(f"⚠️  意见同步内容中心失败（只用本地镜像继续）: "
                          f"{type(_e).__name__}: {str(_e)[:100]}", file=sys.stderr)
            if pend:
                print(f"🔁 【{g}】闸有 {len(pend)} 条待处理意见，先重生成再批准…")
                regen_cmd = P("regen_shots.py", "--storyboard", sb_path,
                              "--out-dir", out, "--gate", g)
                if args.video_id:
                    regen_cmd += ["--video-id", args.video_id]
                rr = subprocess.run(regen_cmd, capture_output=False, text=True)
                if rr.returncode != 0:
                    print(f"❌ 意见重生成未完成（退出码 {rr.returncode}），**未批准**【{g}】闸。\n"
                          f"   可人工直接编辑 {gates.review_path(out, g)} 的"
                          f"台词/画面字段后再 --approve {g}", file=sys.stderr)
                    sys.exit(1)
                with open(sb_path, encoding="utf-8") as f:
                    sb = json.load(f)
                # 重写闸文件：意见已消费 → 不再渲染「意见:」行（防止下次 --approve 重复收集）
                try:
                    gates.write_review(out, g, sb, img_dir, feedback=[])
                except Exception:
                    pass
                print(f"✅ 【{g}】闸意见处理完毕，重新停闸给人复核效果（直接再跑同一条 --approve 命令即可）。")
                sys.exit(0)
            sb, changes, regen = gates.apply_review(out, g, sb)[:3]
            gates.mark_approved(out, g)
            print(f"✅ 已批准【{g}】闸")
            for c in changes:
                print(f"    {c}")
            # 上一轮 regen 重写过的镜 → 本阶段只重跑这些（增量，不整批重烧）
            rerun = set(regen or [])
            ap_affected = os.path.join(out, "review", "affected_shots.json")
            if g in ("script", "images") and os.path.exists(ap_affected):
                try:
                    rerun.update(int(x) for x in json.load(open(ap_affected, encoding="utf-8")))
                    os.remove(ap_affected)
                except Exception:
                    pass
            if rerun:
                print(f"    标记重跑: 镜 {sorted(rerun)}")
                args.shots = ",".join(str(x) for x in sorted(rerun))
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
        print("    修改已回写分镜。继续运行剩余阶段。")

    # ② 闸检查：未批准则写出审阅文件并停下
    def check_gate(gate, before_stage):
        if not gates or gate not in wanted_gates:
            return
        if gates.is_approved(out, gate):
            print(f"✅【{gate}】闸已通过")
            return
        if before_stage not in stages:
            return
        rp = gates.write_review(out, gate, sb, img_dir)
        print(gates.gate_banner(out, gate, sb))
        report(f"gate_{gate}", note=f"停在人工确认闸: {gate}（审阅文件 {rp}）")
        sys.exit(0)

    check_gate("script", "voiceover")
    check_gate("storyboard", "images")

    if "validate" in stages:
        run_stage("validate", P("storyboard_schema.py", sb_path))
        report("validate", storyboardPath=sb_path, outDir=out)

    if "voiceover" in stages:
        budget_guard("voiceover")
        cmd = P("generate_voiceover.py", "--storyboard", sb_path,
                "--output-dir", vo_dir, "--update-storyboard")
        if args.voice_id:
            cmd += ["--voice-id", args.voice_id]
        if args.model:
            cmd += ["--model", args.model]
        if args.tts_provider:
            cmd += ["--tts-provider", args.tts_provider]
        if args.shots:
            cmd += ["--shots", args.shots]
        if args.only_missing:
            cmd.append("--only-missing")
        run_stage("voiceover", cmd)
        report("voiceover")
        budget_watch("voiceover")

    if "srt" in stages:
        # --split-timed：镜内按配音侧车的真实词边界断句（无侧车的镜逐字节退回旧行为）
        run_stage("srt", P(
            "generate_srt.py", "--storyboard", sb_path, "--output", srt_path,
            "--split-timed"))
        report("srt", srtPath=srt_path)

    # ══ 合规闸（v5.1 P2-3，先审后播）══
    # 放在生图之前：台词/字幕有问题时**在花钱之前**拦下。
    # 敏感词表不在这里硬编码 —— 送内容中心 /audit/compliance（复用其 sensitive_words +
    # audit_rules 自定义规则），加词只需在内容中心建规则。
    # 注意与 QC 的差别：中心不可达时**不阻断**（记 degraded，发布门禁另拦），
    # 只有「确实查出了 critical/high 命中」才停 compliance_failed（exit 5）。
    if "compliance" in stages:
        print(f"\n{'='*60}\n▶ {stage_title('compliance')}\n{'='*60}")
        comp_cmd = P("check_compliance.py", "--storyboard", sb_path, "--out-dir", out)
        comp_r = subprocess.run(comp_cmd, capture_output=False, text=True)
        if comp_r.returncode == EXIT_COMPLIANCE_BLOCKED:
            try:
                cj = json.load(open(os.path.join(out, "compliance.json"), encoding="utf-8"))
                report("compliance_failed",
                       note=f"合规未过：命中 {cj.get('blockedCount', 0)} 处（{cj.get('severity')} 级）",
                       compliance=summarize_compliance(cj))
            except Exception as e:
                print(f"⚠️  compliance.json 读取失败: {type(e).__name__}: {e}", file=sys.stderr)
                report("compliance_failed", note="合规未过（明细读取失败）")
            print(f"❌ 合规未过，已停在 {stage_title('compliance')}；"
                  f"改完台词/字幕或调整敏感词后 `--only compliance` 复跑", file=sys.stderr)
            sys.exit(EXIT_COMPLIANCE_BLOCKED)
        elif comp_r.returncode != 0:
            # 脚本自身异常（非门禁阻断）——按 QC 的既有约定：非 0 即中止
            print(f"❌ 阶段 {STAGE_CN['compliance']} 异常退出（退出码 {comp_r.returncode}），已中止",
                  file=sys.stderr)
            sys.exit(1)
        else:
            try:
                cj = json.load(open(os.path.join(out, "compliance.json"), encoding="utf-8"))
                summary = summarize_compliance(cj)
                note = ("合规检查降级（内容中心不可达），未完成检查"
                        if cj.get("degraded") else
                        (f"合规通过" + (f"（另有 {cj.get('hitCount', 0)} 处低级别提示）"
                                       if cj.get("hitCount") else "")))
                report("compliance", note=note, compliance=summary)
            except Exception as e:
                print(f"⚠️  compliance.json 读取失败（不影响管线）: {type(e).__name__}: {e}",
                      file=sys.stderr)
                report("compliance")

    # ══ 素材复用（先查 Eagle，命中则不生图 → 审计报告 P0-2 价值闭环）══
    if "reuse" in stages:
        run_stage("reuse", P(
            "eagle_reuse.py", "--storyboard", sb_path,
            "--out-dir", out, "--update-storyboard"))
        report("reuse")

    # ══ Pexels 免费素材兜底（三级路由第二级；无 key 优雅跳过，v4.0 P2-4）══
    if "pexels" in stages:
        run_stage("pexels", P(
            "pexels_search.py", "--storyboard", sb_path,
            "--output-dir", img_dir, "--update-storyboard"))

    if "images" in stages:
        budget_guard("images")
        cmd = P("generate_images.py", "--storyboard", sb_path,
                "--output-dir", img_dir, "--update-storyboard")
        # v5.1：补传 --image-provider（此前缺失，导致档位/命令行的生图 provider 到不了子脚本）
        if args.image_provider:
            cmd += ["--image-provider", args.image_provider]
        if args.image_model:
            cmd += ["--model", args.image_model]
        if args.style_preset:
            cmd += ["--style-preset", args.style_preset]
        if args.shots:
            cmd += ["--shots", args.shots]
        if args.only_missing:
            cmd.append("--only-missing")
        run_stage("images", cmd)
        report("images")
        budget_watch("images")

    # ══ images 闸：素材确认（**必须在入库 Eagle 之前**，v4.0 P0-2：
    #    否则被否决的图先入库，还会被后续 reuse 复用回来）══
    if gates and "images" in wanted_gates and "images" in stages:
        if not gates.is_approved(out, "images"):
            gates.write_review(out, "images", sb, img_dir)
            print(gates.gate_banner(out, "images", sb))
            sys.exit(0)
        print("✅【images】闸已通过")

    # ══ 素材入库 Eagle（在闸之后：只有人确认通过的图才入库）══
    if "eagle" in stages:
        run_stage("eagle", P(
            "eagle_ingest.py", "--storyboard", sb_path, "--update-storyboard"))
        report("eagle")

    # ══ 动态 B-roll（可选：项目配置 video.broll.mode，默认 none）══
    if "broll" in stages:
        budget_guard("broll")
        broll_cmd = P("generate_broll.py", "--storyboard", sb_path,
                      "--out-dir", out, "--update-storyboard")
        # 类型缺省 B-roll 模式（v5.1 P3-2）：只在项目配置**没声明** video.broll.mode 时兜底。
        # 优先级：命令行 > 项目配置 > 类型目录 > 内置 none（品牌线目录里是 key，但它不覆盖
        # 项目配置里显式的 none —— 花钱的东西不许被目录悄悄打开）。
        if cprofile.get("broll_mode") and not ((vcfg.get("broll") or {}).get("mode")):
            broll_cmd += ["--mode", str(cprofile["broll_mode"])]
        run_stage("broll", broll_cmd)
        report("broll")
        budget_watch("broll")

    if "draft" in stages:
        # 剪映草稿需要「单条整段配音」：把逐镜 mp3 按镜序拼起来
        voice_all = os.path.join(out, "voice_all.mp3")
        vo_files = []
        for i, shot in enumerate(sb.get("shots") or [], 1):
            sid = shot.get("shot_id", i)
            p = os.path.join(vo_dir, f"shot_{sid:03d}.mp3")
            if os.path.exists(p):
                vo_files.append(p)
        if vo_files:
            lst = os.path.join(out, "_vo_concat.txt")
            with open(lst, "w", encoding="utf-8") as f:
                for p in vo_files:
                    f.write(f"file '{p}'\n")
            r = subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                 "-safe", "0", "-i", lst, "-c:a", "libmp3lame", voice_all],
                capture_output=True, text=True)
            os.remove(lst)
            if r.returncode != 0:
                print(f"❌ 合成整段配音失败: {r.stderr[-300:]}", file=sys.stderr)
                sys.exit(1)
            print(f"🎧 已合成整段配音（{len(vo_files)} 段）")
        run_stage("draft", P(
            "generate_draft.py", "--draft-name", draft_name,
            "--audio", voice_all,
            "--srt", srt_path, "--storyboard", sb_path,
            "--images-dir", img_dir,
            # A4：逐镜配音目录作 ducking key，有实拍原声才产垫轨；留档到 out
            "--vo-dir", vo_dir, "--out-dir", out))
        report("draft", draftName=draft_name, draftPath=draft_name)

    if "video" in stages:
        cmd = P("assemble_video.py", "--storyboard", sb_path,
                "--srt", srt_path, "--audio-dir", vo_dir,
                "--output", os.path.join(out, f"{video_id}.mp4"))
        # 类型声明不要字幕（品牌/混剪）→ 明确关闭字幕压层。不能只靠「SRT 文件不存在」：
        # 目录里若残留上次口播跑的 subtitles.srt，就会被静默压上去。
        if not expect_subtitles:
            cmd.append("--no-subtitles")
        if kenburns:
            cmd.append("--kenburns")
        if bgm:
            cmd += ["--bgm", os.path.abspath(os.path.expanduser(str(bgm)))]
        for key, flag in (("intro", "--intro"), ("outro", "--outro")):
            v0 = vcfg.get(key)
            if v0 and os.path.exists(os.path.expanduser(str(v0))):
                cmd += [flag, os.path.abspath(os.path.expanduser(str(v0)))]
        run_stage("video", cmd)
        report("video", roughCutPath=os.path.join(out, f"{video_id}.mp4"))

    # ══ 封面/标题包（v5.1 P2-2：钩子帧优选 + 标题 A/B 候选）══
    # 零成本、确定性（不调模型）。标题真相源 = out/cover_titles.json（agent 用 LLM 写好），
    # 缺省才落 cover_templates.json 模板兜底。**失败不阻断**：这是收尾增强不是质量门禁，
    # 若在此中止会连 QC 都跑不到，任务反而卡住。
    if "cover" in stages:
        cover_cmd = P("generate_cover.py", "--storyboard", sb_path,
                      "--out-dir", out, "--update-storyboard")
        if sb.get("title"):
            cover_cmd += ["--title", str(sb["title"])]
        print(f"\n{'='*60}\n▶ {stage_title('cover')}\n{'='*60}")
        cover_r = subprocess.run(cover_cmd, capture_output=False, text=True)
        if cover_r.returncode != 0:
            print(f"⚠️  封面/标题包生成失败（退出码 {cover_r.returncode}），跳过该阶段继续",
                  file=sys.stderr)
            report("cover", note="封面/标题包生成失败（已跳过，不影响粗剪交付）")
        else:
            try:
                cj = json.load(open(os.path.join(out, "cover.json"), encoding="utf-8"))
                cov = cj.get("cover") or {}
                report("cover", cover={
                    "image": cov.get("image") or "",
                    "shotId": cov.get("shot_id"),
                    "origin": cov.get("origin") or "",
                    "hookScore": cov.get("hook_score"),
                    "aspectRatio": cj.get("aspect_ratio") or "",
                    "source": cj.get("source") or "",
                    "recommended": cj.get("recommended") or "",
                    "titles": [t.get("text") for t in (cj.get("titles") or []) if isinstance(t, dict)],
                    "copy": cj.get("copy") or {},
                })
            except Exception as e:
                print(f"⚠️  cover.json 读取失败（不影响管线）: {type(e).__name__}: {e}", file=sys.stderr)
                report("cover")

        # ══ 标题补检（v5.1 P3-2）：补「标题候选未判敏感词」这个口 ══
        # 合规闸刻意排在生图之前（台词有问题要在花钱前拦下），因此首次送检时 cover.json
        # 还不存在，sources 里一直记着「标题候选(尚未生成)」——而标题是对外露出的内容。
        # cover 跑完后用 --titles-only 补一次：结论**合并**进同一份 compliance.json
        # （不覆盖台词/字幕的既有结论），命中则与合规闸同款处理（停 compliance_failed）。
        if cover_r.returncode == 0 and "compliance" in stages:
            print(f"\n{'='*60}\n▶ 标题合规补检（cover 产出后）\n{'='*60}")
            t_cmd = P("check_compliance.py", "--storyboard", sb_path, "--out-dir", out,
                      "--titles-only")
            t_r = subprocess.run(t_cmd, capture_output=False, text=True)
            if t_r.returncode == EXIT_COMPLIANCE_BLOCKED:
                try:
                    cj = json.load(open(os.path.join(out, "compliance.json"), encoding="utf-8"))
                    # ⚠️ 刻意**不传** status：与上面的合规闸同款「可修复暂停态」语义，
                    # 让任务停在原来的交付里程碑上（传 in_progress 会把已交付任务降级成生产中）
                    report("compliance_failed",
                           note=f"标题候选合规未过：累计命中 {cj.get('blockedCount', 0)} 处"
                                f"（{cj.get('severity')} 级）",
                           compliance=summarize_compliance(cj))
                except Exception:
                    report("compliance_failed", note="标题候选合规未过")
                print("❌ 标题候选命中敏感词，已停在 compliance_failed；"
                      "改 `cover_titles.json` 后 `--only cover` 重出标题，"
                      "再 `--only compliance` 复检", file=sys.stderr)
                sys.exit(EXIT_COMPLIANCE_BLOCKED)
            if t_r.returncode != 0:
                print(f"⚠️  标题合规补检异常（退出码 {t_r.returncode}），跳过（不影响粗剪交付）",
                      file=sys.stderr)

    # ══ QC 粗剪自检门禁（v5.0：error 阻断，任务停 qc_failed，不进待终剪）══
    if "qc" in stages:
        final_mp4 = os.path.join(out, f"{video_id}.mp4")
        qc_cmd = P("qc_checks.py", "--storyboard", sb_path, "--out-dir", out,
                   "--report", os.path.join(out, "qc_report.json"))
        # 类型口径（v5.1 P3-2）：无配音/无字幕的类型线不检查对应产物，
        # 否则混剪这类视频**永远**过不了 QC（缺 mp3、缺 SRT 被判 error）。
        if not expect_voiceover:
            qc_cmd.append("--no-voiceover")
        if not expect_subtitles:
            qc_cmd.append("--no-subtitles")
        if os.path.exists(final_mp4):
            qc_cmd += ["--video", final_mp4]
        print(f"\n{'='*60}\n▶ {stage_title('qc')}\n{'='*60}")
        qc_r = subprocess.run(qc_cmd, capture_output=False, text=True)
        qc_report_path = os.path.join(out, "qc_report.json")
        qc_counts = {"error": 0, "warning": 0}
        try:
            qrj = json.load(open(qc_report_path, encoding="utf-8"))
            qc_counts = qrj.get("counts", qc_counts)
        except Exception:
            pass
        if qc_r.returncode == 2:
            # 阻断：停在 qc_failed（status 保持 in_progress——这是可修复的门禁暂停，
            # 不是终态 failed；注意不能带 error/fail，否则内容中心会强制落 failed）
            note = f"QC 未通过：{qc_counts.get('error', '?')} 项阻断 / {qc_counts.get('warning', 0)} 项提醒（见 qc_report.json）"
            report("qc_failed", status="in_progress", note=note,
                   roughCutPath=(final_mp4 if os.path.exists(final_mp4) else None))
            print(f"\n🛑 QC 门禁阻断，任务停在 qc_failed。修复后重跑：\n"
                  f"   {PY} scripts/run_pipeline.py --storyboard {sb_path} --out-dir {out}"
                  f" --video-id {args.video_id or video_id} --only qc", file=sys.stderr)
            sys.exit(2)
        if qc_r.returncode != 0:
            print(f"❌ QC 自检本身异常（退出码 {qc_r.returncode}），已中止", file=sys.stderr)
            sys.exit(1)
        report("qc", note=f"QC 通过（{qc_counts.get('warning', 0)} 项 warning）",
               roughCutPath=(final_mp4 if os.path.exists(final_mp4) else None))
    elif "video" in stages or "draft" in stages:
        print("⚠️  已跳过 QC 门禁（--skip qc）：粗剪未经机器自检，终剪前请人工确认素材完整性")

    print(f"\n{'='*60}\n✅ 链路完成: {video_id}\n{'='*60}")
    print(f"  分镜(含回填): {sb_path}")
    print(f"  配音: {vo_dir}")
    print(f"  图片: {img_dir}")
    print(f"  字幕: {srt_path}")
    if "eagle" in stages:
        print(f"  Eagle: 已入库/校验（项目文件夹）")
    if "draft" in stages:
        print(f"  草稿: {draft_name}（剪映草稿目录）")
    if "video" in stages:
        print(f"  粗剪（待终剪）: {os.path.join(out, video_id + '.mp4')}")
    if "cover" in stages:
        print(f"  封面: {os.path.join(out, 'cover.jpg')} / 标题候选: {os.path.join(out, 'cover.json')}")

    # ══ 成本汇总 ══
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from providers import cost_report, load_cost_log
        entries = load_cost_log(cost_log)
        if entries:
            rep = cost_report(entries)
            print(f"\n💰 本次消耗: ¥{rep['total']:.4f}"
                  + ("（含估算项）" if rep["has_estimate"] else ""))
            label = {"tts": "配音", "image": "生图", "video": "视频"}
            for k, b in rep["by_kind"].items():
                unit = "字" if k == "tts" else ("张" if k == "image" else "片")
                print(f"    {label.get(k, k):<4s} {b['n']:>3d} 次 / {b['units']}{unit}  → ¥{b['cost']:.4f}   {','.join(b['models'])[:48]}")
            cost_json = os.path.join(out, "cost.json")
            with open(cost_json, "w", encoding="utf-8") as f:
                json.dump({"video_id": video_id, "project_id": sb.get("project_id"),
                           "report": rep, "entries": entries}, f,
                          ensure_ascii=False, indent=2)
            print(f"    明细: {cost_json}")
        else:
            print("\n💰 本次无计费调用（全部复用或跳过）")
            rep = {"total": 0.0}
    except Exception as e:
        print(f"⚠️  成本汇总失败: {type(e).__name__}: {str(e)[:100]}", file=sys.stderr)
        rep = {"total": 0.0}

    # ══ 完成回写（含成本汇总；v4.0 P1-5）══
    # 关键：**只有「跑过 QC 门禁且没被它拦下」才算完成**。此前无条件 report("done")，
    # 导致 `--only cover` / `--only draft` 这类局部运行把整条任务标成 done/draft_ready ——
    # 实测把一条 qc_failed（QC 未过、不可交付）的任务误判成「待终剪」，等于绕过质量门禁。
    # 因此判据不是「产出过草稿/粗剪」，而是「本次运行包含 qc 且走到了这里」
    # （qc 报错会先 exit 2 中断，能走到这行即代表 QC 通过）。
    if args.video_id:
        verified = "qc" in stages
        rough_path = os.path.join(out, f"{video_id}.mp4")
        extra = {"cost": {"total": round(float(rep.get("total", 0.0)), 4),
                          "kind": {k: round(v.get("cost", 0.0), 4)
                                   for k, v in (rep.get("by_kind") or {}).items()}}}
        if os.path.exists(rough_path):
            # 粗剪走 roughCutPath：final_path 从此只由用户「终剪完成」动作登记（P0 语义分离）
            extra["roughCutPath"] = rough_path
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=nw=1:nk=1", rough_path],
                    capture_output=True, text=True, timeout=15)
                if r.returncode == 0:
                    extra["durationSec"] = round(float(r.stdout.strip()), 2)
            except Exception:
                pass
        if verified:
            report("done", note="管线跑完（QC 已过），待人工终剪", **extra)
        else:
            # 未跑 QC 的运行（--only cover / --skip qc 等）：**不碰 current_stage / status**，
            # 只回写成本与产物指针 + 一条说明性日志。空 stage 在内容中心侧等价于「保持原值」
            # （见 VideoService.reportProgress）；写成 done 会把 QC 未过的任务误显示成待终剪。
            why = (f"局部运行（仅 {','.join(stages)}）" if args.only
                   else "本次未跑 QC 门禁")
            report("", note=f"{why}：未过 QC 门禁，任务状态保持不动", **extra)
            print(f"ℹ️  {why}：未过 QC 门禁，不回写「待终剪」状态")
        # 成本红线告警（v4.0 成本纪律：>¥1 提醒）
        if float(rep.get("total", 0.0)) > 1.0:
            print(f"\n🚨 成本告警: 本次消耗 ¥{rep['total']:.2f} 超过 ¥1 红线，"
                  f"请检查是否误用付费模型/未走增量复用")


if __name__ == "__main__":
    main()
