#!/usr/bin/env python3
"""
把生成的素材入库 Eagle（审计报告 P0-2）。

为什么需要：
  此前生成的图只落在目录里，不入库、不打标 → **下次遇到相似画面还得重新生图**，
  而生图占单条成本约 94%。入 Eagle 后才能检索复用。

关键设计：**复用用户已有的 eagle-watcher 客户端**（`eagle_watcher.eagle_api`），
而不是另写一套 Eagle API 调用。理由：
  - 纯标准库、无新增依赖
  - 自带重试、token 解析（含 keychain）、文件夹 get-or-create
  - 与 eagle-watcher 共用同一套文件夹/标签体系，不会分裂成两个库

入库时写入的元数据（决定后续能否检索到）：
  - folder      —— 项目专属文件夹（配置 eagle.folder，没有则按账号名自动建）
  - tags        —— 项目 / 风格 / 景别 / 光线 / 色温
  - annotation  —— 完整生图 prompt（**这是能被语义检索到的关键**）
  - name        —— `<video_id>_镜N`

幂等：若分镜里已有 `source_ref.eagle_id` 且**库内文件与本地文件一致**（md5 比对）则跳过；
本地文件已重生成（v4.0 P0-2：素材闸勾「重跑」后）则把旧条目移入回收站并重新入库——
否则 Eagle 里永远是被用户否决的旧图，还会被后续 reuse 复用回来。

占位图守卫（v5.3.1）：test 档 placeholder（¥0 开发档、不可交付）默认**不入库**——
入库会被 reuse 语义检索命中并静默流入真实视频。判据与 qc_checks 一致
（visual.placeholder / source_ref.placeholder）；显式 --include-placeholders 才入库，
且打 placeholder 标签 + [placeholder] 标注（reuse 仍会排除）。

用法：
  eagle_ingest.py --storyboard sb.json [--folder 历史文化] [--dry-run] [--update-storyboard]
"""
import argparse
import hashlib
import json
import os
import sys
import re

EW_SRC = os.path.expanduser("~/Projects/tools/eagle-watcher/src")



def _source_ref(shot):
    """安全读取 source_ref（LLM 分镜可能写成字符串，契约只保证 dict）"""
    try:
        from storyboard_schema import source_ref as _sr
        return _sr(shot)
    except Exception:
        ref = ((shot or {}).get("visual") or {}).get("source_ref")
        return ref if isinstance(ref, dict) else {}

def get_api():
    if os.path.isdir(EW_SRC):
        sys.path.insert(0, EW_SRC)
    try:
        from eagle_watcher.eagle_api import EagleAPI, resolve_token
    except ImportError as e:
        print(f"❌ 无法复用 eagle-watcher 客户端（{e}）。"
              f"请确认 {EW_SRC} 存在且可导入。", file=sys.stderr)
        sys.exit(1)
    # token：优先 eagle-watcher 配置，其次本目录 secrets
    tok = ""
    cfgp = os.path.expanduser("~/.eagle-watcher/config.yaml")
    if os.path.exists(cfgp):
        import re
        txt = open(cfgp, encoding="utf-8").read()
        m = re.search(r"^\s*token:\s*[\"']?([^\s\"']+)", txt, re.M)
        if m:
            tok = m.group(1)
    if not tok:
        sp = os.path.expanduser("~/.dsh/secrets/eagle.env")
        if os.path.exists(sp):
            for line in open(sp):
                if line.startswith("export EAGLE_TOKEN="):
                    tok = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not tok:
        print("❌ 未找到 Eagle token（~/.eagle-watcher/config.yaml 或 "
              "~/.dsh/secrets/eagle.env）", file=sys.stderr)
        sys.exit(1)
    return EagleAPI(token=tok)


