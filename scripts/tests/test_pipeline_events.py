#!/usr/bin/env python3
"""跨仓事件契约与退出码的子进程测：跑真 run_pipeline，但不花钱、不依赖任何在跑的服务。

跑法（任选一）：
    .venv-pyjd/bin/python scripts/tests/test_pipeline_events.py
    .venv-pyjd/bin/python -m unittest discover -s scripts/tests -t scripts/tests

为什么用子进程而不是 import：要钉的就是**引擎真实打出来的 stdout**——面板执行器
逐行读的就是这份字节流，import 进来调函数测不到 print 的形状，也测不到退出码。

为什么不花钱 / 不需要服务：
  - 三道闸都在任何花钱阶段**之前**判，所以停在闸上的那次运行一个子阶段都没跑；
  - 不传 --video-id 时 report() 直接 no-op，零网络；
  - 内容中心一律指向一个**测试自己起的**一次性 stub（端口 0，内核分配，不会撞端口）
    或直接指向 refused 端口，不碰真实的 :3002 / PocketBase / Eagle；
  - HOME 换到临时目录，避免机器上已有的类型目录缓存与回写密钥影响结论。

覆盖的是今天刚立的三件事：manual 缺 --gate 退回三闸全停（#8）、事件行形状是契约
（#4）、回写 401/403 立即停而网络类失败继续跑（#6）。
"""
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
REPO = os.path.dirname(SCRIPTS)
VENV_PY = os.path.join(REPO, ".venv-pyjd", "bin", "python")
RUN = os.path.join(SCRIPTS, "run_pipeline.py")
PREFIX = "#VIDEO-EVENT# "
# loopback 上没人监听的端口：connect 立刻 refused，属「临时不通」而非「被拒」
DEAD_BASE = "http://127.0.0.1:1/api/v1"

GOOD_SB = {
    "project_id": "p-test",
    "platform": "douyin",
    "aspect_ratio": "9:16",
    "content_type": "koubo",
    "shots": [{
        "shot_id": 1,
        "script_line": "这是一句够长的测试台词，用来过契约校验。",
        "visual": {
            "prompt": "书桌与台灯",
            "shot_language": {"shot_size": "中景", "focal_length": "35mm", "depth_of_field": "浅景深",
                              "lighting": "暖光", "color_temperature": "暖", "camera_movement": "固定"},
        },
    }],
}


class Reject401(http.server.BaseHTTPRequestHandler):
    """替代内容中心：所有请求都按「token 不匹配」拒——正是 #6 要快停的那一类。"""

    def do_GET(self):
        self.send_response(401)
        self.end_headers()
        self.wfile.write(b'{"success":false}')

    def do_POST(self):
        body = b'{"success":false,"error":"callback token mismatch"}'
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class EngineCase(unittest.TestCase):
    """公共脚手架：临时 HOME（无缓存无密钥）+ 临时产物目录 + 事件行解析。"""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pipeline-events-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.home = os.path.join(self.root, "home")
        os.makedirs(self.home)
        self.sb_path = self._dump("storyboard.json", GOOD_SB)

    def _dump(self, name, obj):
        p = os.path.join(self.root, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return p

    def run_engine(self, extra=(), base=DEAD_BASE, sb=None, video_id=None, out="out"):
        argv = [VENV_PY if os.path.exists(VENV_PY) else sys.executable, RUN,
                "--storyboard", sb or self.sb_path,
                "--out-dir", os.path.join(self.root, out),
                "--profile", "test"]
        if video_id:
            argv += ["--video-id", video_id]
        argv += list(extra)
        env = dict(os.environ, HOME=self.home, CONTENT_OPS_API_BASE=base,
                   VIDEO_COST_LOG=os.path.join(self.root, ".cost.jsonl"))
        for k in ("VIDEO_CALLBACK_TOKEN", "CONTENT_OPS_API_TOKEN", "AGENT_API_KEY", "VIDEO_RECORD_ID"):
            env.pop(k, None)
        r = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=180)
        events = [json.loads(ln[len(PREFIX):]) for ln in r.stdout.splitlines()
                  if ln.startswith(PREFIX)]
        return r, events

    def names(self, events):
        return [e["event"] for e in events]


