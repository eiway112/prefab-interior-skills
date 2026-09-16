"""
SRE Reasoner 回归测试集
========================
版本：v1.3（2026-09-16）
运行：python sre_regression_test.py

覆盖：M1 分类协议、M3 场景推理与 Step 1a 裁定、M4 适用性裁判、M6 降级、
      IC-10 Response v1.5.8 Schema、SR 引擎化红线，
      以及 SRE 确定性体检行为组 T-B1—T-B7 + A5-B 锚定升档
      （判据源《文档/SRE确定性体检设计方案_v1.0.md》§3.2 / §4.3 / §5.2 / §6.2）。
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import random
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import sre_reasoner
from sre_reasoner import reason, classify_standard, _evidence_counter

# ---------------------------------------------------------------------------
# 确定性体检基础设施（设计方案 §3.2 判据 / §4.3 挂载位 / §5.2 十二字段契约）
# 期望值一律取自活体模块与 standards-index.md 现读结果：并行批次改写 STANDARD_NAMES /
# DOMAINS 字面量时，本文件只随事实变化，不随文本漂移。
# ---------------------------------------------------------------------------

SRE_SOURCE = Path(sre_reasoner.__file__).resolve()
SRE_SRC = SRE_SOURCE.read_text(encoding="utf-8")
_SRC_TREE = ast.parse(SRE_SRC)
_REPORT_PATH = Path(__file__).resolve().parent / "sre_regression_report.json"

# 与 sre_reasoner._load_standards_index() 的候选顺序一致
_INDEX_CANDIDATES = [
    SRE_SOURCE.parent.parent / "shared" / "standards-index.md",
    SRE_SOURCE.parent.parent / "standards-index.md",
]

# T-B1 的测量点：本模块 import 完毕、任何用例尚未执行之前
IMPORT_TIME_STATUS_COUNT = len(sre_reasoner.STANDARD_STATUS)

GAP_SIGNALS: list[dict] = []
_SIGNAL_TOUCHED: dict[str, object] = {}

CATEGORY_ENUM = ("DEGRADE", "GAP", "DRIFT")
ESCALATION_ENUM = ("S", "A", "B", "C", "—")
ANCHOR_ENUM = ("true", "false", "—", "unknown")
ACTION_ENUM = ("待补录", "待修代码", "待核原文", "已裁定", "不适用")
STATUS_ENUM = ("义务已生效未落实", "可即刻执行", "待用户确认", "待核原文",
               "待实施", "随批次上线", "已闭环", "有意延后")
SIGNAL_KEYS = ("signal_id", "类别", "判据", "实测值", "期望值", "证据定位",
               "裁定动作", "承担者", "状态", "escalation", "anchor", "verify_channel")

# 索引 §1.1A 中代表"已确认"的那一态；其余三态即 §3.2 T-B2 所指降级侧。
# 运行期核对它仍在现读的表内，SOT 改名时用例转红而非静默放行。
CONFIRMED_VERIFY_STATE = "已官方核验"

# §3.2 T-B6：全国层级 = 编号不以 DB/DBJ/SJG 开头且非 T/ 团标
LOCAL_ID_PREFIXES = ("DB", "DBJ", "SJG", "T/")

# §3.2 场景矩阵（取自 sre_reasoner.ACTIVATION_TABLE 既有行，不新造场景）
SCENARIOS = [
    ("住宅", "分户墙", None), ("住宅", "分户楼板", None),
    ("住宅", "户内吊顶", ["隔声"]), ("住宅", "户内吊顶", ["吸声"]),
    ("住宅", "楼地面", None), ("酒店", "客房吊顶", None),
    ("学校", "教室吊顶", None), ("办公", "办公吊顶", None),
    ("医院", "病房地面", None),
]
LOCATIONS = ["全国", "北京", "浙江", "广东", "深圳", "福建", None]


def _index_text() -> str | None:
    for path in _INDEX_CANDIDATES:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return None


def _section(text: str, start: str, stops: tuple[str, ...]) -> str:
    """按标题正则切出小节；起点未命中返回空串。"""
    lines = text.splitlines()
    begin = next((i for i, ln in enumerate(lines) if re.match(start, ln)), None)
    if begin is None:
        return ""
    end = next((i for i, ln in enumerate(lines[begin + 1:], begin + 1)
                if any(re.match(s, ln) for s in stops)), len(lines))
    return "\n".join(lines[begin:end])


def _table(block: str) -> tuple[list[str], list[list[str]]]:
    """表头感知取块内首张表：返回 (表头单元, 数据行单元)。"""
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        if i + 1 >= len(lines) or set(lines[i + 1].replace("|", "").strip()) - set("-: "):
            continue
        header = [c.strip() for c in line.strip().strip("|").split("|")]
        rows = [[c.strip() for c in ln.strip().strip("|").split("|")]
                for ln in lines[i + 2:] if ln.startswith("|")]
        return header, rows
    return [], []


def _cell(row: list[str], header: list[str], key: str) -> str:
    return row[header.index(key)] if key in header and header.index(key) < len(row) else ""


def _status_enum() -> list[str]:
    """索引 §1.1「标准状态」字段的合法取值集（现读，到「官方核验日期」行为止）。

    §1.1 表首列是状态字段名（且续行首列为空），故停表判据取行首单元，不取列名。
    """
    block = _section(_index_text() or "", r"^### 1\.1\s", (r"^### 1\.1A",))
    header, rows = _table(block)
    values: list[str] = []
    for row in rows:
        if "官方核验日期" in (row[0] if row else ""):
            break
        values += re.findall(r"`([^`]+)`", _cell(row, header, "取值"))
    return list(dict.fromkeys(values))


def _verify_state_enum() -> list[str]:
    """索引 §1.1A 核验状态四态（现读）。"""
    block = _section(_index_text() or "", r"^### 1\.1A", (r"^### 1\.2",))
    header, rows = _table(block)
    key = header[0] if header else ""
    return list(dict.fromkeys(r[0] for r in rows if key and r))


def _deprecated_rows() -> list[tuple[str, str]]:
    """索引 §7.2 的 (标准编号, 状态) 行集（现读，条数不写死）。"""
    block = _section(_index_text() or "", r"^### 7\.2", (r"^### 7\.3",))
    header, rows = _table(block)
    return [(_cell(r, header, "标准编号"), _cell(r, header, "状态"))
            for r in rows if _cell(r, header, "标准编号")]


def _anchor_ids() -> tuple[set[str] | None, str | None]:
    """索引 §10.2 锚定集。不可达时返回 (None, 降级说明)——§5.2 禁静默填 false。"""
    text = _index_text()
    if text is None:
        return None, "standards-index.md 不可达（候选：{}），A5-B 全部信号 anchor=unknown".format(
            "; ".join(str(p) for p in _INDEX_CANDIDATES))
    block = _section(text, r"^### 10\.2", (r"^### ", r"^## "))
    header, rows = _table(block)
    ids = {_cell(r, header, "标准编号") for r in rows} - {""}
    if not ids:
        return None, "索引 §10.2 锚定表解析为空，A5-B 全部信号 anchor=unknown"
    return ids, None


def _assign_line(name: str) -> int | None:
    for node in ast.walk(_SRC_TREE):
        targets = getattr(node, "targets", [getattr(node, "target", None)])
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and any(
                isinstance(t, ast.Name) and t.id == name for t in targets):
            return node.lineno
    return None


def _def_line(name: str) -> int | None:
    obj = getattr(sre_reasoner, name, None)
    try:
        return inspect.getsourcelines(obj)[1]
    except (TypeError, OSError):
        return _assign_line(name)


def _loc(*pairs: tuple[str, int | None]) -> str:
    return "；".join(f"{SRE_SOURCE.name}:{line}（{what}）" for what, line in pairs if line)


def _main_guard_calls() -> tuple[list[int], list[int]]:
    """_load_standards_index() 的调用点按「是否位于 __main__ 守卫子树内」分组。"""
    calls = [n.lineno for n in ast.walk(_SRC_TREE)
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_load_standards_index"]
    guards = [n for n in ast.walk(_SRC_TREE)
              if isinstance(n, ast.If) and "__name__" in ast.dump(n.test)
              and "'__main__'" in ast.dump(n.test)]
    inside = [c for c in calls if any(g.lineno <= c <= (g.end_lineno or g.lineno) for g in guards)]
    return inside, [c for c in calls if c not in inside]


def _probe_id() -> str:
    """每次运行随机的、索引与硬编码表内都不存在的标准编号形态串。"""
    while True:
        candidate = "GB/T 9%06d-19%02d" % (random.randrange(1_000_000), random.randrange(100))
        if (candidate not in sre_reasoner.STANDARD_STATUS
                and candidate not in sre_reasoner.STANDARD_NAMES):
            return candidate


def _reachable_domains() -> set[str]:
    """激活可达域 = 激活表值域 ∪ 声学子域集 ∪ 需求驱动增补域（增补逻辑经活体函数求得）。"""
    reachable = {d for v in sre_reasoner.ACTIVATION_TABLE.values() for d in v}
    reachable |= set(sre_reasoner.ACOUSTIC_SUBDOMAINS)
    demand_matrix = [None, ["隔声"], ["吸声"], ["撞击声"], ["防火", "验收"],
                     ["隔声", "吸声", "撞击声"]]
    for project_type, space_type, _ in SCENARIOS:
        for demands in demand_matrix:
            activated, _ = sre_reasoner._activate_domains(
                project_type, space_type, demands, [])
            reachable |= set(activated)
    return reachable


def _iter_tables(text: str):
    """遍历全文所有 Markdown 表，产出 (表头单元, 数据行单元)。"""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if (line.startswith("|") and i + 1 < len(lines)
                and not set(lines[i + 1].replace("|", "").strip()) - set("-: ")):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            yield header, rows
            i = j
        else:
            i += 1


def _main_table_truth() -> dict[str, str]:
    """索引主表（首列「序号」且含「状态」列）的 编号→状态 真值，按表头列名取值。

    刻意不复用被测代码的固定列号口径：本函数即 T-B4 的对照基准。
    """
    truth: dict[str, str] = {}
    for header, rows in _iter_tables(_index_text() or ""):
        if not header or header[0] != "序号" or "状态" not in header:
            continue
        id_col = next((c for c in ("标准编号", "图集编号") if c in header), None)
        if not id_col:
            continue
        for row in rows:
            std_no = _cell(row, header, id_col)
            if std_no:
                truth[std_no] = _cell(row, header, "状态")
    return truth


def _applicable_ids(project_type: str, space_type: str, demands, location) -> set[str]:
    response = sre_reasoner.reason(project_type, space_type, location=location,
                                   demands=demands, system="轻钢龙骨")
    return {item["标准编号"] for item in response["适用标准集"]}


def _record_signal(signal_id: str, category: str, observed: str, expected: str,
                   location: str, escalation: str, violated: bool, touched=set()) -> None:
    """按 §5.2 十二字段记账。裁定动作/状态首轮留空键（§10 条 4），anchor 由 A5-B 覆写。

    `violated=False`（该项已修复）时不落信号——信号集须随修复收敛，否则摘掉
    `@unittest.expectedFailure` 后仍会留下一条已消失的缺口，与 §6.2 自退役语义相悖。
    """
    if not violated:
        return
    GAP_SIGNALS.append({
        "signal_id": signal_id,
        "类别": category,
        "判据": f"《SRE确定性体检设计方案_v1.0.md》§3.2 {signal_id} 行（按指针取值，不在运行期重抄）",
        "实测值": observed,
        "期望值": expected,
        "证据定位": location,
        "裁定动作": None,
        "承担者": "用户（授权运行时写入）→ 维护者（实施）",
        "状态": None,
        "escalation": escalation,
        "anchor": "false",
        "verify_channel": "—",
    })
    _SIGNAL_TOUCHED[signal_id] = touched


def _validate_signal(sig: dict) -> None:
    """落盘前拒绝枚举外的值（§10 条 4）。"""
    missing = [k for k in SIGNAL_KEYS if k not in sig]
    if missing:
        raise ValueError(f"信号 {sig.get('signal_id')} 缺字段：{missing}")
    for key, allowed in (("类别", CATEGORY_ENUM), ("escalation", ESCALATION_ENUM),
                         ("anchor", ANCHOR_ENUM)):
        if sig[key] not in allowed:
            raise ValueError(f"信号 {sig['signal_id']} 的 {key}={sig[key]!r} 越出闭合枚举 {allowed}")
    for key, allowed in (("裁定动作", ACTION_ENUM), ("状态", STATUS_ENUM)):
        value = sig[key]
        if value is None:
            continue
        # §5.2：一格可并列多值（`待修代码①：…；待补录②：…`），逐段校验而非只查首词
        for seg in re.split(r"[；;]", str(value)):
            seg = seg.strip()
            if not seg:
                continue
            head = re.sub(r"[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]", "",
                          re.split(r"[：:（(]", seg)[0]).strip()
            if head not in allowed:
                raise ValueError(
                    f"信号 {sig['signal_id']} 的 {key} 段首词 {head!r} 越出闭合枚举 {allowed}")


def _aggregate_anchors() -> list[str]:
    """A5-B：本组其余检查跑完后运行，对每条信号按其触及编号叠加 anchor（§4.1/§4.3）。"""
    anchors, degraded = _anchor_ids()
    warnings = []
    if degraded:
        warnings.append(f"[SRE-GAP] A5-B 降级：{degraded}")
    for sig in GAP_SIGNALS:
        touched = _SIGNAL_TOUCHED.get(sig["signal_id"])
        touched = touched() if callable(touched) else set(touched or ())
        if anchors is None:
            sig["anchor"] = "unknown"
        else:
            sig["anchor"] = "true" if anchors & touched else "false"
    return warnings


def _signal_state() -> tuple[str, int]:
    """§6.3.3 ① 的跨轮指纹：绑到信号内容，实测值规模漂移即视为抖动。"""
    rows = sorted([sig["signal_id"], sig["类别"], sig["实测值"], sig["期望值"]]
                  for sig in GAP_SIGNALS)
    digest = hashlib.sha256(
        json.dumps(rows, ensure_ascii=False).encode("utf-8")).hexdigest()
    return digest[:16], len(rows)


def _previous_report() -> dict:
    try:
        loaded = json.loads(_REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


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


class _SREDeterminismBase(unittest.TestCase):
    """体检用例基类：进入前对齐加载器，退出后就地回滚模块级字典。

    unittest 按类名字母序排，本组类名排在 `TestSRRedlines` 之前；加载器同时改写
    `STANDARD_STATUS` 与 `STANDARD_NAMES`（`setdefault` 支路），若留在原地会污染既有
    23 条用例——T-B1 的「导入态计数」尤其依赖未加载的初值。故 `tearDown` 用
    clear+update 原地回滚而不换引用，被测代码持有的仍是同一对象。
    """

    def setUp(self) -> None:
        self._saved_status = dict(sre_reasoner.STANDARD_STATUS)
        self._saved_names = dict(sre_reasoner.STANDARD_NAMES)
        sre_reasoner._load_standards_index()

    def tearDown(self) -> None:
        for target, saved in ((sre_reasoner.STANDARD_STATUS, self._saved_status),
                              (sre_reasoner.STANDARD_NAMES, self._saved_names)):
            target.clear()
            target.update(saved)

    def _empty_families(self, response: dict) -> list[str]:
        """从证据对象里取输出空标准族的领域名。"""
        out = []
        for ev in response.get("证据对象", []):
            if ev.get("证据类型") != "mapping":
                continue
            match = re.match(r"^领域=([^,]+),", str(ev.get("输入事实", "")))
            if match and "标准族=[]" in str(ev.get("输出结论", "")):
                out.append(match.group(1))
        return out


class TestSREDeterminismStatic(_SREDeterminismBase):
    """SRE 确定性体检·行为组（静态可测子集）T-B1 / T-B3 / T-B4 / T-B7。

    判据源《文档/SRE确定性体检设计方案_v1.0.md》§3.2，逐例以 `@unittest.expectedFailure`
    挂档。**自退役规则（§6.2）**：本类用例转成 unexpected success 即说明对应缺陷已由
    `sre_reasoner.py` 真实修复——此时必须摘掉装饰器、把断言转为正向常态断言，
    **禁止回退或注释掉被测代码的修复来让用例重新"预期失败"**。unexpected success
    会让 `wasSuccessful()` 返回 False、门禁 exit 1，这是设计意图而非故障。
    """

    @unittest.expectedFailure
    def test_TB1_index_loaded_at_import(self):
        inside, outside = _main_guard_calls()
        loaded = len(sre_reasoner.STANDARD_STATUS)
        truth = _main_table_truth()
        _record_signal(
            "T-B1", "DEGRADE",
            f"库导入态 STANDARD_STATUS = {IMPORT_TIME_STATUS_COUNT} 条；显式调用加载器后 = {loaded} 条；"
            f"主表应载 {len(truth)} 条",
            "导入态 > 0 条，且与显式加载同输入同输出（两入口可达同一加载器）",
            _loc(("STANDARD_STATUS 定义", _assign_line("STANDARD_STATUS")),
                 ("_load_standards_index 定义", _def_line("_load_standards_index")),
                 ("__main__ 守卫内调用", inside[0] if inside else None),
                 ("导入期调用", outside[0] if outside else None)),
            "S", touched=set(truth),
            violated=IMPORT_TIME_STATUS_COUNT <= 0 or IMPORT_TIME_STATUS_COUNT != loaded,
        )
        self.assertGreater(IMPORT_TIME_STATUS_COUNT, 0, "库导入态标准状态表为空")
        self.assertEqual(IMPORT_TIME_STATUS_COUNT, loaded,
                         "导入态与显式加载态不同：两入口口径已分叉")

    @unittest.expectedFailure
    def test_TB3_activated_domains_have_mapping(self):
        dead = sorted(_reachable_domains() - set(sre_reasoner.DOMAINS))
        redundant = sorted(set(sre_reasoner.DOMAINS) - _reachable_domains())
        _record_signal(
            "T-B3", "GAP",
            f"死链域 {len(dead)} 个：{dead}；冗余域 {len(redundant)} 个：{redundant}",
            "激活可达域 ⊆ DOMAINS 键集，且无不可达冗余键",
            _loc(("DOMAINS 定义", _assign_line("DOMAINS")),
                 ("ACTIVATION_TABLE 定义", _assign_line("ACTIVATION_TABLE")),
                 ("ACOUSTIC_SUBDOMAINS 定义", _assign_line("ACOUSTIC_SUBDOMAINS")),
                 ("_map_domain_to_standards 定义", _def_line("_map_domain_to_standards"))),
            "B", violated=bool(dead or redundant),
        )
        self.assertEqual(dead, [], "存在被激活却无映射的死链域")
        self.assertEqual(redundant, [], "存在不可达的冗余映射键")

    @unittest.expectedFailure
    def test_TB4_status_read_by_header(self):
        truth = _main_table_truth()
        enum = _status_enum()
        mismatch = {k: (sre_reasoner.STANDARD_STATUS.get(k), v)
                    for k, v in truth.items() if sre_reasoner.STANDARD_STATUS.get(k) != v}
        # 设计 §3.2 取前缀口径（明文允许「现行有效（代替…）」类括号注记），非全等比较
        out_of_enum = {k: v for k, v in sre_reasoner.STANDARD_STATUS.items()
                       if not any(str(v).startswith(e) for e in enum)}
        # 两状态独立表达：被部分替代不得被改写为过渡期（真值注入法，不依赖列位缺陷是否已修）
        conversion = ""
        if "被部分替代" in enum and "过渡期" in enum:
            ids = sorted(_applicable_ids("住宅", "分户墙", None, "浙江"))
            if ids:
                sre_reasoner.STANDARD_STATUS[ids[0]] = "被部分替代"
                after = next((i for i in reason("住宅", "分户墙", location="浙江")["适用标准集"]
                              if i["标准编号"] == ids[0]), None)
                conversion = f"{ids[0]}：注入 被部分替代 → 输出 {after and after['时间状态']!r}"
        conversion_bad = bool(conversion) and "→ 输出 '被部分替代'" not in conversion
        _record_signal(
            "T-B4", "DRIFT",
            f"主表 {len(truth)} 项中 {len(mismatch)} 项加载态≠表头真值；加载态越出 §1.1 枚举 "
            f"{len(out_of_enum)} 项；{conversion or '状态转换项未测（枚举已改名）'}",
            "状态一律按表头列名读取（与表头感知真值同值）、落在 §1.1 枚举内，"
            "且 被部分替代 与 过渡期 不得互转",
            _loc(("固定列号取值", _assign_line("STANDARD_STATUS")),
                 ("_load_standards_index 定义", _def_line("_load_standards_index")),
                 ("时间状态映射", _def_line("_apply_applicability"))),
            "A", touched=set(mismatch) | set(out_of_enum),
            violated=bool(mismatch or out_of_enum or conversion_bad),
        )
        self.assertEqual(mismatch, {}, "加载状态与表头真值不一致")
        self.assertEqual(out_of_enum, {}, "加载状态越出索引 §1.1 六值枚举")
        if conversion:
            self.assertFalse(conversion_bad, f"{conversion}｜被部分替代 被方向性改写为 过渡期")

    @unittest.expectedFailure
    def test_TB7_withdrawn_standards_reachable(self):
        registered = _deprecated_rows()
        missing = sorted(i for i, _ in registered if i and i not in sre_reasoner.STANDARD_STATUS)
        _record_signal(
            "T-B7", "GAP",
            f"§7.2 登记 {len(registered)} 行，其中 {len(missing)} 行未被加载器载入：{missing}",
            "§7.2 全部登记行可达（其已废止/被部分替代状态可被推理链读到）",
            _loc(("表类型守卫", _def_line("_load_standards_index")),
                 ("STANDARD_STATUS 定义", _assign_line("STANDARD_STATUS"))),
            "S", touched=set(missing), violated=bool(missing),
        )
        self.assertEqual(missing, [], "§7.2 已废止/被部分替代登记对推理链不可达")


class TestSREDeterminismBehavior(_SREDeterminismBase):
    """SRE 确定性体检·行为组（推理运行子集）T-B2 / T-B5 / T-B6。

    自退役规则同 `TestSREDeterminismStatic`（设计方案 §6.2）：unexpected success =
    修复已落地，须摘装饰器转正向断言，**禁止回退 `sre_reasoner.py` 的修复**。
    """

    @unittest.expectedFailure
    def test_TB2_unregistered_id_degrades(self):
        enum = _status_enum()
        probes = [_probe_id() for _ in range(5)]
        got = {p: sre_reasoner._standard_status(p) for p in probes}
        # 导入态（setUp 快照、未经显式加载）下锚定编号走同一兜底分支——§9.1 判该行为 anchor=true 的来源
        anchors, _ = _anchor_ids()
        sre_reasoner.STANDARD_STATUS.clear()
        sre_reasoner.STANDARD_STATUS.update(self._saved_status)
        anchor_fallback = sorted(a for a in (anchors or set()) if a not in self._saved_status)
        got |= {a: sre_reasoner._standard_status(a) for a in anchor_fallback}
        deterministic = {k: v for k, v in got.items() if v in enum}
        _record_signal(
            "T-B2", "DEGRADE",
            f"{len(probes)} 个随机不存在编号 + 导入态未登记的锚定编号 {len(anchor_fallback)} 条，"
            f"经 _standard_status() 得确定性状态 {len(deterministic)} 项："
            f"{sorted(set(deterministic.values()))}（触 SR-R-P0-2）",
            "未登记编号不得返回任何 §1.1 确定性状态，须落显式降级态（待核验/未知）",
            _loc(("_standard_status 定义（含兜底默认值）", _def_line("_standard_status"))),
            "S", touched=set(deterministic), violated=bool(deterministic),
        )
        self.assertEqual(deterministic, {}, "对输入域无界的未登记编号给出了确定性状态")

    @unittest.expectedFailure
    def test_TB5_empty_family_reported_uncovered(self):
        silent: list[tuple[str, str, str | None, str]] = []
        for project_type, space_type, demands in SCENARIOS:
            for location in LOCATIONS:
                response = reason(project_type, space_type, location=location, demands=demands)
                uncovered = response.get("未覆盖领域", [])
                for domain in self._empty_families(response):
                    if not any(domain in u or domain.split("(")[0] in u for u in uncovered):
                        silent.append((project_type, space_type, location, domain))
        _record_signal(
            "T-B5", "DEGRADE",
            f"空标准族输出 {len(silent)} 处未上报未覆盖领域（静默）：{silent[:6]}"
            + ("…" if len(silent) > 6 else ""),
            "凡 标准族=[] 的映射证据，其领域必须出现在 未覆盖领域 中（LA-4/M 系列降级可见）",
            _loc(("_map_domain_to_standards 定义", _def_line("_map_domain_to_standards")),
                 ("reason 定义", _def_line("reason"))),
            "B", violated=bool(silent),
        )
        self.assertEqual(silent, [], "空标准族被静默吞掉")

    @unittest.expectedFailure
    def test_TB6_national_baseline_additive(self):
        lost: list[tuple[str | None, str]] = []
        for project_type, space_type, demands in SCENARIOS:
            per_location = {loc: _applicable_ids(project_type, space_type, demands, loc)
                            for loc in LOCATIONS}
            union = set().union(*per_location.values())
            national = {i for i in union if not i.startswith(LOCAL_ID_PREFIXES)}
            for loc, ids in per_location.items():
                lost += [(loc, i) for i in sorted(national - ids)]
        _record_signal(
            "T-B6", "DEGRADE",
            f"全国层级标准随地点丢失 {len(lost)} 处：{lost[:8]}" + ("…" if len(lost) > 8 else ""),
            "全国基线对全部地点（含未提供地点）可叠加，地方标准作增量而非互斥分支",
            _loc(("_map_domain_to_standards 定义", _def_line("_map_domain_to_standards"))),
            "A", touched={i for _, i in lost}, violated=bool(lost),
        )
        self.assertEqual(lost, [], "地点分支抑制了全国层级标准的输出")


def _fingerprint(path: Path) -> dict:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {"path": str(path), "readable": False, "error": str(exc)}
    return {"path": str(path), "readable": True, "bytes": len(data),
            "sha256_12": hashlib.sha256(data).hexdigest()[:12]}


def run_and_report() -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # A5-B 锚定升档：必须在本组其余检查全部执行完之后运行（§4.1 / §4.3）
    warnings = _aggregate_anchors()
    for text in warnings:
        print(f"[SRE-GAP] {text}")
    for sig in GAP_SIGNALS:
        _validate_signal(sig)

    fingerprint, count = _signal_state()
    previous = _previous_report()
    previous_fingerprint = previous.get("signal_fingerprint")
    stable_streak = (previous.get("signal_stable_streak", 0) + 1
                     if previous_fingerprint == fingerprint else 1)

    report = {
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "success": result.wasSuccessful(),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "signal_count": count,
        "signal_fingerprint": fingerprint,
        "signal_previous_fingerprint": previous_fingerprint,
        "signal_stable_streak": stable_streak,
        "gap_signals": GAP_SIGNALS,
        "measurements": {
            "sre_reasoner": _fingerprint(SRE_SOURCE),
            "standards_index": {str(p): _fingerprint(p) for p in _INDEX_CANDIDATES if p.exists()},
        },
    }
    _REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已写入: {_REPORT_PATH}")
    print(f"缺口信号 {count} 条｜本轮指纹 {fingerprint}｜上轮指纹 "
          f"{previous_fingerprint or '（首轮，无历史）'}｜连续一致 {stable_streak} 轮"
          f"（§6.3.3 ① 需 ≥2）")
    print("范围说明：本 JSON 只承载载体 B 的行为组信号 T-B1—T-B7；静态组 T-A1—T-A5 由 "
          "程序文件/validate_governance.py 检查 5 独立产出，两载体互不读取（设计方案 §4.1）。")

    if result.unexpectedSuccesses:
        print("⚠ 存在 unexpected success：对应缺陷已被修复。按设计方案 §6.2 须摘除该用例的 "
              "@unittest.expectedFailure 装饰器并转为正向断言——禁止回退 sre_reasoner.py 的修复来消除本提示。")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_and_report())
