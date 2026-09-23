#!/usr/bin/env python3
"""
声音克隆工具化（v4.0 P2-3）——把 ad-hoc 的克隆流程固化为一条命令。

流程（阿里百炼 CosyVoice 复刻）：
  ① 干声体检（时长 10s~5min、可解码）
  ② 上传公网（复刻要求公网 URL；用自家服务器随机名 + 用完即删，见 §27.3）
  ③ VoiceEnrollmentService.create_voice 复刻 → voice_id
  ④ 试听验证（T2A 合成一句，确认音色可用）
  ⑤ 登记 voice_config.json + 项目配置 tts._alternatives（可选 --write-config）

用法：
  clone_voice.py --audio 武安封号.wav --name panduola-narrator \
      [--model cosyvoice-v3.5-flash] [--project panduola] [--dry-run]

依赖：
  - dashscope SDK（.venv-pyjd 已装）
  - ~/.dsh/secrets/dashscope.env（DASHSCOPE_API_KEY / DASHSCOPE_HOST）
  - 公网托管：~/.dsh/secrets/dashscope.env 里配 VOICE_UPLOAD_SSH=my-server 与
    VOICE_UPLOAD_DIR=/var/www/yiwenai、VOICE_UPLOAD_BASE=https://yiwenai.online
    （或用 --upload-ssh/--upload-dir/--upload-base 覆盖）

⚠️ 复刻单价约 ¥0.01/音色；target_model 必须与合成 model 完全一致（§28.4 铁律）。
"""
import argparse
import json
import os
import secrets
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_DS_ENV = os.path.expanduser("~/.dsh/secrets/dashscope.env")
_VOICE_CONFIG = os.path.expanduser("~/Movies/AI视频素材/panduola/voice/voice_config.json")

MIN_SEC, MAX_SEC = 10, 300


def read_secret(key, default=None):
    if os.environ.get(key):
        return os.environ[key]
    if os.path.exists(_DS_ENV):
        for line in open(_DS_ENV, encoding="utf-8"):
            line = line.strip()
            if line.startswith(f"export {key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


def probe_audio(path):
    """ffmpeg 探测时长/声道；返回 (秒, 信息 dict) 或抛错"""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
         "-show_streams", path],
        capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe 失败（文件损坏或格式不支持）: {r.stderr[:120]}")
    info = json.loads(r.stdout)
    dur = float(info.get("format", {}).get("duration", 0))
    if dur < MIN_SEC or dur > MAX_SEC:
        raise RuntimeError(f"时长 {dur:.1f}s 不在 {MIN_SEC}~{MAX_SEC}s 范围（CosyVoice 要求 10s~5min）")
    a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    return dur, {"codec": a.get("codec_name") if a else "?",
                 "channels": a.get("channels") if a else 0,
                 "sample_rate": a.get("sample_rate") if a else "?"}


def upload_public(path, ssh_host, remote_dir, base_url):
    """scp 到自家服务器随机名 → 返回公网 URL（调用方负责用完删除）"""
    ext = os.path.splitext(path)[1].lower() or ".wav"
    name = f"vc-{secrets.token_hex(8)}{ext}"
    remote = f"{ssh_host}:{remote_dir.rstrip('/')}/{name}"
    subprocess.run(["scp", "-q", path, remote], check=True, timeout=120)
    url = f"{base_url.rstrip('/')}/{name}"
    return url, name


