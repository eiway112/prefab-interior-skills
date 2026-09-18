#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pending_ledger_test.py — 检查 7「遗留存活性台账」专项测试（第六门禁，CG-20260918-005）

口径沿 verification_policy_test.py（检查 3 专项）：
  - clean 态零 FAIL；单纯到期只 WARN＋INFO，不计 fail_count（CG-20260917-009 同构）
  - 每一类结构违法都必须能被注入并复红（「修净后的守卫须仍能失败」），
    负向注入用合成文本直调 check_pending_ledger，不落盘、不改任何治理件
  - 键闭合真值源须对 §九 跨物理行断行免疫（PL-016 守卫）
  - 另含一条对本仓真实 change-governance.md 的 clean 态断言（到期只 WARN 故不随时间转红）

用法：python -B 程序文件/pending_ledger_test.py
依赖：Python 3.8+（仅标准库）
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_governance as V  # noqa: E402

TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def d(offset: int) -> str:
    return (TODAY + timedelta(days=offset)).strftime("%Y-%m-%d")


HEADER = ("| 编号 | 事项 | 来源登记 | 登记日期 | 到期日 | 状态 | 处置批次／依据 |\n"
          "|------|------|---------|---------|--------|------|---------------|\n")


def row(pid="PL-001", item="测试事项", src="CG-20260918-005 遗留 ①",
        reg=None, due=None, status="待处置", basis="常规 TTL"):
    reg = reg if reg is not None else d(-1)
    due = due if due is not None else d(89)
    return f"| {pid} | {item} | {src} | {reg} | {due} | {status} | {basis} |\n"


def doc(rows: str, cg_rows=None, ledger=True, section=True, header=True) -> str:
    """合成一份最小 change-governance.md：§九 变更日志 ＋ §十一 台账。

    header=False 时 rows 须是自带表头＋分隔行的整表字符串（用于注入缺列/列数不符）。
    表头与数据行之间不得有空行，否则表头感知解析把数据行判为「无表头块」整块丢弃。
    """
    if cg_rows is None:
        cg_rows = ("| 变更编号 | 日期 | 级别 | 变更内容 | 影响范围 | 状态 |\n"
                   "|---------|------|------|---------|---------|------|\n"
                   "| CG-20260918-005 | 2026-09-18 | B | 测试行 | 测试 | 已实施 |\n")
    out = ["# 测试用治理文件", "", "## 九、变更日志", "", cg_rows, "## 十、其他", "", "散文", ""]
    if section:
        out += ["## 十一、遗留存活性台账（PENDING-TTL 本仓化）", ""]
        if ledger:
            block = (HEADER.rstrip("\n") + "\n" + rows.rstrip("\n")) if header else rows.rstrip("\n")
            out += [block, ""]
    out += ["> **执行优先级**：footer", ""]
    return "\n".join(out)


def run(text: str):
    rep = V.Report()
    V.check_pending_ledger(text, rep)
    items = [it for s in rep.sections for it in s["items"]]
    fails = [m for lv, m in items if lv == "FAIL"]
    warns = [m for lv, m in items if lv == "WARN"]
    infos = [m for lv, m in items if lv == "INFO"]
    oks = [m for lv, m in items if lv == "PASS"]
    return {"fail": fails, "warn": warns, "info": infos, "ok": oks,
            "fail_count": len(fails), "n": len(items)}


class TestCleanState(unittest.TestCase):
    def test_clean_ledger_zero_fail(self):
        r = run(doc(row()))
        self.assertEqual(r["fail_count"], 0, r["fail"])
        self.assertTrue(any("台账表就位" in m for m in r["ok"]))
        self.assertTrue(any("零超期" in m for m in r["ok"]))

    def test_three_status_values_all_judgeable(self):
        rows = (row("PL-001", status="待处置")
                + row("PL-002", status="已闭合", due="—", basis="CG-20260918-005")
                + row("PL-003", status="已裁定不做", due="—", basis="用户裁定不做"))
        r = run(doc(rows))
        self.assertEqual(r["fail_count"], 0, r["fail"])
        self.assertTrue(any("待处置 1 ／ 已闭合 1 ／ 已裁定不做 1" in m for m in r["ok"]))

    def test_blank_due_allowed_only_for_closed(self):
        r = run(doc(row(status="已闭合", due="—", basis="CG-20260918-005")))
        self.assertEqual(r["fail_count"], 0, r["fail"])

    def test_real_repo_ledger_is_clean(self):
        p = SCRIPT_DIR.parent / "_专题_技能合集策划" / "change-governance.md"
        self.assertTrue(p.exists(), f"真实治理文件缺失：{p}")
        r = run(p.read_text(encoding="utf-8"))
        self.assertEqual(r["fail_count"], 0, r["fail"])


