"""
SRE Reasoner 回归测试集
========================
版本：v1.7（2026-09-17，CG-20260917-004：新增断点8 判断层守卫 test_BP8_name_keyword_does_not_override_binding_support_role——L2/binding_support 标准名称含「测量/评价」角色仍恒 design_basis，订正第三方审阅 T-A1「名称差分会改角色」的被推翻推定）
运行：python sre_regression_test.py

覆盖：M1 分类协议、M3 场景推理与 Step 1a 裁定、M4 适用性裁判、M6 降级、
      IC-10 Response v1.9.0 Schema、SR 引擎化红线，
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

# IC-10 契约候选，与索引同序（运行时 shared 镜像为 L3、技能目录兜底）
_CONTRACT_CANDIDATES = [
    SRE_SOURCE.parent.parent / "shared" / "interface-contracts.md",
    SRE_SOURCE.parent.parent / "interface-contracts.md",
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
    """表头感知取块内首张表：返回 (表头单元, 数据行单元)。

    数据行在首个非表格行处截断——否则同一小节内的第二张表（如索引 §二 末尾的
    「官方核验记录」）会被并入首表行集，其表头单元被当成编号读出。
    """
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        sep = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if not sep or set(sep.replace("|", "").strip()) - set("-: "):
            continue
        header = [c.strip() for c in line.strip().strip("|").split("|")]
        rows: list[list[str]] = []
        for ln in lines[i + 2:]:
            if not ln.startswith("|"):
                break
            rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
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


def _contract_text() -> str:
    for path in _CONTRACT_CANDIDATES:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def _contract_ic10_status_enum() -> list[str]:
    """IC-10 `适用标准集[].时间状态` 合法集（从契约 Schema 现读，不写死）。

    契约缺失或正则脱靶时返回空表——调用方按"全表越界"失败收口，不静默放行。
    """
    match = re.search(r'"时间状态":\s*\{[^{}]*?"enum":\s*\[([^\]]*)\]', _contract_text(), re.S)
    if not match:
        return []
    return [s.strip().strip('"') for s in match.group(1).split(",") if s.strip()]


def _contract_ic10_role_enum() -> list[str]:
    """IC-10 `适用标准集[].角色` 合法集（从契约 Schema 现读，本文件不留字面量副本）。

    契约缺失或正则脱靶时返回空表——调用方按"全表越界"失败收口，不静默放行。
    """
    match = re.search(r'"角色":\s*\{[^{}]*?"enum":\s*\[([^\]]*)\]', _contract_text(), re.S)
    if not match:
        return []
    return [s.strip().strip('"') for s in match.group(1).split(",") if s.strip()]


def _contract_declares(field: str) -> bool:
    """字段是否已在 IC-10 契约 Schema 里声明（additionalProperties: false 的前置条件）。"""
    return f'"{field}":' in _contract_text()


def _index_l1_ids() -> set[str]:
    """索引 §二「第一层级：强制性国标（红线标准）」主表编号（从索引现读）。

    不取 `sre_reasoner.INDEX_L1_IDS`——运行时自证自指无交叉核对力，两侧同错即静默放行。
    """
    block = _section(_index_text() or "", r"^## 二、", (r"^## 三、",))
    header, rows = _table(block)
    return {_cell(r, header, "标准编号") for r in rows} - {""}


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
        # 断点7（CG-20260917-002）：层级真值源是 rules.md §1.2，DB/DBJ 地方标准=L2
        # （binding_support 设计/验收），非 L3。此前代码给 L3 与 rules.md 实质分歧。
        r = self._classify("DB33/T 1168-2019")
        self.assertEqual(r["层级"], "L2")
        self.assertEqual(r["权限"], "binding_support")
        self.assertEqual(r["地域范围"], "浙江")

    def test_dbj_is_local_l2(self):
        """断点7（CG-20260917-002）：DBJ/T 序号型（15=广东、13=福建）亦为 L2。"""
        for no in ("DBJ/T 15-208-2020", "DBJ/T 13-428-2023"):
            r = self._classify(no)
            self.assertEqual(r["层级"], "L2", f"{no} 应为 L2")
            self.assertEqual(r["权限"], "binding_support")

    def test_dbj_province_code_form_matches(self):
        """遗留2（CG-20260917-003）：DBJ+省码数字形态（DBJ33/T 1327-2024）须命中前缀，
        不再落 unknown_type；省份从索引 §5.3「适用地区」现读为浙江。
        负向半条：DBJX 一类非法形态仍须降级（守卫修净后仍能失败）。"""
        r = self._classify("DBJ33/T 1327-2024")
        self.assertEqual(r["标准类型"], "地方建设标准")
        self.assertEqual(r["层级"], "L2")
        self.assertEqual(r["权限"], "binding_support")
        self.assertEqual(r["地域范围"], "浙江")
        self.assertEqual(r["分类置信度"], "deterministic")
        bad = self._classify("DBJX 123-2024")
        self.assertEqual(bad["标准类型"], "unknown_type")
        self.assertEqual(bad["分类置信度"], "inferred")

    def test_t_group_is_l2_reference(self):
        # 遗留1（CG-20260917-003）：团体标准层级真值源 rules.md §1.2 定 L2（原代码 L4 分歧）；
        # 权限仍 reference（GS-1 团标不优先于 GB/T）。
        r = self._classify("T/CSUS 40-2022")
        self.assertEqual(r["层级"], "L2")
        self.assertEqual(r["权限"], "reference")

    def test_unknown_prefix_degrades(self):
        r = self._classify("XYZ 123-2024")
        self.assertEqual(r["分类置信度"], "inferred")
        self.assertEqual(r["权限"], "reference")

    def test_atlas_j_series_matches_prefix(self):
        """§1.2「数字+`J`」行须真命中：`\\b` 版式在 J 与数字间不成立，图集号会静默落 §1.4 降级支。"""
        for atlas in ("08J931", "07J905-1"):
            r = self._classify(atlas)
            self.assertEqual(r["标准类型"], "图集", f"{atlas} 未命中 §1.2 图集行")
            self.assertEqual(r["层级"], "L3")
            self.assertEqual(r["权限"], "reference")
            self.assertEqual(r["分类置信度"], "deterministic")

    def test_index_section2_id_is_l1_not_demoted(self):
        """前缀不可识别但索引 §二「第一层级：强制性国标（红线标准）」收录 → L1/red_line。

        降级为 reference 会把红线标准降为参考级。期望集从索引 §二 现读，不写死编号清单。
        """
        l1_ids = _index_l1_ids()
        self.assertGreater(len(l1_ids), 0, "索引 §二 现读为空，判据不可用")
        demoted = {i for i in l1_ids if self._classify(i)["层级"] != "L1"}
        self.assertEqual(demoted, set(), f"索引 §二 收录的强制性国标被降为参考级：{sorted(demoted)}")
        # 负向半条：索引外编号仍须走 §1.4 降级，本判据不得把任意编号升成 L1
        fake = "ZZ 9999-1999"
        self.assertNotIn(fake, l1_ids)
        self.assertEqual(
            (self._classify(fake)["层级"], self._classify(fake)["权限"],
             self._classify(fake)["分类置信度"]),
            ("L4", "reference", "inferred"), "索引外编号未走 §1.4 降级支")


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

    def _matrix_items(self, std_no: str):
        """全 34 组激活对 × LOCATIONS 里指定编号的产出条目，随附其场景键。"""
        for project_type, space_type in sre_reasoner.ACTIVATION_TABLE:
            for location in LOCATIONS:
                for s in reason(project_type, space_type, location=location)["适用标准集"]:
                    if s["标准编号"] == std_no:
                        yield (project_type, space_type, location), s

    def test_index_section2_standard_gets_mandatory_check(self):
        """GB 18580-2025 裁定值（出处＝索引 §二 红线标准）：全矩阵恒为 L1/red_line/mandatory_check。"""
        bad = [(k, s["层级"], s["权限"], s["角色"])
               for k, s in self._matrix_items("GB 18580-2025")
               if (s["层级"], s["权限"], s["角色"]) != ("L1", "red_line", "mandatory_check")]
        self.assertGreater(len(list(self._matrix_items("GB 18580-2025"))), 0,
                           "GB 18580-2025 未进入任何场景输出，判据空跑")
        self.assertEqual(bad, [], f"甲醛环保红线在部分场景仍被降为参考级：{bad[:4]}")

    def test_atlas_standard_gets_construction_guide(self):
        """08J931 裁定值（出处＝§1.2「数字+`J`」图集行 + Step 4「L3 图集」）：恒为 L3/construction_guide。"""
        hits = list(self._matrix_items("08J931"))
        self.assertGreater(len(hits), 0, "08J931 未进入任何场景输出，判据空跑")
        bad = [(k, s["层级"], s["角色"]) for k, s in hits
               if (s["层级"], s["角色"]) != ("L3", "construction_guide")]
        self.assertEqual(bad, [], f"图集未落 Step 4 的 L3 分支：{bad[:4]}")

    def test_M4_fallback_role_stays_in_contract_enum(self):
        """负向注入：前缀不可识别、索引未收录的编号经 M4 `else` 兜底，角色仍须属契约五值。

        全矩阵正例在数据面修净后不再含兜底支编号（恒真空跑），故合成注入绑定该支——
        兜底值回退为 `reference` 时本用例转红（记忆「修净后的守卫须仍能失败」）。
        """
        fake = "ZZ 9999-1999"
        self.assertNotIn(fake, sre_reasoner.INDEX_L1_IDS, "合成编号已在索引 §二，负向取证失效")
        self.assertFalse(any(re.match(pat, fake) for pat, *_ in sre_reasoner.PREFIX_PATTERNS),
                         "合成编号撞上真实前缀模式，未走 §1.4 降级支")
        domain = next(d for d, m in sre_reasoner.DOMAINS.items()
                      if "默认" in m and "全部" not in m and "住宅" not in m)
        scenario = next(k for k, v in sre_reasoner.ACTIVATION_TABLE.items() if domain in v)
        saved = {d: dict(m) for d, m in sre_reasoner.DOMAINS.items()}
        try:
            mapping = dict(sre_reasoner.DOMAINS[domain])
            mapping["默认"] = list(mapping["默认"]) + [fake]
            sre_reasoner.DOMAINS[domain] = mapping
            hit = next((s for s in reason(*scenario)["适用标准集"] if s["标准编号"] == fake), None)
            self.assertIsNotNone(hit, "合成编号未进入输出，负向路径根本没走到")
            role_enum = _contract_ic10_role_enum()
            self.assertIn(hit["角色"], role_enum,
                          f"M4 兜底支产出 {hit['角色']!r}，越出 IC-10 契约枚举 {role_enum}")
            self.assertLess(sre_reasoner._role_priority(hit["角色"]), 99,
                            "兜底角色落不进 Step 5 优先级表，排序按未知处理")
        finally:
            for d, m in saved.items():
                sre_reasoner.DOMAINS[d] = m


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
    """IC-10 Response v1.9.0 Schema 合规（v1.9.0：新增响应字段「外部协同」，CG-20260917-002）。"""

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
        """IC-10 条目逐字段合规：全 34 组激活对 × LOCATIONS 矩阵遍历。

        判据原为 `reason("住宅", "分户墙")` 单场景（CG-20260916-005 复核 F-03 已登记该
        覆盖面缺口）：该场景不含任何走 M1 降级支的编号，`角色` 断言在 M4 `else` 兜底越枚举
        真实存在时仍恒真。扩面后凡落进兜底支的编号都进入判据面。
        """
        contract_enum = _contract_ic10_status_enum()
        role_enum = _contract_ic10_role_enum()
        self.assertGreater(len(role_enum), 0, "IC-10 契约 角色 枚举现读为空，降级判据不可用")
        bad: list[str] = []
        visited: set[tuple[str, str]] = set()
        checked = 0
        for project_type, space_type in sre_reasoner.ACTIVATION_TABLE:
            for location in LOCATIONS:
                visited.add((project_type, space_type))
                for s in reason(project_type, space_type, location=location)["适用标准集"]:
                    checked += 1
                    tag = f"{project_type}/{space_type}/{location} {s.get('标准编号')}"
                    for field in ("标准编号", "标准名称", "层级", "权限", "角色",
                                  "地域适用性", "时间状态"):
                        if field not in s:
                            bad.append(f"{tag} 缺字段 {field}")
                    if s.get("层级") not in ("L1", "L2", "L3", "L4"):
                        bad.append(f"{tag} 层级 {s.get('层级')!r} 越界")
                    if s.get("权限") not in ("red_line", "binding_support", "reference"):
                        bad.append(f"{tag} 权限 {s.get('权限')!r} 越界")
                    if s.get("角色") not in role_enum:
                        bad.append(f"{tag} 角色 {s.get('角色')!r} 越出 IC-10 契约枚举 {role_enum}")
                    if s.get("时间状态") not in contract_enum:
                        bad.append(f"{tag} 时间状态 {s.get('时间状态')!r} 越出 IC-10 契约枚举")
                    if s.get("状态注记") == "":
                        bad.append(f"{tag} 状态注记 为空串，应省略该字段")
        self.assertEqual(visited, set(sre_reasoner.ACTIVATION_TABLE), "矩阵遍历漏组")
        self.assertGreater(checked, len(visited) * len(LOCATIONS),
                           "矩阵未产出条目（空跑），字段断言无绑定力")
        self.assertEqual(bad, [], f"IC-10 条目字段越界 {len(bad)} 处：{bad[:6]}")

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


class TestP0SceneExpectations(unittest.TestCase):
    """P0 断点 1-6 + P1 断点8 修复的场景级期望值断言（第三方审阅报告 §三 / §6.3）。

    每条均为「给定输入 → 断言输出标准集/字段」，这是报告指出当前完全缺失的一类机检；
    并各带负向半条防过度修正。回退对应修复后本组用例须复红（反向注入自证）。
    """

    # ---- 断点1：环保分支不可达（医院/学校键被「默认」拦截）----
    def test_BP1_hospital_school_environmental_branch_reachable(self):
        """医院/学校 environmental 须拿到 rules.md §3.2 该行全部三条标准。"""
        for pt, sp in (("医院", "病房"), ("医院", "诊疗室"), ("学校", "教室墙面")):
            stds = {s["标准编号"] for s in reason(pt, sp)["适用标准集"]}
            for need in ("GB 18580-2025", "GB 30981.1-2025", "T/CSUS 03-2019"):
                self.assertIn(need, stds, f"{pt}|{sp} 环保分支丢 {need}")

    def test_BP1_non_hospital_environmental_stays_default(self):
        """负向半条：住宅户内墙面 environmental 仍只走「默认」族，不得误得医院/学校专属三条。

        若把「医院/学校」分支提前时漏掉 project_type 限定，本用例转红。
        """
        stds = {s["标准编号"] for s in reason("住宅", "户内墙面")["适用标准集"]}
        self.assertIn("GB 18580-2025", stds)
        for forbidden in ("T/CSUS 03-2019", "GB 30981.1-2025"):
            self.assertNotIn(forbidden, stds, f"住宅场景误命中医院/学校专属族 {forbidden}")

    # ---- 断点2：地点入参归一化（北京市→北京）----
    def test_BP2_location_full_name_normalized(self):
        """「北京市/浙江省/广东省」全称须与 stripped 形态命中同一适用标准集。"""
        for full, stripped in (("北京市", "北京"), ("浙江省", "浙江"), ("广东省", "广东")):
            a = {s["标准编号"] for s in reason("住宅", "分户墙", location=full)["适用标准集"]}
            b = {s["标准编号"] for s in reason("住宅", "分户墙", location=stripped)["适用标准集"]}
            self.assertEqual(a, b, f"{full} 与 {stripped} 适用标准集不一致（归一化失效）")
        r = reason("住宅", "分户墙", location="北京市")
        db11 = [s for s in r["适用标准集"] if s["标准编号"] == "DB11/T 1553-2025"]
        self.assertTrue(db11, "北京市未命中 DB11/T 1553-2025")
        self.assertEqual(db11[0]["地域适用性"], "项目所在地适用")

    # ---- 断点3：DBJ 省码索引现读 ----
    @staticmethod
    def _index_region_truth() -> dict[str, str]:
        """索引 §5.3「适用地区」现读（编号→地区），独立于被测代码的解析路径。"""
        block = _section(_index_text() or "", r"^### 5\.3", (r"^### ", r"^## "))
        header, rows = _table(block)
        out: dict[str, str] = {}
        for row in rows:
            no = _cell(row, header, "标准编号")
            reg = _cell(row, header, "适用地区")
            if no and reg and not no.startswith("—"):
                out[no] = reg
        return out

    def test_BP3_dbj_province_resolved_from_index(self):
        """DB/DBJ 地方标准省份须从索引 §5.3「适用地区」现读，不落「待确认省份」。

        对引擎能分类为地方标准者断言。DBJ+省码数字形态（DBJ33/T 1327-2024）此前因
        `^DBJ\\b` 漏命中而落 unknown_type、被本用例跳过；该缺口已由遗留2（CG-20260917-003）
        闭合，DBJ33/T 现可分类，其省份（浙江）由本用例一并现读校验。
        """
        region_truth = self._index_region_truth()
        self.assertTrue(region_truth, "索引 §5.3 适用地区现读为空，判据不可用")
        checked = 0
        for no, reg in region_truth.items():
            if not no.startswith(("DB", "DBJ")):
                continue
            c = classify_standard(no, [])
            if c["标准类型"] == "unknown_type":
                continue
            self.assertEqual(c["地域范围"], reg, f"{no} 地域范围应为 {reg}（索引现读）")
            checked += 1
        self.assertGreaterEqual(checked, 2, "断点3 判据空跑：可分类的 DB/DBJ 条目不足")

    def test_BP3_dbj_applicable_in_own_province(self):
        """DBJ/T 15-208-2020 在广东场景须判「项目所在地适用」，不再误判「不适用仅作对比」。"""
        r = reason("住宅", "分户墙", location="广东")
        dbj15 = [s for s in r["适用标准集"] if s["标准编号"] == "DBJ/T 15-208-2020"]
        self.assertTrue(dbj15, "广东场景未命中 DBJ/T 15-208-2020")
        self.assertEqual(dbj15[0]["地域适用性"], "项目所在地适用")

    # ---- 断点4：场景未命中降级提示写入「未覆盖领域」----
    def test_BP4_unmatched_scene_surfaced_in_uncovered(self):
        # 断点6（CG-20260917-002）：原用例含 ("住宅","卫生间")，自 ACTIVATION_TABLE
        # 改由空间类型维度承载厨卫湿区后，卫生间经 SPACE_ALIASES→厨卫湿区 已命中，不再是
        # 未命中场景。换成真正无映射的 ("商业","地下车库")，保持本判据不空跑。
        for pt, sp in (("养老机构", "失智照护区"), ("商业", "地下车库"), ("其他", "特殊空间")):
            unc = reason(pt, sp).get("未覆盖领域")
            self.assertTrue(unc, f"{pt}|{sp} 未命中场景但「未覆盖领域」为空")
            self.assertTrue(any("场景未命中" in u for u in unc),
                            f"{pt}|{sp}「未覆盖领域」缺场景未命中降级提示: {unc}")

    def test_BP4_matched_scene_no_false_uncovered(self):
        """负向半条：命中激活表的场景不得误报「场景未命中」。"""
        unc = reason("住宅", "分户墙").get("未覆盖领域", [])
        self.assertFalse(any("场景未命中" in u for u in unc),
                         f"命中场景误报场景未命中: {unc}")

    # ---- 断点6：厨卫湿区归入空间类型维度（别名路径复活）----
    def test_BP6_wet_area_matches_via_space_dimension(self):
        """("住宅","卫生间")/("住宅","厨房") 经 SPACE_ALIASES→厨卫湿区 须命中激活表，不再降级。"""
        for sp in ("卫生间", "厨房", "厨卫湿区"):
            r = reason("住宅", sp)
            self.assertTrue(r["适用标准集"], f"住宅|{sp} 命中厨卫湿区行但适用标准集为空")
            unc = r.get("未覆盖领域", [])
            self.assertFalse(any("场景未命中" in u for u in unc),
                             f"住宅|{sp} 应经别名命中厨卫湿区，却报场景未命中: {unc}")

    def test_BP6_acoustic_demands_accepted(self):
        """吸声/撞击声 是 IC-10 性能需求枚举成员，须能激活且不崩溃（遗漏A：契约补枚举）。"""
        for d in ("吸声", "撞击声", "隔声"):
            r = reason("住宅", "楼板", demands=[d])
            self.assertIsInstance(r["适用标准集"], list, f"性能需求 {d} 激活异常")

    # ---- 断点5：外协占位改结构化「外部协同」字段对外可见 ----
    def test_BP5_external_collab_structured_visible(self):
        """住宅+厨卫湿区触发 waterproof(外部协同)，须出结构化「外部协同」条目而非被静默去重。"""
        r = reason("住宅", "卫生间")
        self.assertIn("外部协同", r, "厨卫湿区未产出结构化「外部协同」字段")
        collab = r["外部协同"]
        self.assertTrue(collab, "「外部协同」为空")
        item = collab[0]
        self.assertEqual(item["协同技能"], "waterproofing-expert")
        # 话术须与 interface-contracts.md 头部记录一致：已迁出至独立项目，非「待建」
        self.assertIn("已迁出", item["技能状态"],
                      f"外协话术与迁出记录矛盾（不得为「待建」）: {item['技能状态']}")
        self.assertNotIn("待建", item["技能状态"])
        # 占位「（…」不得再泄漏进对外标准编号集
        for s in r["适用标准集"]:
            self.assertFalse(s["标准编号"].startswith("（"),
                             f"外协占位泄漏进适用标准集: {s['标准编号']}")

    def test_BP5_external_collab_carries_degradation_evidence(self):
        """每条「外部协同」须附一条 degradation 证据（M6：外协不得静默）。

        判据须锁定外协专属证据（规则来源含「外部协同」），否则会被「地方标准不适用」
        那条无关 degradation 证据顶替而恒真（反向注入4 实测：松判据下回退仍绿＝空跑）。
        """
        r = reason("住宅", "卫生间")
        collab_ev = [ev for ev in r["证据对象"]
                     if ev["证据类型"] == "degradation" and "外部协同" in ev["规则来源"]]
        self.assertTrue(collab_ev, "外部协同缺专属 degradation 降级证据（规则来源未含「外部协同」）")
        self.assertIn("waterproofing-expert", collab_ev[0]["输出结论"])

    # ---- 断点8（P1·item11）：名称关键词不改 binding_support 角色 ----
    def test_BP8_name_keyword_does_not_override_binding_support_role(self):
        """断点8：L2/L3+binding_support 标准角色恒 design_basis，名称含「测量/评价」不改角色。

        第三方审阅 T-A1 曾推定「名称差分会改角色」，反事实实测推翻（CG-20260917-004）：名称关键词
        仅在 sre_reasoner.py:697（非 L1 且非 L2/L3-binding_support 支）参与 verification_reference 判定，
        而 DB/DBJ 设计验收类属 L2/binding_support，在 :695-696 即定 design_basis、永不到达 :697。
        正向对照：名称同样含「测量/评价」但非 L1、非 binding_support 者仍落 verification_reference，
        证明名称分支为活代码、只是被 binding_support 支遮蔽——本守卫因此非恒真空跑（回退分支序即转红）。
        """
        # 遮蔽组：L2/binding_support + 名称含「评价」→ 角色恒 design_basis（不被名称改写）
        for no in ("DB33/T 1168-2019", "DBJ/T 15-208-2020"):
            c = classify_standard(no, [])
            self.assertEqual(c["层级"], "L2", f"{no} 应为 L2（断点7 裁定）")
            self.assertEqual(c["权限"], "binding_support", f"{no} 应为 binding_support")
            self.assertIn("评价", sre_reasoner._standard_name(no),
                          f"{no} 前置条件不成立：名称须含「评价」才能检验是否被改写")
            role = sre_reasoner._apply_applicability([c], None, [])[0]["角色"]
            self.assertEqual(role, "design_basis",
                             f"{no} 名称含「评价」但角色应恒 design_basis（binding_support 支遮蔽 :697 名称支）")
        # 正向对照：名称含测量/评价但未被 L1/binding_support 遮蔽 → verification_reference（名称支为活代码）
        control = []
        for k, v in sre_reasoner.STANDARD_NAMES.items():
            if "测量" not in v and "评价" not in v:
                continue
            c = classify_standard(k, [])
            if c["层级"] != "L1" and c["权限"] != "binding_support":
                control.append((k, c))
            if len(control) >= 3:
                break
        self.assertTrue(control, "断点8 对照空跑：无「名称含测量/评价且未被遮蔽」的标准，守卫失去证伪力")
        for no, c in control:
            role = sre_reasoner._apply_applicability([c], None, [])[0]["角色"]
            self.assertEqual(role, "verification_reference",
                             f"{no} 对照：名称含测量/评价且未被遮蔽 → 应 verification_reference（:697 活代码）")


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
        self._saved_activation = dict(sre_reasoner.ACTIVATION_TABLE)
        sre_reasoner._load_standards_index()

    def tearDown(self) -> None:
        for target, saved in ((sre_reasoner.STANDARD_STATUS, self._saved_status),
                              (sre_reasoner.STANDARD_NAMES, self._saved_names),
                              (sre_reasoner.ACTIVATION_TABLE, self._saved_activation)):
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

    判据源《文档/SRE确定性体检设计方案_v1.0.md》§3.2。**自退役规则（§6.2）**：用例转成
    unexpected success 即说明对应缺陷已由 `sre_reasoner.py` 真实修复——此时必须摘掉装饰器、
    把断言转为正向常态断言，**禁止回退或注释掉被测代码的修复来让用例重新"预期失败"**。
    unexpected success 会让 `wasSuccessful()` 返回 False、门禁 exit 1，这是设计意图而非故障。

    **挂档历史**：T-B1、T-B7 随 CG-20260916-003 修复摘档；T-B4 随 CG-20260916-004 修复摘档，
    判据同步收紧为「拆分主态精确属 IC-10 契约枚举 + 回串无损」（旧前缀口径作废）；T-B3 随
    CG-20260916-005 补录 `acoustic(贡献)`／`acoustic(吸声)`／`acoustic(边界提示)` 三键后摘档。
    本组四项现均为正向常态断言，**已无 `expectedFailure` 挂档项**。
    """

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

    def test_TB4_status_read_by_header(self):
        truth = _main_table_truth()
        enum = _status_enum()
        contract_enum = _contract_ic10_status_enum()
        mismatch = {k: (sre_reasoner.STANDARD_STATUS.get(k), v)
                    for k, v in truth.items() if sre_reasoner.STANDARD_STATUS.get(k) != v}
        # CG-20260916-004 起收紧：状态单元按 §4 契约口径拆为（主态, 括注），主态须**精确**属
        # IC-10 枚举成员（前缀口径作废——它曾把「现行有效（…）」整串放行到输出侧）
        out_of_enum = {k: v for k, v in sre_reasoner.STANDARD_STATUS.items()
                       if sre_reasoner._split_status(v)[0] not in contract_enum}
        # 拆分必须无损：主态 + 括注要能原样回串为索引状态单元，否则「已废止（无替代）」类限定丢失
        lossy = {k: v for k, v in sre_reasoner.STANDARD_STATUS.items()
                 if (lambda h, t: h + (f"（{t}）" if t else ""))(*sre_reasoner._split_status(v)) != v}
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
            f"主表 {len(truth)} 项中 {len(mismatch)} 项加载态≠表头真值；加载表 {len(sre_reasoner.STANDARD_STATUS)} 项中"
            f"拆分主态越出契约枚举 {len(out_of_enum)} 项、有损拆分 {len(lossy)} 项；"
            f"{conversion or '状态转换项未测（枚举已改名）'}",
            "状态一律按表头列名读取（与表头感知真值同值）、拆分主态精确属 IC-10 契约枚举且回串无损，"
            "且 被部分替代 与 过渡期 不得互转",
            _loc(("固定列号取值", _assign_line("STANDARD_STATUS")),
                 ("_load_standards_index 定义", _def_line("_load_standards_index")),
                 ("时间状态拆分", _def_line("_split_status")),
                 ("时间状态映射", _def_line("_apply_applicability"))),
            "A", touched=set(mismatch) | set(out_of_enum) | set(lossy),
            violated=bool(mismatch or out_of_enum or lossy or conversion_bad),
        )
        self.assertEqual(mismatch, {}, "加载状态与表头真值不一致")
        self.assertGreater(len(contract_enum), 0, "IC-10 契约枚举现读为空，越界判据不可用")
        self.assertTrue(_contract_declares("状态注记"),
                        "引擎可输出 状态注记，但 IC-10 Schema 未声明该字段")
        self.assertEqual(out_of_enum, {}, "拆分主态越出 IC-10 契约枚举")
        self.assertEqual(lossy, {}, "状态单元拆分有损，括注限定被丢弃")
        if conversion:
            self.assertFalse(conversion_bad, f"{conversion}｜被部分替代 被方向性改写为 过渡期")

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

    **挂档历史**：T-B2 随 CG-20260916-004 摘档，并加正向断言「降级值须属 IC-10 契约取值集且
    全表唯一」；T-B5、T-B6 随 CG-20260916-005 摘档（空族上报 / 全国基线可叠加），各加一条收紧
    用例——T-B5 负向路径（合成无映射域）、T-B6 逐地点正向期望集。**行为组 T-B1—T-B7 七项至此
    全部转正，本文件不再挂 `expectedFailure`。**
    """

    def test_TB2_unregistered_id_degrades(self):
        enum = _status_enum()
        contract_enum = _contract_ic10_status_enum()
        probes = [_probe_id() for _ in range(5)]
        got = {p: sre_reasoner._standard_status(p) for p in probes}
        # 导入态（setUp 快照、未经显式加载）下锚定编号走同一兜底分支——§9.1 判该行为 anchor=true 的来源
        anchors, _ = _anchor_ids()
        sre_reasoner.STANDARD_STATUS.clear()
        sre_reasoner.STANDARD_STATUS.update(self._saved_status)
        anchor_fallback = sorted(a for a in (anchors or set()) if a not in self._saved_status)
        got |= {a: sre_reasoner._standard_status(a) for a in anchor_fallback}
        deterministic = {k: v for k, v in got.items() if v in enum}
        degraded = {k: v for k, v in got.items() if v not in enum}
        off_contract = {k: v for k, v in degraded.items() if v not in contract_enum}
        _record_signal(
            "T-B2", "DEGRADE",
            f"{len(probes)} 个随机不存在编号 + 导入态未登记的锚定编号 {len(anchor_fallback)} 条，"
            f"经 _standard_status() 得确定性状态 {len(deterministic)} 项："
            f"{sorted(set(deterministic.values()))}（触 SR-R-P0-2）；"
            f"降级侧 {len(degraded)} 项取值 {sorted(set(degraded.values()))}，越出契约取值集 {len(off_contract)} 项",
            "未登记编号不得返回任何 §1.1 确定性状态，须落 IC-10 契约取值集内的显式降级态且全表同值",
            _loc(("_standard_status 定义（含兜底默认值）", _def_line("_standard_status"))),
            "S", touched=set(deterministic) | set(off_contract),
            violated=bool(deterministic or off_contract),
        )
        self.assertEqual(deterministic, {}, "对输入域无界的未登记编号给出了确定性状态")
        self.assertGreater(len(contract_enum), 0, "IC-10 契约枚举现读为空，降级判据不可用")
        self.assertEqual(off_contract, {}, "降级输出越出 IC-10 契约取值集（臆造词）")
        self.assertEqual(len(set(degraded.values())), 1, "兜底返回值不唯一，降级口径不确定")

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

    def test_TB5_empty_family_negative_path(self):
        """摘档收紧：矩阵内已无空族，故合成注入无映射域，验上报机制而非数据碰巧非空。"""
        fake = "synthetic(无映射域)"
        self.assertNotIn(fake, sre_reasoner.DOMAINS, "合成域撞上真实映射键，负向取证失效")
        project_type, space_type = next(iter(sre_reasoner.ACTIVATION_TABLE))
        sre_reasoner.ACTIVATION_TABLE[project_type, space_type] = list(
            sre_reasoner.ACTIVATION_TABLE[project_type, space_type]) + [fake]
        response = reason(project_type, space_type, location="全国")
        empty = self._empty_families(response)
        uncovered = response.get("未覆盖领域", [])
        self.assertIn(fake, empty, "合成域未产出空标准族，负向路径根本没走到")
        self.assertTrue(any(fake in u for u in uncovered),
                        f"空标准族未上报 未覆盖领域：{uncovered}")

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

    def test_TB6_national_and_local_coexist(self):
        """摘档收紧：从「跨地点差分」升级为「逐地点正向期望集」，期望值取自 DOMAINS 现读。"""
        missing: list[tuple[str, str, str]] = []
        for project_type, space_type, demands in SCENARIOS:
            activated, _ = sre_reasoner._activate_domains(
                project_type, space_type, demands, [])
            for location in [x for x in LOCATIONS if x]:
                got = _applicable_ids(project_type, space_type, demands, location)
                for domain in sorted(activated):
                    mapping = sre_reasoner.DOMAINS.get(domain, {})
                    expect = set(mapping.get("全国", [])) | set(mapping.get(location, []))
                    missing += [(domain, location, i) for i in sorted(
                        {e for e in expect - got if not e.startswith("（")})]
        self.assertEqual(missing, [],
                         f"全国基线或地方增量在该地点缺失：{missing[:6]}")


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
