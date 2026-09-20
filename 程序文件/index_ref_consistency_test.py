#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
index_ref_consistency_test.py — 检查 8「技能侧索引序号引用一致性」专项测试（第八门禁，CG-20260920-004）

口径沿 pending_ledger_test.py（第六门禁）／cross_layer_eol_test.py（第七门禁）：
  - clean 态对真实仓断言：零 FAIL、判定单元 38/35/24、真漂 0、无锚不判 10 值／4 位置、豁免 E3 4＋E2 11＋E6 1
  - 每一类违法都须能被注入并复红（「修净后的守卫须仍能失败」），负向注入用合成数据面
    内存内直调 check_index_ref_consistency，不落盘、不改任何治理件与技能件
  - 控制例 C1—C6 证豁免规则（E1—E6）与多值展开（F8）均非恒真

用法：python -B 程序文件/index_ref_consistency_test.py
依赖：Python 3.8+（仅标准库）
"""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_governance as V  # noqa: E402

INDEX_L1 = SCRIPT_DIR.parent / "_专题_技能合集策划" / "standards-index.md"
SI_TEXT = INDEX_L1.read_text(encoding="utf-8")


class FakeFile:
    """内存内技能件替身：只提供 scan_carriers 用到的 read_text。"""
    def __init__(self, name, text):
        self.name = name
        self._text = text

    def read_text(self, encoding=None, **kw):
        return self._text


def F(name, text):
    return (name, FakeFile(name, text))


REAL_TRUTH = V.build_index_truth(SI_TEXT)


def run(skill_md_files=None, truth_override=None, sync_text_override=None):
    rep = V.Report()
    res = V.check_index_ref_consistency(
        None, SI_TEXT, rep,
        skill_md_files=skill_md_files, truth_override=truth_override,
        sync_text_override=sync_text_override)
    items = [it for s in rep.sections for it in s["items"]]
    return {
        "fail": [m for lv, m in items if lv == "FAIL"],
        "warn": [m for lv, m in items if lv == "WARN"],
        "info": [m for lv, m in items if lv == "INFO"],
        "ok":   [m for lv, m in items if lv == "PASS"],
        "res": res,
    }


class TestRealRepoCleanBaseline(unittest.TestCase):
    def setUp(self):
        self.r = run()

    def test_zero_fail(self):
        self.assertEqual(self.r["fail"], [], f"真实仓 clean 态不应有 FAIL：{self.r['fail']}")

    def test_nine_ok_rows(self):
        # 组 A4 ＋ B0 ＋ D1 ＋ 三载体 ＝ 9 条 [OK]（设计方案 §7.1）
        self.assertEqual(len(self.r["ok"]), 9, self.r["ok"])

    def test_carrier_counts(self):
        joined = "\n".join(self.r["ok"])
        self.assertIn("38 判定单元真漂 0", joined)   # 载体①（含 ①′ 表行内）
        self.assertIn("35 判定单元真漂 0", joined)   # 载体②
        self.assertIn("24 判定单元真漂 0", joined)   # 载体③
        self.assertEqual(sum(self.r["res"]["units"].values()), 97)

    def test_noanchor_positions(self):
        na = self.r["res"]["noanchor"]
        self.assertEqual(len(na), 10)
        self.assertEqual(len({(f, l) for f, l, _, _ in na}), 4)

    def test_exempt_counts(self):
        res = self.r["res"]
        self.assertEqual(len(res["e3"]), 4)    # F1 标准内部表行号
        self.assertEqual(res["e2"], 11)        # 原序号注记
        self.assertEqual(len(res["e6"]), 1)    # 序号44-1


class TestCarrierDrift(unittest.TestCase):
    def test_prose_carrier_drift(self):
        r = run(skill_md_files=[F("x.md", "T/CECS 1018-2022 装配式墙面 序号 44\n")])
        self.assertTrue(any("① 散文形" in m for m in r["fail"]), r["fail"])
        self.assertIn("44", str(r["res"]["drifts"]))

    def test_table_column_drift(self):
        text = "| 标准 | 索引序号 |\n|---|---|\n| GB 8624-2012 | 99 |\n"
        r = run(skill_md_files=[F("x.md", text)])
        self.assertTrue(any("② 表列形" in m for m in r["fail"]), r["fail"])
        self.assertEqual(r["res"]["drifts"][0][3], "99")

    def test_inline_drift(self):
        r = run(skill_md_files=[F("x.md", "见 standards-index T/CECS 1018-2022 索引#44\n")])
        self.assertTrue(any("③ 内联形" in m for m in r["fail"]), r["fail"])

    def test_positive_pass(self):
        # 正确序号不误报
        r = run(skill_md_files=[F("x.md", "GB 8624-2012《建筑材料及制品燃烧性能分级》序号 42\n")])
        self.assertEqual(r["res"]["drifts"], [], r["res"]["drifts"])


class TestTruthTablePreconditions(unittest.TestCase):
    def _t(self, **over):
        t = dict(REAL_TRUTH)
        t.update(over)
        return t

    def test_A1_no_main_table(self):
        r = run(truth_override=self._t(main_tables=[]))
        self.assertTrue(any("A1" in m for m in r["fail"]), r["fail"])
        self.assertTrue(any("跳过" in m for m in r["info"]))
        self.assertFalse(any("B0" in m for m in r["ok"]))

    def test_A2_duplicate_seq(self):
        r = run(truth_override=self._t(dup_seq=[(10, "GB A", "GB B")]))
        self.assertTrue(any("A2" in m for m in r["fail"]), r["fail"])

    def test_A3_non_continuous(self):
        gapped = {k: v for k, v in REAL_TRUTH["seq2code"].items() if k != 20}
        r = run(truth_override=self._t(seq2code=gapped))
        self.assertTrue(any("A3" in m for m in r["fail"]), r["fail"])

    def test_A4_non_single_not_sentinel(self):
        fake = REAL_TRUTH["codes"]  # 保留闭包
        t = self._t(non_single={"GB8624-2012": [42, 7]})
        r = run(truth_override=t)
        self.assertTrue(any("A4" in m for m in r["fail"]), r["fail"])
        self.assertTrue(callable(fake))


class TestDerivedTableB0(unittest.TestCase):
    def test_B0_mismatch(self):
        fake_table = ({"header": ["序号", "标准编号", "核验日期"],
                       "rows": [(3, ["5", "GB 9999-2099", "2026-01-01"])]}, 0, 1)
        derived = list(REAL_TRUTH["derived_tables"]) + [fake_table]
        r = run(truth_override=dict(REAL_TRUTH, derived_tables=derived))
        self.assertTrue(any("B0" in m for m in r["fail"]), r["fail"])

    def test_B0_real_is_ok(self):
        r = run()
        self.assertTrue(any("B0" in m for m in r["ok"]), r["ok"])


class TestScanFaceD1(unittest.TestCase):
    def test_missing_dir(self):
        real = V.extract_py_literals(
            (SCRIPT_DIR / "sync_skill_backup.py").read_text(encoding="utf-8"),
            ["SKILL_DIRS"])["SKILL_DIRS"]
        bad = list(real)
        bad.append("prefab-nonexistent-xyz")
        r = run(sync_text_override="SKILL_DIRS = %r" % bad)
        self.assertTrue(any("漏配" in m for m in r["fail"]), r["fail"])

    def test_extra_dir(self):
        real = V.extract_py_literals(
            (SCRIPT_DIR / "sync_skill_backup.py").read_text(encoding="utf-8"),
            ["SKILL_DIRS"])["SKILL_DIRS"]
        fewer = [d for d in real if d != "skill-qa-tester"]
        r = run(sync_text_override="SKILL_DIRS = %r" % fewer)
        self.assertTrue(any("越界" in m for m in r["fail"]), r["fail"])

    def test_clean_d1_ok(self):
        r = run()
        self.assertTrue(any("D1" in m for m in r["ok"]), r["ok"])


class TestControlCases(unittest.TestCase):
    """C1—C6：豁免规则与多值展开不得恒真（设计方案 §5.3／§10 条件 5）。"""

    def test_C1_原序号_only_exempts_原(self):
        # 保留 原序号 59（SJG 159-2024 真序号＝59），把 序号 写成 44 → 只报 44
        r = run(skill_md_files=[F("x.md", "SJG 159-2024 装配式装修评价标准 序号 44（原序号 59）\n")])
        vals = [d[3] for d in r["res"]["drifts"]]
        self.assertEqual(vals, ["44"], r["res"]["drifts"])
        self.assertGreaterEqual(r["res"]["e2"], 1)   # 原序号计入 E2 豁免
        # 注记值 59 恰等于自身锚真序号，仅靠 drifts/e2 抓不住「(?<!原) 被删」这一变异；
        # 以「① 判定单元恰 1（只序号 44，原序号 59 不计）」钉住 lookbehind，删则①升至 2 复红
        self.assertEqual(r["res"]["units"]["①"], 1,
                         "原序号 59 不得计入 ① 载体，证 (?<!原) 排除生效（非恒真）")

    def test_C2_E3_exempt_by_window_literal(self):
        # 反向：真索引引用改写成「表 5.1.1 序号 47」→ 由窗口字面豁免（47 本非 GB 50222 序号）
        r = run(skill_md_files=[F("x.md", "GB 50222-2017 表 5.1.1 序号 47\n")])
        self.assertEqual(r["res"]["drifts"], [], "E3 应豁免标准内部表行号")
        self.assertGreaterEqual(len(r["res"]["e3"]), 1)
        # 正向：把「表 5.1.1 序号」去掉窗口字面 → 须报 DRIFT（锚 GB 50222＝序号 5）
        r2 = run(skill_md_files=[F("x.md", "GB 50222-2017 索引序号 17\n")])
        self.assertEqual([d[3] for d in r2["res"]["drifts"]], ["17"],
                         "去掉表行号字面后 17 应判 DRIFT（证豁免由窗口字面驱动，非恒真）")

    def test_C3_no_anchor_to_drift(self):
        # 无编号 → NO-ANCHOR
        r = run(skill_md_files=[F("x.md", "本表 序号 44 说明\n")])
        self.assertEqual(r["res"]["drifts"], [])
        self.assertTrue(any(v == "44" for _, _, _, v in r["res"]["noanchor"]))
        # 补入真实编号且去掉连写后缀 → 由 NO-ANCHOR 转 DRIFT
        r2 = run(skill_md_files=[F("x.md", "GB 8624-2012 序号 44\n")])
        self.assertEqual([d[3] for d in r2["res"]["drifts"]], ["44"])

    def test_C4_member_criterion_catches_outside(self):
        # 锚集扩大（两编号）但值落在集外 → 仍报 DRIFT
        r = run(skill_md_files=[F("x.md", "GB 8624-2012 与 T/CECS 1018-2022 序号 99\n")])
        self.assertEqual([d[3] for d in r["res"]["drifts"]], ["99"])
        # 落在集内 → PASS（成员判据，不指定唯一配对）
        r2 = run(skill_md_files=[F("x.md", "GB 8624-2012 与 T/CECS 1018-2022 序号 31\n")])
        self.assertEqual(r2["res"]["drifts"], [])

    def test_C5_scan_face_failures(self):
        TestScanFaceD1.test_missing_dir(self)
        TestScanFaceD1.test_extra_dir(self)

    def test_C6_multivalue_has_teeth_and_E6_brake(self):
        # ① 多值并列，只第 2 值错 → 1 条 DRIFT（旧「只判首值」缺陷下会静默通过）
        r = run(skill_md_files=[F("x.md", "GB 55037-2022 序号 2、99\n")])
        self.assertEqual([d[3] for d in r["res"]["drifts"]], ["99"], r["res"]["drifts"])
        # ② 只第 1 值错 → 1 条 DRIFT
        r2 = run(skill_md_files=[F("x.md", "GB 50222-2017 序号 99、5\n")])
        self.assertEqual([d[3] for d in r2["res"]["drifts"]], ["99"])
        # ③ 条目号连写 44-1 → 落 EXEMPT（E6），不得拆成两值各判
        r3 = run(skill_md_files=[F("x.md", "注意子条目 序号44-1 的计数方式\n")])
        self.assertEqual(r3["res"]["drifts"], [])
        self.assertGreaterEqual(len(r3["res"]["e6"]), 1)
        self.assertFalse(any(v in ("44", "1") for _, _, _, v in r3["res"]["noanchor"]))


class TestExpansionAndNormalization(unittest.TestCase):
    def test_parallel_and_range_expand(self):
        # 并列 31/42 全进判据；升序区间 40-42 展开为三值
        r = run(skill_md_files=[F("x.md", "GB/T 23451-2023、GB/T 51129-2017、GB 8624-2012 序号 40-42\n")])
        self.assertEqual(r["res"]["drifts"], [], r["res"]["drifts"])
        self.assertGreaterEqual(r["res"]["units"]["①"], 3)

    def test_F6_longest_match(self):
        # JGJ/T 491-2021 不被通用正则切坏；序号 19 正确
        r = run(skill_md_files=[F("x.md", "JGJ/T 491-2021 装配式内装修技术标准 序号 19\n")])
        self.assertEqual(r["res"]["drifts"], [], r["res"]["drifts"])
        r2 = run(skill_md_files=[F("x.md", "JGJ/T 491-2021 序号 20\n")])
        self.assertEqual([d[3] for d in r2["res"]["drifts"]], ["20"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
