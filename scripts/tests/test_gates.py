#!/usr/bin/env python3
"""人工确认闸的纯函数单测：只读写临时目录，不联网、不起内容中心、不花钱。

跑法（任选一）：
    .venv-pyjd/bin/python scripts/tests/test_gates.py
    .venv-pyjd/bin/python -m unittest discover -s scripts/tests -t scripts/tests

为什么要单独钉这套：闸是「花钱之前必须人点头」的唯一一道语义边界，而它的行为
散在指纹、mtime、md 解析三处，改任何一个字段选择都可能把「正常断点续跑」误判成
「批准后有人改过分镜」（每次都被重新停闸），或者反过来把真改动放过去。
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gates  # noqa: E402


def sb_two_shots():
    return {
        "project_id": "p1",
        "shots": [
            {"shot_id": 1, "script_line": "第一句台词",
             "visual": {"prompt": "书桌与台灯",
                        "shot_language": {"shot_size": "中景", "focal_length": "35mm",
                                          "depth_of_field": "浅景深", "lighting": "暖光",
                                          "color_temperature": "暖", "camera_movement": "固定"}}},
            {"shot_id": 2, "script_line": "第二句台词",
             "visual": {"prompt": "摊开的旧书",
                        "shot_language": {"shot_size": "特写", "focal_length": "50mm",
                                          "depth_of_field": "浅景深", "lighting": "窗光",
                                          "color_temperature": "中性", "camera_movement": "下摇"}}},
        ],
    }


class GateCase(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp(prefix="gate-test-")
        self.addCleanup(shutil.rmtree, self.out, True)

    def write(self, gate, text):
        gates.ensure_review_dir(self.out)
        p = gates.review_path(self.out, gate)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def set_times(self, path, mtime):
        os.utime(path, (mtime, mtime))


class TestDigest(GateCase):
    """指纹只覆盖「人在该闸真正审过的字段」，机器回填不得影响它。"""

    def test_script_gate_ignores_visual_and_machine_fields(self):
        base = sb_two_shots()
        d0 = gates.gate_digest("script", base)
        changed = sb_two_shots()
        # 改画面描述不是台词闸的审查对象
        changed["shots"][0]["visual"]["prompt"] = "换成完全不同的画面"
        self.assertEqual(d0, gates.gate_digest("script", changed))
        # 配音回填的实测时长同样是机器写的
        changed["shots"][1]["duration_sec_actual"] = 7.31
        self.assertEqual(d0, gates.gate_digest("script", changed))

    def test_script_gate_detects_line_edit(self):
        base = sb_two_shots()
        changed = sb_two_shots()
        changed["shots"][1]["script_line"] = "第二句被人改过了"
        self.assertNotEqual(gates.gate_digest("script", base),
                            gates.gate_digest("script", changed))

    def test_storyboard_gate_ignores_image_backfill(self):
        base = sb_two_shots()
        d0 = gates.gate_digest("storyboard", base)
        after_images = sb_two_shots()
        # generate_images 会给每镜回填 source_ref.path —— 这是机器在改分镜
        for s in after_images["shots"]:
            s["source_ref"] = {"path": "/tmp/shot.jpg", "provider": "placeholder"}
        self.assertEqual(d0, gates.gate_digest("storyboard", after_images))

    def test_storyboard_gate_detects_prompt_and_shot_language(self):
        base = sb_two_shots()
        d0 = gates.gate_digest("storyboard", base)
        for mut in (
            lambda sb: sb["shots"][0]["visual"].__setitem__("prompt", "改画面"),
            lambda sb: sb["shots"][0]["visual"]["shot_language"].__setitem__("shot_size", "远景"),
        ):
            changed = sb_two_shots()
            mut(changed)
            self.assertNotEqual(d0, gates.gate_digest("storyboard", changed))

    def test_storyboard_gate_is_order_sensitive_for_shot_language_keys(self):
        # json.dumps(sort_keys=True)：键顺序不该造成假「内容变了」
        a = {"shots": [{"shot_id": 1, "visual": {"prompt": "p", "shot_language":
                                                 {"shot_size": "中景", "focal_length": "35mm"}}}]}
        b = {"shots": [{"shot_id": 1, "visual": {"prompt": "p", "shot_language":
                                                 {"focal_length": "35mm", "shot_size": "中景"}}}]}
        self.assertEqual(gates.gate_digest("storyboard", a), gates.gate_digest("storyboard", b))

    def test_images_gate_covers_prompt_and_path(self):
        base = sb_two_shots()
        d0 = gates.gate_digest("images", base)
        new_path = sb_two_shots()
        new_path["shots"][0].setdefault("source_ref", {})["path"] = "/tmp/shot_001.jpg"
        self.assertNotEqual(d0, gates.gate_digest("images", new_path))

    def test_empty_storyboard_does_not_crash(self):
        for sb in (None, {}, {"shots": None}):
            self.assertEqual(len(gates.gate_digest("script", sb)), 16)


class TestApprovalState(GateCase):
    def test_no_marker_means_not_approved(self):
        self.assertFalse(gates.is_approved(self.out, "script", sb_two_shots()))

    def test_mark_approved_records_digest(self):
        sb = sb_two_shots()
        p = gates.mark_approved(self.out, "script", sb)
        with open(p, encoding="utf-8") as f:
            content = f.read()
        self.assertIn(f"digest={gates.gate_digest('script', sb)}", content)
        self.assertIn("at=", content)
        self.assertTrue(gates.is_approved(self.out, "script", sb))

    def test_content_change_after_approval_reopens_gate(self):
        sb = sb_two_shots()
        gates.mark_approved(self.out, "script", sb)
        sb["shots"][0]["script_line"] = "批准之后又改了台词"
        self.assertFalse(gates.is_approved(self.out, "script", sb))

    def test_machine_backfill_after_approval_keeps_gate_closed(self):
        # 批准台词 → 配音回填时长 → 复跑不该被重新拦
        sb = sb_two_shots()
        gates.mark_approved(self.out, "script", sb)
        sb["shots"][0]["duration_sec_actual"] = 4.2
        self.assertTrue(gates.is_approved(self.out, "script", sb))

    def test_legacy_marker_without_digest_is_still_honored(self):
        # 补丁落地那天不能把在途任务集体重新停闸
        gates.ensure_review_dir(self.out)
        with open(gates.approved_path(self.out, "script"), "w", encoding="utf-8") as f:
            f.write("approved\n")
        self.assertTrue(gates.is_approved(self.out, "script", sb_two_shots()))

    def test_bare_marker_is_the_no_storyboard_path(self):
        gates.mark_approved(self.out, "storyboard")
        self.assertTrue(gates.is_approved(self.out, "storyboard"))
        self.assertTrue(gates.is_approved(self.out, "storyboard", sb_two_shots()))

    def test_unreadable_marker_is_not_approved(self):
        gates.ensure_review_dir(self.out)
        # 同名目录顶掉标记文件：读必失败，宁可当作未批准也不放行
        os.makedirs(gates.approved_path(self.out, "script"))
        self.assertFalse(gates.is_approved(self.out, "script", sb_two_shots()))


class TestReviewTouched(GateCase):
    def test_edit_after_approval_is_reported(self):
        rp = self.write("script", "## 镜 1\n第一句台词\n")
        ap = gates.mark_approved(self.out, "script", sb_two_shots())
        self.set_times(ap, 1_000_000)
        self.set_times(rp, 2_000_000)
        self.assertTrue(gates.review_touched_after_approval(self.out, "script"))

    def test_approval_after_edit_is_consumed(self):
        rp = self.write("script", "## 镜 1\n第一句台词\n")
        ap = gates.mark_approved(self.out, "script", sb_two_shots())
        self.set_times(ap, 2_000_000)
        self.set_times(rp, 1_000_000)
        self.assertFalse(gates.review_touched_after_approval(self.out, "script"))

    def test_missing_files_are_silent(self):
        self.assertFalse(gates.review_touched_after_approval(self.out, "script"))


class TestGateOrdering(GateCase):
    def test_remaining_gates(self):
        self.assertEqual(gates.remaining_gates("script"), "storyboard,images")
        self.assertEqual(gates.remaining_gates("storyboard"), "images")
        self.assertEqual(gates.remaining_gates("images"), "")
        self.assertEqual(gates.remaining_gates("nonsense"), "")

    def test_engine_manual_default_matches_gate_order(self):
        # 引擎里另写了一份 MANUAL_GATES，漂了就会「批准闸门后不停后面的闸」
        import run_pipeline
        self.assertEqual(run_pipeline.MANUAL_GATES, gates.GATE_ORDER)
        self.assertEqual(gates.GATES, gates.GATE_ORDER)


class TestApplyReview(GateCase):
    """人改 md → 回写分镜。这一段决定「批准后到底应用了什么」。"""

    def test_script_edit_writes_back_line_and_audio(self):
        self.write("script", "## 镜 1\n改过的第一句\n\n## 镜 2\n第二句台词\n")
        sb, changes, regen, fb = gates.apply_review(self.out, "script", sb_two_shots())
        self.assertEqual(sb["shots"][0]["script_line"], "改过的第一句")
        self.assertEqual(sb["shots"][0]["audio"]["text"], "改过的第一句")
        self.assertEqual(changes, ["镜1 台词已更新"])
        self.assertEqual((regen, fb), ([], []))

    def test_feedback_lines_are_not_applied_as_dialogue(self):
        self.write("script", "## 镜 1\n第一句台词\n意见: 这句太书面\n")
        sb, changes, regen, fb = gates.apply_review(self.out, "script", sb_two_shots())
        self.assertEqual(changes, [])
        self.assertEqual(fb, [{"target": "shot-1", "text": "这句太书面"}])
        self.assertEqual(sb["shots"][0]["script_line"], "第一句台词")

    def test_storyboard_edit_updates_prompt_and_six_shot_fields(self):
        self.write("storyboard",
                   "## 镜 1\n第一句台词\n\n画面: 新的画面描述\n"
                   "镜头: 远景/24mm/深景深/顶光/冷/推镜\n")
        sb, changes, _, _ = gates.apply_review(self.out, "storyboard", sb_two_shots())
        vis = sb["shots"][0]["visual"]
        self.assertEqual(vis["prompt"], "新的画面描述")
        self.assertEqual(vis["shot_language"]["shot_size"], "远景")
        self.assertEqual(vis["shot_language"]["camera_movement"], "推镜")
        self.assertEqual(changes, ["镜1 画面描述已更新"])

    def test_storyboard_partial_shot_language_does_not_clobber(self):
        # 镜头行字段数不是 6 → 整行忽略，不能把剩下的字段清空
        self.write("storyboard", "## 镜 1\n第一句台词\n\n镜头: 远景/24mm\n")
        sb, _, _, _ = gates.apply_review(self.out, "storyboard", sb_two_shots())
        self.assertEqual(sb["shots"][0]["visual"]["shot_language"]["lighting"], "暖光")

    def test_images_verdict_rerun_selects_shot_and_clears_hash(self):
        sb = sb_two_shots()
        for s in sb["shots"]:
            s["visual"]["source_hash"] = "deadbeef"
        self.write("images", "## 镜 1\n第一句台词\n\n画面: 书桌与台灯\n结论: 通过\n\n"
                             "## 镜 2\n第二句台词\n\n画面: 摊开的旧书\n结论: 重跑\n")
        sb, _, regen, _ = gates.apply_review(self.out, "images", sb)
        self.assertEqual(regen, [2])
        self.assertIsNone(sb["shots"][1]["visual"].get("source_hash"))
        self.assertEqual(sb["shots"][0]["visual"]["source_hash"], "deadbeef")

    def test_missing_review_file_is_noop(self):
        sb, changes, regen, fb = gates.apply_review(self.out, "script", sb_two_shots())
        self.assertEqual((changes, regen, fb), ([], [], []))

    def test_unedited_generated_review_round_trips_to_nothing(self):
        # write_review 刚生成的文件原样喂回 apply_review 不该产生任何改动
        # （只测 script 闸：storyboard/images 的成本尾注会去读项目配置，那是要联网的）
        sb = sb_two_shots()
        p = gates.write_review(self.out, "script", sb, feedback=[])
        self.assertTrue(os.path.exists(p))
        _, changes, regen, fb = gates.apply_review(self.out, "script", sb)
        self.assertEqual((changes, regen, fb), ([], [], []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
