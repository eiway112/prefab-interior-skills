"""
SRE Reasoner 回归测试集
========================
版本：v1.2（2026-08-13）
运行：python sre_regression_test.py

覆盖：M1 分类协议、M3 场景推理与 Step 1a 裁定、M4 适用性裁判、M6 降级、
      IC-10 Response v1.5.8 Schema、SR 引擎化红线。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sre_reasoner import reason, classify_standard, _evidence_counter


class TestM1Classification(unittest.TestCase):
    """M1 编号前缀分类协议。"""

    def _classify(self, std_no: str) -> dict:
        ev = []
        return classify_standard(std_no, ev)

    def test_gb_55xxx_is_l1_redline(self):
        r = self._classify("GB 55038-2025")
        self.assertEqual(r["标准类型"], "全文强制性国标")
        self.assertEqual(r["层级"], "L1")
        self.assertEqual(r["权限"], "red_line")

    def test_gb_t_is_l2_binding(self):
        r = self._classify("GB/T 50121-2005")
        self.assertEqual(r["层级"], "L2")
        self.assertEqual(r["权限"], "binding_support")

    def test_db_is_local(self):
        r = self._classify("DB33/T 1168-2019")
        self.assertEqual(r["层级"], "L3")
        self.assertEqual(r["地域范围"], "浙江")

    def test_t_group_is_l4_reference(self):
        r = self._classify("T/CSUS 40-2022")
        self.assertEqual(r["层级"], "L4")
        self.assertEqual(r["权限"], "reference")

    def test_unknown_prefix_degrades(self):
        r = self._classify("XYZ 123-2024")
        self.assertEqual(r["分类置信度"], "inferred")
        self.assertEqual(r["权限"], "reference")


class TestM3ScenarioReasoning(unittest.TestCase):
    """M3 场景→领域→标准族推理链。"""

    def test_residential_partition_wall_default(self):
        r = reason("住宅", "分户墙")
        stds = [s["标准编号"] for s in r["适用标准集"]]
        self.assertIn("GB 55038-2025", stds)
        self.assertIn("GB 55037-2022", stds)
        self.assertIn("GB 50210-2018", stds)

    def _extract_domains(self, reasoning_path: str) -> list[str]:
        start = reasoning_path.find("激活域(") + len("激活域(")
        depth = 1
        end = start
        while end < len(reasoning_path) and depth > 0:
            if reasoning_path[end] == "(":
                depth += 1
            elif reasoning_path[end] == ")":
                depth -= 1
            end += 1
        return reasoning_path[start:end - 1].split(", ")

    def test_hotel_guest_room_ceiling_filter_acoustic(self):
        # 显式不含隔声：acoustic(贡献) 应被过滤
        r = reason("酒店", "客房吊顶", demands=["防火", "验收"])
        domains = self._extract_domains(r["推理路径"])
        self.assertNotIn("acoustic(贡献)", domains)

    def test_residential_ceiling_augment_acoustic(self):
        # 显式隔声：户内吊顶应增补 acoustic(贡献)
        r = reason("住宅", "户内吊顶", demands=["隔声"])
        domains = self._extract_domains(r["推理路径"])
        self.assertIn("acoustic(贡献)", domains)

    def test_commercial_no_acoustic_default(self):
        r = reason("商业", "商铺")
        stds = [s["标准编号"] for s in r["适用标准集"]]
        self.assertNotIn("GB 50118-2010", stds)

    def test_unknown_space_falls_back_minimum(self):
        r = reason("其他", "特殊空间")
        stds = [s["标准编号"] for s in r["适用标准集"]]
        self.assertTrue(any("55037" in s for s in stds))
        self.assertTrue(any("50210" in s for s in stds))


class TestM4Applicability(unittest.TestCase):
    """M4 适用性裁判规则。"""

    def test_local_standard_applicable_when_location_matches(self):
        r = reason("住宅", "分户墙", location="浙江")
        local_stds = [s for s in r["适用标准集"] if s["标准编号"].startswith("DB33")]
        self.assertTrue(local_stds)
        for s in local_stds:
            self.assertEqual(s["地域适用性"], "项目所在地适用")

    def test_local_standard_not_applicable_when_location_differs(self):
        r = reason("住宅", "分户墙", location="广东")
        db33 = [s for s in r["适用标准集"] if s["标准编号"].startswith("DB33")]
        for s in db33:
            self.assertEqual(s["地域适用性"], "不适用仅作对比")

    def test_l1_has_mandatory_check_role(self):
        r = reason("住宅", "分户墙")
        gb55038 = next(s for s in r["适用标准集"] if s["标准编号"] == "GB 55038-2025")
        self.assertEqual(gb55038["角色"], "mandatory_check")


class TestM6Degradation(unittest.TestCase):
    """M6 降级与兜底协议。"""

    def test_missing_location_prompts_question(self):
        r = reason("住宅", "分户墙")
        self.assertIn("未覆盖领域", r)
        self.assertTrue(any("地方标准" in u for u in r["未覆盖领域"]))

    def test_unknown_standard_degrades(self):
        # 通过未知构造体系触发外部协同占位，不应导致崩溃
        r = reason("住宅", "分户墙", system="未知构造")
        self.assertIsInstance(r["适用标准集"], list)


class TestIC10SchemaCompliance(unittest.TestCase):
    """IC-10 Response v1.5.8 Schema 合规。"""

    def test_required_fields_present(self):
        r = reason("住宅", "分户墙")
        self.assertIn("适用标准集", r)
        self.assertIn("推理路径", r)
        self.assertIn("证据对象", r)
        self.assertIsInstance(r["证据对象"], list)
        self.assertGreaterEqual(len(r["证据对象"]), 1)

    def test_evidence_object_schema(self):
        r = reason("住宅", "分户墙")
        for ev in r["证据对象"]:
            self.assertIn("证据ID", ev)
            self.assertIn("证据类型", ev)
            self.assertIn(ev["证据类型"], ["classification", "activation", "mapping", "arbitration", "applicability", "degradation"])
            self.assertIn("规则来源", ev)
            self.assertIn("输入事实", ev)
            self.assertIn("输出结论", ev)
            self.assertIn("置信度", ev)
            self.assertIn(ev["置信度"], ["deterministic", "inferred", "unknown"])

    def test_standard_item_schema(self):
        r = reason("住宅", "分户墙")
        for s in r["适用标准集"]:
            self.assertIn("标准编号", s)
            self.assertIn("标准名称", s)
            self.assertIn("层级", s)
            self.assertIn(s["层级"], ["L1", "L2", "L3", "L4"])
            self.assertIn("权限", s)
            self.assertIn(s["权限"], ["red_line", "binding_support", "reference"])
            self.assertIn("角色", s)
            self.assertIn(s["角色"], ["mandatory_check", "design_basis", "verification_reference", "construction_guide", "prefab_evaluation"])
            self.assertIn("地域适用性", s)
            self.assertIn("时间状态", s)

    def test_decision_trace_when_requested(self):
        r = reason("住宅", "分户墙", return_trace=True)
        self.assertIn("决策轨迹", r)
        self.assertIn("Step 0", r["决策轨迹"])
        self.assertIn("Step 6", r["决策轨迹"])

    def test_decision_trace_not_default(self):
        r = reason("住宅", "分户墙")
        self.assertNotIn("决策轨迹", r)


class TestSRRedlines(unittest.TestCase):
    """SR 引擎化红线 SR-R-P1-5 / P1-6 / P2-3。"""

    def test_evidence_objects_cover_required_types(self):
        r = reason("住宅", "分户墙", demands=["隔声"])
        types = {ev["证据类型"] for ev in r["证据对象"]}
        self.assertTrue(
            types >= {"classification", "activation", "mapping"},
            f"证据类型覆盖不足: {types}"
        )

    def test_evidence_rule_source_is_locatable(self):
        r = reason("住宅", "分户墙")
        for ev in r["证据对象"]:
            self.assertTrue(
                ev["规则来源"].startswith("standards-reasoning-rules.md §"),
                f"规则来源不可定位: {ev['规则来源']}"
            )

    def test_degradation_evidence_on_missing_location(self):
        r = reason("住宅", "分户墙")
        types = {ev["证据类型"] for ev in r["证据对象"]}
        self.assertIn("degradation", types)


def run_and_report() -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    report = {
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "success": result.wasSuccessful(),
    }
    Path("sre_regression_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已写入: sre_regression_report.json")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_and_report())