def delete_public(ssh_host, remote_dir, name):
    try:
        subprocess.run(["ssh", ssh_host, "rm", "-f",
                        f"{remote_dir.rstrip('/')}/{name}"],
                       check=False, timeout=30)
    except Exception as e:
        print(f"⚠️  远端清理失败（请手动删除）: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="声音克隆（百炼 CosyVoice 复刻工具化）")
    ap.add_argument("--audio", required=True, help="干声文件（10s~5min，无 BGM）")
    ap.add_argument("--name", required=True, help="音色前缀（字母数字，≤10 字符，如 panduola）")
    ap.add_argument("--model", default="cosyvoice-v3.5-flash",
                    help="target_model（必须与后续合成 model 一致；默认 cosyvoice-v3.5-flash）")
    ap.add_argument("--language", default=["zh", "en"], nargs="*",
                    help="语言提示（默认 zh en）")
    ap.add_argument("--sample-text", default="你好，这是一段音色试听验证。",
                    help="复刻后的试听文本")
    ap.add_argument("--project", help="写入项目配置 tts._alternatives（可选）")
    ap.add_argument("--upload-ssh", default=None, help="覆盖上传 ssh 主机（默认 my-server）")
    ap.add_argument("--upload-dir", default=None, help="覆盖上传目录（默认 /var/www/yiwenai）")
    ap.add_argument("--upload-base", default=None, help="覆盖公网 base（默认 https://yiwenai.online）")
    ap.add_argument("--dry-run", action="store_true", help="只体检不实际复刻")
    args = ap.parse_args()

    audio = os.path.abspath(os.path.expanduser(args.audio))
    if not os.path.exists(audio):
        print(f"❌ 音频不存在: {audio}", file=sys.stderr)
        return 1

    # ① 体检
    dur, info = probe_audio(audio)
    print(f"🎙️  干声体检: {dur:.1f}s codec={info['codec']} ch={info['channels']} "
          f"sr={info['sample_rate']} ✅")

    prefix = "".join(c for c in args.name if c.isalnum())[:10]
    if not prefix:
        print("❌ name 必须含字母/数字", file=sys.stderr)
        return 1

    ssh_host = args.upload_ssh or read_secret("VOICE_UPLOAD_SSH", "my-server")
    remote_dir = args.upload_dir or read_secret("VOICE_UPLOAD_DIR", "/var/www/yiwenai")
    base_url = args.upload_base or read_secret("VOICE_UPLOAD_BASE", "https://yiwenai.online")

    if args.dry_run:
        print(f"🔍 dry-run: 将以 model={args.model} prefix={prefix} 复刻 "
              f"（上传 {ssh_host}:{remote_dir} → {base_url}）")
        return 0

    # ② 上传公网
    print(f"⬆️  上传公网（{ssh_host}:{remote_dir}，随机名，用完即删）…")
    url, remote_name = upload_public(audio, ssh_host, remote_dir, base_url)
    print(f"    URL: {url}")
    try:
        # ③ 复刻
        key = read_secret("DASHSCOPE_API_KEY")
        host = read_secret("DASHSCOPE_HOST", "dashscope.aliyuncs.com")
        if not key:
            print("❌ 未配置 DASHSCOPE_API_KEY（~/.dsh/secrets/dashscope.env）", file=sys.stderr)
            return 1
        import dashscope
        from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer
        dashscope.api_key = key
        # 自定义业务空间域名（若配置）；复刻走 HTTP，合成走 WebSocket，都指到同一 host
        if host and host != "dashscope.aliyuncs.com":
            dashscope.base_http_api_url = f"https://{host}/api/v1"
            dashscope.base_websocket_api_url = f"wss://{host}/api-ws/v1/inference"
        ve = VoiceEnrollmentService(api_key=key)
        print(f"🧬 复刻中（target_model={args.model} prefix={prefix}）…")
        voice_id = ve.create_voice(
            target_model=args.model, prefix=prefix, url=url,
            language_hints=args.language)
        print(f"✅ 复刻成功 voice_id: {voice_id}")

        # ④ 试听验证
        from providers import tts_dashscope  # 复用合成通道（同源协议分派）
        audio_bytes, dur2 = tts_dashscope(args.sample_text, voice_id,
                                          model=args.model)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.write(audio_bytes)
        tmp.close()
        print(f"🎧 试听已生成: {tmp.name}（{dur2:.2f}s）——请试听确认音色")
    finally:
        # ⑤ 清理公网文件（立即删，不留在服务器）
        delete_public(ssh_host, remote_dir, remote_name)
        print("🧹 公网临时文件已删除")

    # ⑥ 登记
    entry = {"voice_id": voice_id, "model": args.model, "source": os.path.basename(audio),
             "created": __import__("datetime").date.today().isoformat()}
    cfg = {}
    if os.path.exists(_VOICE_CONFIG):
        try:
            cfg = json.load(open(_VOICE_CONFIG, encoding="utf-8"))
        except Exception:
            cfg = {}
    cfg[prefix] = entry
    os.makedirs(os.path.dirname(_VOICE_CONFIG), exist_ok=True)
    json.dump(cfg, open(_VOICE_CONFIG, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"📝 已登记 {_VOICE_CONFIG}")

    # ⑦ 写项目配置备选（可选）
    if args.project:
        pc = os.path.join(_HERE, "project_configs", f"{args.project}.json")
        if os.path.exists(pc):
            p = json.load(open(pc, encoding="utf-8"))
            alts = p.setdefault("tts", {}).setdefault("_alternatives", {})
            alts["克隆音色"] = {"model": args.model, "voice_id": voice_id}
            json.dump(p, open(pc, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"📝 已写入项目配置 {pc}（tts._alternatives.克隆音色）")
        else:
            print(f"⚠️  项目配置不存在，跳过: {pc}", file=sys.stderr)

    print("\n用法：")
    print(f"  run_pipeline.py ... --tts-provider dashscope --model {args.model} "
          f"--voice-id {voice_id}")
    print("  或写入项目配置 tts.model/tts.voice_id 后零参数运行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