class TestDueDateDisclosure(unittest.TestCase):
    def test_overdue_is_warn_not_fail(self):
        r = run(doc(row(due=d(-1))))
        self.assertEqual(r["fail_count"], 0, r["fail"])
        self.assertEqual(len(r["warn"]), 1, r["warn"])
        self.assertIn("须重新裁定", r["warn"][0])
        self.assertTrue(any("超期 PL-001" in m for m in r["info"]), r["info"])

    def test_due_today_not_overdue(self):
        r = run(doc(row(due=d(0))))
        self.assertEqual(r["fail_count"], 0, r["fail"])
        self.assertEqual(len(r["warn"]), 0, r["warn"])
        self.assertTrue(any("零超期" in m for m in r["ok"]))

    def test_due_tomorrow_overdue_boundary(self):
        r = run(doc(row(due=d(-2))))
        self.assertTrue(any("已过 2 天" in m for m in r["info"]), r["info"])

    def test_soon_window_info(self):
        r = run(doc(row(due=d(V.LEDGER_SOON_DAYS))))
        self.assertEqual(len(r["warn"]), 0, r["warn"])
        self.assertTrue(any("预警 PL-001" in m for m in r["info"]), r["info"])

    def test_beyond_soon_window_no_info(self):
        r = run(doc(row(due=d(V.LEDGER_SOON_DAYS + 1))))
        self.assertFalse(any("预警" in m for m in r["info"]), r["info"])

    def test_over_ttl_cap_is_warn_not_fail(self):
        r = run(doc(row(reg=d(0), due=d(V.LEDGER_TTL_EVENT + 20))))
        self.assertEqual(r["fail_count"], 0, r["fail"])
        self.assertEqual(len(r["warn"]), 1, r["warn"])
        self.assertIn("续期", r["warn"][0])

    def test_closed_row_overdue_not_counted(self):
        r = run(doc(row(status="已闭合", reg=d(-500), due=d(-400), basis="CG-20260918-005")))
        self.assertEqual(len(r["warn"]), 0, r["warn"])
        self.assertEqual(r["fail_count"], 0, r["fail"])


class TestStructuralFailInjection(unittest.TestCase):
    """每类结构违法都必须能复红——恒绿的守卫等于空跑。"""

    def assert_fail(self, r, keyword):
        self.assertGreater(r["fail_count"], 0, f"未复红：{r['ok']}")
        self.assertTrue(any(keyword in m for m in r["fail"]),
                        f"未见判据关键词 '{keyword}'：{r['fail']}")

    def test_missing_section(self):
        self.assert_fail(run(doc(row(), section=False)), "未找到 §十一")

    def test_missing_table(self):
        self.assert_fail(run(doc(row(), ledger=False)), "未找到台账表")

    def test_missing_header_row(self):
        self.assert_fail(run(doc(row(), header=False)), "未找到台账表")

    def test_missing_column(self):
        bad = ("| 编号 | 事项 | 登记日期 | 到期日 | 状态 | 处置批次／依据 |\n"
               "|---|---|---|---|---|---|\n"
               f"| PL-001 | x | {d(-1)} | {d(10)} | 待处置 | y |\n")
        self.assert_fail(run(doc(bad, header=False)), "缺必需列")

    def test_bad_id_shape(self):
        self.assert_fail(run(doc(row(pid="PL-1"))), "不合 PL-nnn 形制")

    def test_non_pl_id_shape(self):
        self.assert_fail(run(doc(row(pid="OBS-2"))), "不合 PL-nnn 形制")

    def test_duplicate_id(self):
        self.assert_fail(run(doc(row("PL-001") + row("PL-001"))), "编号重复")

    def test_status_out_of_enum(self):
        self.assert_fail(run(doc(row(status="处理中"))), "不在三值枚举内")

    def test_unparseable_reg_date(self):
        self.assert_fail(run(doc(row(reg="2026年09月18日"))), "登记日期")

    def test_unparseable_due_date(self):
        self.assert_fail(run(doc(row(due="下个月"))), "到期日")

    def test_invalid_calendar_date(self):
        self.assert_fail(run(doc(row(due="2026-02-30"))), "不可解析")

    def test_pending_without_due(self):
        self.assert_fail(run(doc(row(due="—"))), "到期日为空")

    def test_reg_after_due(self):
        self.assert_fail(run(doc(row(reg=d(10), due=d(5)))), "晚于到期日")

    def test_closed_without_basis(self):
        self.assert_fail(run(doc(row(status="已闭合", due="—", basis="—"))), "依据为空")

    def test_refused_without_basis(self):
        self.assert_fail(run(doc(row(status="已裁定不做", due="—", basis=""))), "依据为空")

    def test_empty_source(self):
        self.assert_fail(run(doc(row(src="—"))), "来源登记为空")

    def test_dangling_cg_in_source(self):
        self.assert_fail(run(doc(row(src="CG-19990101-001 遗留 (a)"))), "CG-19990101-001")

    def test_dangling_cg_in_basis(self):
        self.assert_fail(run(doc(row(status="已闭合", due="—", basis="CG-19990101-002"))),
                         "CG-19990101-002")

    def test_column_count_mismatch(self):
        bad = HEADER + f"| PL-001 | x | CG-20260918-005 | {d(-1)} | {d(9)} | 待处置 |\n"
        self.assert_fail(run(doc(bad, header=False)), "行列数")

    def test_no_cg_truth_source(self):
        empty_log = ("| 变更编号 | 日期 | 级别 | 变更内容 | 影响范围 | 状态 |\n"
                     "|---|---|---|---|---|---|\n")
        self.assert_fail(run(doc(row(), cg_rows=empty_log)), "真值源")