class TestGateStopContract(EngineCase):
    def test_manual_without_gate_stops_at_first_gate_before_any_stage(self):
        r, ev = self.run_engine()  # 不带 --gate、不带 --video-id
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.names(ev), ["gate_pause"])
        g = ev[0]
        self.assertEqual((g["gate"], g["reason"]), ("script", "unapproved"))
        # 关键：一个阶段都没起跑 = 这次运行没有理由产生任何费用
        self.assertNotIn("stage_start", self.names(ev))

    def test_gate_pause_event_carries_exactly_the_documented_fields(self):
        # 面板按这些字段名解析；改名就是破坏契约，这条会先红
        _, ev = self.run_engine()
        g = ev[0]
        self.assertEqual(set(g), {"v", "event", "gate", "reason", "review"})
        self.assertEqual(g["v"], 1)
        self.assertTrue(g["review"].endswith(os.path.join("review", "script.md")), g["review"])

    def test_review_file_is_written_for_the_human(self):
        _, ev = self.run_engine()
        self.assertTrue(os.path.exists(ev[0]["review"]))


class TestExitCodes(EngineCase):
    def test_non_koubo_without_catalog_rules_exits_6_and_runs_nothing(self):
        # 拿不到类型规则还按口播全阶段跑 = 给混剪白烧配音与生图（#3）
        r, ev = self.run_engine(extra=["--content-type", "mixcut"])
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertEqual(ev, [])

    def test_invalid_storyboard_emits_stage_start_then_stage_failed(self):
        bad = self._dump("bad.json", {"shots": [{"shot_id": 1, "script_line": "缺项目缺比例"}],
                                      "content_type": "koubo"})
        r, ev = self.run_engine(extra=["--only", "validate"], sb=bad)
        self.assertEqual(self.names(ev), ["stage_start", "stage_failed"])
        start, fail = ev
        self.assertEqual((start["stage"], start["index"], start["total"]), ("validate", 1, 13))
        self.assertTrue(start["cn"])
        self.assertEqual((fail["stage"], fail["rc"]), ("validate", 1))
        self.assertTrue(fail["error"])
        self.assertEqual(r.returncode, 1)


class TestCallbackFailFast(EngineCase):
    def test_rejected_callback_stops_with_exit_7_after_the_gate_event(self):
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Reject401)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)  # 先 shutdown 再关监听 socket，别留 fd
        self.addCleanup(srv.shutdown)
        base = "http://127.0.0.1:%d/api/v1" % srv.server_address[1]
        r, ev = self.run_engine(base=base, video_id="stubrecord000001")
        self.assertEqual(r.returncode, 7, r.stdout + r.stderr)
        # 顺序本身就是断言：先承认停在闸上（本地事实），再报回写被拒
        self.assertEqual(self.names(ev), ["gate_pause", "callback_rejected"])
        self.assertEqual((ev[1]["stage"], ev[1]["http"]), ("gate_script", 401))

    def test_transient_callback_failure_continues_to_the_gate(self):
        # 中心不通（refused）≠ 被拒：不该因为追踪器抖动就掐掉一次正经运行
        r, ev = self.run_engine(video_id="stubrecord000001")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.names(ev), ["gate_pause"])
        self.assertNotIn("callback_rejected", self.names(ev))
        self.assertIn("进度回写不通", r.stderr)


class TestPrefixGuard(EngineCase):
    def test_event_prefix_and_manual_gates_constants(self):
        # 面板里写死了同一个前缀字符串；这里钉住引擎侧不再漂
        sys.path.insert(0, SCRIPTS)
        import run_pipeline
        self.assertEqual(run_pipeline.EVENT_PREFIX, PREFIX)
        self.assertEqual(run_pipeline.MANUAL_GATES, ["script", "storyboard", "images"])
        self.assertEqual(run_pipeline.EXIT_CALLBACK_REJECTED, 7)

    def test_stop_events_are_emitted_before_the_callback(self):
        # 「停在闸上」必须先于回写：中心抖动不该把这条本地事实一起吞掉。
        # 停闸点固定两处（未批 / 批过但内容或审阅文件变了），少一处说明有人动了它
        with open(RUN, encoding="utf-8") as f:
            src = f.read()
        sites = re.findall(r'contract\("gate_pause"[\s\S]{0,260}?sys\.exit\(0\)', src)
        self.assertEqual(len(sites), 2, f"闸停点应有 2 处，实到 {len(sites)}")
        for block in sites:
            self.assertIn("report(", block)
            self.assertLess(block.index("contract("), block.index("report("),
                            "gate_pause 事件应排在 report() 之前")


if __name__ == "__main__":
    unittest.main(verbosity=2)