def file_md5(path, buf_size=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(buf_size):
            h.update(chunk)
    return h.hexdigest()


def stored_src_hash(api, eagle_id):
    """
    读 Eagle 条目 annotation 里的 [src_hash:...]（入库时写入）。
    ⚠️ 不用 eagle_api.get_item：Eagle v4 的 /api/v2/item/get 返回 data.data **数组**，
    get_item 按旧形状解析会拿到错乱条目（实测踩坑），这里直连 v2 并取数组首项。
    """
    try:
        import urllib.request
        url = f"http://localhost:41595/api/v2/item/get?id={eagle_id}"
        tok = os.environ.get("EAGLE_TOKEN", "")
        headers = {"Authorization": f"Bearer {tok}"} if tok else {}
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10) as r:
            d = json.loads(r.read().decode("utf-8"))
        arr = (d.get("data") or {}).get("data") or []
        ann = (arr[0] if arr else {}).get("annotation") or ""
        m = re.search(r"\[src_hash:([0-9a-f]{32})\]", ann)
        return m.group(1) if m else None
    except Exception:
        return None


def trash_item(api, eagle_id):
    try:
        api._post("item/moveToTrash", {"itemIds": [eagle_id]})
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="素材入库 Eagle（复用 eagle-watcher 客户端）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--folder", help="覆盖目标文件夹（默认取项目配置 eagle.folder）")
    ap.add_argument("--dry-run", action="store_true", help="只预览不实际入库")
    ap.add_argument("--refresh", action="store_true",
                    help="强制重新入库（忽略指纹比对；历史无指纹条目也会重建）")
    ap.add_argument("--update-storyboard", action="store_true",
                    help="把 eagle_id 回写进 visual.source_ref")
    ap.add_argument("--include-placeholders", action="store_true",
                    help="显式允许占位图入库（默认禁止）。占位图是 ¥0 开发档产物、不可交付，"
                         "入库后会被 reuse 语义检索命中并静默流入真实视频；确需入库时会打 "
                         "placeholder 标签/[placeholder] 标注，reuse 仍会排除")
    args = ap.parse_args()

    sb_path = os.path.expanduser(args.storyboard)
    sb = json.load(open(sb_path, encoding="utf-8"))
    project_id = sb.get("project_id") or ""
    video_id = sb.get("video_id") or os.path.splitext(os.path.basename(sb_path))[0]

    # 项目配置（决定文件夹与标签前缀）
    pcfg = {}
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from providers import load_project_config
        pcfg = load_project_config(project_id)
    except Exception:
        pass
    ecfg = pcfg.get("eagle") or {}
    folder_name = args.folder or ecfg.get("folder") or (pcfg.get("account") or project_id)
    tag_prefix = ecfg.get("tags") or ([project_id] if project_id else [])

    api = None if args.dry_run else get_api()
    folder_id = None
    if api:
        folder_id = api.get_or_create_folder(folder_name)
        print(f"📁 目标文件夹: {folder_name}（id={folder_id}）")

    ok, skipped, failed, ph_skipped = 0, 0, 0, 0
    for i, s in enumerate(sb.get("shots") or [], 1):
        sid = s.get("shot_id", i)
        vis = s.get("visual") or {}
        path = _source_ref(s).get("path") or vis.get("image_path")
        if not path or not os.path.exists(path):
            print(f"  ⏭  镜{sid}: 无产物，跳过")
            skipped += 1
            continue
        # ⚠️ 契约里 source_ref 初始为 null（§2.1）。setdefault 遇显式 null 会返回
        #    游离 dict，回填不进 vis → eagle_id 静默丢失 → 每次重复入库（v3.3 潜伏 bug）。
        src = vis.get("source_ref")
        ref = src if isinstance(src, dict) else {}
        if ref is not src:
            vis["source_ref"] = ref
        # 占位图守卫（v5.3.1）：判据与 qc_checks 完全一致（visual/placeholder 或
        # source_ref.placeholder，由 generate_images 的本地 provider 写入）。
        # 占位图「不可交付」，进了 Eagle 就会被 reuse 语义检索命中 → ¥0 占位画面静默
        # 流入真实视频。默认不入库；历史已误入库的条目只警告不自动删（删除是破坏性操作）。
        is_placeholder = bool(vis.get("placeholder") or ref.get("placeholder"))
        if is_placeholder and not args.include_placeholders:
            ph_skipped += 1
            if ref.get("eagle_id"):
                print(f"  🚫 镜{sid}: 占位图历史上已误入库（{ref['eagle_id'][:8]}…），本次跳过。"
                      f"请在 Eagle 删除该条目（或对该镜跑 --profile prod 真图，eagle 会自动替换）")
            else:
                print(f"  🚫 镜{sid}: 占位图（¥0 开发档，不可交付），跳过入库"
                      f"（prod 真图重跑后会正常入库）")
            continue
        cur_hash = file_md5(path)
        if ref.get("eagle_id") and not args.refresh:
            if args.dry_run:
                print(f"  ⏭  镜{sid}: 已入库（{ref['eagle_id'][:8]}…），跳过")
                skipped += 1
                continue
            old_hash = stored_src_hash(api, ref["eagle_id"])
            if old_hash is None:
                # 历史条目无指纹（v4.0 之前入库）→ 视为未变化，跳过。
                # 误判"已变化"会把旧图白扔进回收站、还会破坏其他分镜的 eagle_id 引用。
                print(f"  ⏭  镜{sid}: 已入库（历史条目无指纹，视为未变化），跳过"
                      f"（如需刷新: --refresh）")
                skipped += 1
                continue
            if old_hash == cur_hash:
                print(f"  ⏭  镜{sid}: 已入库且未变化（{ref['eagle_id'][:8]}…），跳过")
                skipped += 1
                continue
            # 本地已重生成（素材闸「重跑」）→ 旧条目进回收站，重新入库
            if trash_item(api, ref["eagle_id"]):
                print(f"  🗑  镜{sid}: 旧条目已移入回收站（{ref['eagle_id'][:8]}…）")
            else:
                print(f"  ⚠️  镜{sid}: 旧条目 {ref['eagle_id'][:8]}… 移入回收站失败（继续重新入库）")
            ref.pop("eagle_id")

        sl = vis.get("shot_language") or {}
        tags = [t for t in list(tag_prefix) + [
            (sb.get("style") or {}).get("preset") or "",
            sl.get("shot_size") or "", sl.get("lighting") or "",
            sl.get("color_temperature") or "",
        ] if t]
        # 显式 --include-placeholders 时打标：eagle_reuse 据此排除，防止被复用回真实视频
        if is_placeholder and "placeholder" not in tags:
            tags.append("placeholder")
        name = f"{video_id}_镜{sid}"
        annotation = (vis.get("prompt") or "").strip()
        if s.get("script_line"):
            annotation = f"{annotation}\n台词：{s['script_line'].strip()}"
        if is_placeholder:
            annotation = "[placeholder]\n" + annotation
        # 入库时记录源文件哈希 → 下次比对判断"本地是否重生成过"（幂等 + 重入库闭环）
        annotation = f"{annotation}\n[src_hash:{cur_hash}]"

        if args.dry_run:
            print(f"  🔍 镜{sid}: → {folder_name}  tags={tags}  name={name}")
            ok += 1
            continue
        try:
            r = api.add_from_path(path, name=name, tags=tags,
                                  folder_id=folder_id, annotation=annotation)
            # 坑：Eagle v4 的 addFromPath 返回的 data 是**字符串**（直接就是 item id）
            #     不是对象 —— 早期版本/其他接口才是 dict，故两种都要兼容
            d = r.get("data")
            item_id = d if isinstance(d, str) else (d or {}).get("id")
            if not item_id:
                raise RuntimeError(str(r)[:150])
            ref["eagle_id"] = item_id
            ref["path"] = path
            print(f"  ✅ 镜{sid}: 已入库  id={item_id[:8]}…")
            ok += 1
        except Exception as e:
            print(f"  ❌ 镜{sid}: {type(e).__name__}: {str(e)[:120]}")
            failed += 1

    if args.update_storyboard and ok:
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
        print(f"📝 已回填 eagle_id 到分镜: {sb_path}")

    print(f"\n入库完成: 成功 {ok} / 跳过 {skipped} / 占位图拦截 {ph_skipped} / 失败 {failed}")
    if ph_skipped:
        print("ℹ️  被拦截的占位图不影响流程；prod 真图重跑对应镜后会自动入库。"
              "如确认要连占位图一起入库（仅演示用途），加 --include-placeholders")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