class TestKeyClosureRobustness(unittest.TestCase):
    def test_wrapped_history_row_does_not_hide_later_ids(self):
        """PL-016 守卫：§九 断行不得使其后的 CG 编号对键闭合不可见。"""
        wrapped = ("| 变更编号 | 日期 | 级别 | 变更内容 | 影响范围 | 状态 |\n"
                   "|---|---|---|---|---|---|\n"
                   "| CG-20260916-008 | 2026-09-16 | B | 长内容开头 |\n"
                   "断行续文（历史行跨物理行） |\n"
                   "| CG-20260918-005 | 2026-09-18 | B | 断点之后的行 | x | 已实施 |\n")
        lines = doc(row(), cg_rows=wrapped).splitlines()
        ids = V.collect_cg_log_ids(lines)
        self.assertIn("CG-20260918-005", ids)
        self.assertIn("CG-20260916-008", ids)
        r = run(doc(row(), cg_rows=wrapped))
        self.assertEqual(r["fail_count"], 0, r["fail"])

    def test_bold_id_cell_still_parsed(self):
        bold = ("| 变更编号 | 日期 | 级别 |\n|---|---|---|\n"
                "| **CG-20260918-005** | 2026-09-18 | B |\n")
        ids = V.collect_cg_log_ids(doc(row(), cg_rows=bold).splitlines())
        self.assertIn("CG-20260918-005", ids)

    def test_ids_outside_section_not_counted(self):
        """键闭合真值源只取 §九，散文里提到的 CG 编号不得充当存在性证据。"""
        text = doc(row(src="CG-19990101-009 遗留"))
        text = text.replace("## 十、其他\n\n散文", "## 十、其他\n\n散文提到 CG-19990101-009")
        r = run(text)
        self.assertGreater(r["fail_count"], 0)
        self.assertTrue(any("CG-19990101-009" in m for m in r["fail"]), r["fail"])


class TestConstantConsistency(unittest.TestCase):
    def test_ttl_constants_match_section_11_1(self):
        """常量与 §11.1 散文同源同值——散文口径改了而常量没改即复红。"""
        p = SCRIPT_DIR.parent / "_专题_技能合集策划" / "change-governance.md"
        t = p.read_text(encoding="utf-8")
        self.assertIn(f"＋ **{V.LEDGER_TTL_DEFAULT} 天**", t)
        self.assertIn(f"＋ **{V.LEDGER_TTL_EVENT} 天**", t)

    def test_status_enum_matches_section_11_1(self):
        p = SCRIPT_DIR.parent / "_专题_技能合集策划" / "change-governance.md"
        t = p.read_text(encoding="utf-8")
        joined = "` / `".join(V.LEDGER_STATUS_ENUM)
        self.assertIn(f"`{joined}`", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
