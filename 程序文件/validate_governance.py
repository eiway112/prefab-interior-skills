#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装配式装修技能合集 — 治理文件契约校验脚本
validate_governance.py v1.5.1

校验五类治理文件的一致性和完整性：
  1. redlines-registry.md  — 红线计数一致性（声明 vs 实际 vs 统计表，统计表按表头动态解析）
  2. interface-contracts.md — IC-02/IC-03/IC-05/IC-06/IC-07/IC-08/IC-09/IC-10/IC-11/IC-12/IC-13/IC-14 JSON Schema 必填字段完整性
  3. standards-index.md     — 标准状态枚举合法性（实际落检）+ 时间状态双向检查
                              （实施日期已过仍标"即将实施"→FAIL）+ 核验过期预警
  4. 跨文件漂移反查          — 项目索引/SRE/standards-index §10.1 中的手写计数
                              与注册表本体动态统计值比对，不一致即 FAIL
  5. SRE 静态体检 T-A1—T-A5  — 运行时 sre_reasoner.py 硬编码字面量（AST 提取，不 import）
                              与 standards-index.md 双源一致性 + 索引本体自洽 + 锚定集守卫
                              首轮一律 WARN（不计 fail_count），不打破 exit code 基线
                              判据见《文档/SRE确定性体检设计方案_v1.0.md》§3.1

v1.1 变更（2026-08-06，CG-20260806-008）：
  - 修复 §十一/十二 统计表硬编码 6 技能导致 WS 加入后误判合计（改为按表头动态解析）
  - 修复标准编号解析器遗漏 T/团标、JG/T、HG/T、SJG、RISN-TG、DBJ、图集编号（46→全量识别）
  - 修复非法状态检查空实现（现按行实际抽取状态单元格并比对枚举）
  - 新增时间状态反向检查：实施日期 ≤ 今天但状态仍为"即将实施" → FAIL
  - 新增检查 4：跨文件计数漂移反查（计数以脚本统计本体为准）

v1.3 变更（2026-08-07，CG-20260807-012）：
  - 检查 2 校验范围由 4 条扩展至 8 条：新增 IC-02/IC-05/IC-06/IC-07 请求 Schema 必填字段校验
    （IC-01/IC-04 尚无 JSON Schema，仍为最小字段约束过渡版，暂不纳入）

v1.4 变更（2026-08-13，CG-20260813-037）：
  - 检查 2 校验范围由 9 条扩展至 12 条：新增 IC-12（QA）/IC-13（GS）/IC-14（OR→AC）
    请求 Schema 必填字段校验

v1.5 变更（2026-09-15，CG-20260915-001）：
  - 新增检查 5：SRE 静态体检 T-A1—T-A5（设计方案 §3.1 静态组，载体 A）
  - 新增运行时常量 RUNTIME_SKILLS/SRE_DIR/RUNTIME_SHARED_DIR 与 --runtime-dir 选项；
    运行时目录不可达时降级为 WARN，不 FAIL（无技能仓的机器上门禁不炸）
  - check_standards 返回值由 actual_count 扩为 (actual_count, std_rows, std_names)，
    并在既有表头判别分支内新增标准名称抽取（标准名称／图集名称互为别名），
    供 T-A1—T-A3 复用同一次遍历产物，不做第二趟解析
  - T-A4 三查与 T-A5Ⅰ 的解析口径为表头感知（先按表头判别表类型，再按列名取值），
    不复用被测代码 sre_reasoner.py:247 的固定列号假设（设计方案 §2 自我更正记录证明
    该假设会产出错误数字）

v1.5.1 变更（2026-09-15，CG-20260915-001 复核整改 F-01/F-02）：
  - T-A5Ⅱ 计数分母改为被命中的锚定条目数（设计 §3.1 判据为 ∀ a ∈ 锚定集），
    原先按"命中锚定的信号条数"计数，与随后 info 行列出的命中编号数自相矛盾
  - T-A5Ⅱ 文案显式声明只聚合已实装的静态组 T-A1—T-A4，行为组未实装故计数
    低于设计全组实测值，不得据此判漏报

用法：
  python validate_governance.py
  python validate_governance.py --dir <项目根目录>
  python validate_governance.py --runtime-dir <运行时技能目录>
  python validate_governance.py --verbose

依赖：Python 3.8+（仅标准库）
"""

import ast
import re
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# ── 默认路径 ──────────────────────────────────────────────
# 脚本位于 _src/，治理文件位于 _专题_技能合集策划/
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE = SCRIPT_DIR.parent / "_专题_技能合集策划"

# ── 运行时技能目录（L2 SOT，检查 5 的数据源）─────────────
RUNTIME_SKILLS = Path.home() / ".qoder" / "skills"
SRE_DIR = RUNTIME_SKILLS / "prefab-standards-reviewer"
RUNTIME_SHARED_DIR = RUNTIME_SKILLS / "shared"

# ── 输出工具 ──────────────────────────────────────────────
class Report:
    """结构化校验报告"""
    def __init__(self):
        self.sections: List[Dict] = []
        self.current_section: Optional[Dict] = None

    def section(self, name: str):
        self.current_section = {"name": name, "items": [], "status": "PASS"}
        self.sections.append(self.current_section)

    def ok(self, msg: str):
        self.current_section["items"].append(("PASS", msg))

    def fail(self, msg: str):
        self.current_section["items"].append(("FAIL", msg))
        self.current_section["status"] = "FAIL"

    def warn(self, msg: str):
        self.current_section["items"].append(("WARN", msg))
        if self.current_section["status"] == "PASS":
            self.current_section["status"] = "WARN"

    def info(self, msg: str):
        self.current_section["items"].append(("INFO", msg))

    def print_report(self):
        total_pass = sum(1 for s in self.sections for lv, _ in s["items"] if lv == "PASS")
        total_fail = sum(1 for s in self.sections for lv, _ in s["items"] if lv == "FAIL")
        total_warn = sum(1 for s in self.sections for lv, _ in s["items"] if lv == "WARN")

        print("=" * 70)
        print("  装配式装修技能合集 — 治理文件契约校验报告")
        print(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        for sec in self.sections:
            icon = {"PASS": "[OK]", "FAIL": "[!!]", "WARN": "[??]"}[sec["status"]]
            print(f"\n{icon} {sec['name']}")
            print("-" * 50)
            for level, msg in sec["items"]:
                prefix = {"PASS": "  +", "FAIL": "  x", "WARN": "  !", "INFO": "  -"}[level]
                print(f"{prefix} {msg}")

        print("\n" + "=" * 70)
        overall = "PASS" if total_fail == 0 else "FAIL"
        print(f"  总评：{overall}  |  通过 {total_pass}  失败 {total_fail}  警告 {total_warn}")
        print("=" * 70)
        return total_fail


# ── 文件读取 ──────────────────────────────────────────────
def read_file(path: Path, label: str) -> Optional[str]:
    if not path.exists():
        print(f"[ERROR] {label} 不存在: {path}")
        return None
    return path.read_text(encoding="utf-8")


# ── 检查 1：红线计数一致性 ────────────────────────────────
def check_redlines(text: str, report: Report):
    report.section("红线注册表 — 计数一致性")

    # 1a. 头部声明总数
    m_total = re.search(r"注册红线总数\*\*：(\d+)\s*条", text)
    if not m_total:
        report.fail("未找到头部'注册红线总数'声明")
        return
    declared_total = int(m_total.group(1))
    report.info(f"头部声明总数：{declared_total} 条")

    # 1b. 头部声明分技能明细
    header_detail = re.search(
        r"注册红线总数\*\*：\d+\s*条（([^）]+)）", text
    )
    header_per_skill = {}
    if header_detail:
        for m in re.finditer(r"(\w+)\s+(\d+)\s*条", header_detail.group(1)):
            header_per_skill[m.group(1)] = int(m.group(2))
    report.info(f"头部声明分技能：{header_per_skill}")

    # 1c. 已注册技能数
    m_skills = re.search(r"已注册技能数\*\*：(\d+)\s*/\s*(\d+)", text)
    if m_skills:
        registered_skills = int(m_skills.group(1))
        total_skill_slots = int(m_skills.group(2))
        report.info(f"已注册技能数：{registered_skills} / {total_skill_slots}")
    else:
        registered_skills = 0
        report.warn("未找到'已注册技能数'声明")

    # 1d. 各技能章节声明（P0+P1+P2=合计）
    section_pattern = re.compile(
        r"红线数量：P0\s+(\d+)\s*条\s*\+\s*P1\s+(\d+)\s*条"
        r"(?:\s*\+\s*P2\s+(\d+)\s*条)?\s*=\s*共\s+(\d+)\s*条"
    )
    section_decls = []
    for m in section_pattern.finditer(text):
        p0, p1 = int(m.group(1)), int(m.group(2))
        p2 = int(m.group(3)) if m.group(3) else 0
        total = int(m.group(4))
        section_decls.append((p0, p1, p2, total))

    report.info(f"技能章节声明数：{len(section_decls)} 个")
    for i, (p0, p1, p2, total) in enumerate(section_decls):
        computed = p0 + p1 + p2
        if computed != total:
            report.fail(f"第{i+1}个技能章节：P0({p0})+P1({p1})+P2({p2})={computed}，但声明共{total}条")
        else:
            report.ok(f"第{i+1}个技能章节：{p0}+{p1}+{p2}={total} 内部一致")

    section_sum = sum(d[3] for d in section_decls)
    if section_sum != declared_total:
        report.fail(f"各技能章节合计 {section_sum} 条 ≠ 头部声明 {declared_total} 条")
    else:
        report.ok(f"各技能章节合计 {section_sum} 条 = 头部声明 {declared_total} 条")

    # 1e. 实际红线表格行数（按技能标识分组）
    redline_rows = re.findall(
        r"^\|\s*(([A-Z]+)-R-P(\d)-\d+)\s*\|", text, re.MULTILINE
    )
    actual_counts: Dict[str, int] = {}
    actual_by_priority: Dict[Tuple[str, str], int] = {}
    for full_id, skill, priority in redline_rows:
        actual_counts[skill] = actual_counts.get(skill, 0) + 1
        key = (skill, f"P{priority}")
        actual_by_priority[key] = actual_by_priority.get(key, 0) + 1

    report.info(f"实际红线表格行数：{sum(actual_counts.values())} 行，"
                f"分技能：{dict(actual_counts)}")

    # 1f. 实际总数 vs 声明总数
    actual_total = sum(actual_counts.values())
    if actual_total != declared_total:
        report.fail(f"实际表格行数 {actual_total} ≠ 头部声明 {declared_total}")
    else:
        report.ok(f"实际表格行数 {actual_total} = 头部声明 {declared_total}")

    # 1g. 实际 vs 各技能章节声明 — 从§标题提取技能标识顺序
    skill_section_ids = []
    for m in re.finditer(
        r"^##\s+[一二三四五六七八九十]+、已注册红线：(.+?)（(\w+)）",
        text, re.MULTILINE
    ):
        skill_section_ids.append(m.group(2))

    # 如果标题没提取全，从标识映射表补充
    if len(skill_section_ids) < len(section_decls):
        for m in re.finditer(
            r"\|\s*\*\*(\w+)\*\*\s*\|\s*[^|]+\|\s*[^|]+\|\s*✅\s*已注册",
            text
        ):
            sid = m.group(1)
            if sid not in skill_section_ids:
                skill_section_ids.append(sid)

    for i, (p0, p1, p2, total) in enumerate(section_decls):
        if i < len(skill_section_ids):
            sid = skill_section_ids[i]
            actual = actual_counts.get(sid, 0)
            if actual != total:
                report.fail(f"{sid}：表格实际 {actual} 行 ≠ 章节声明 {total} 条")
            else:
                report.ok(f"{sid}：表格实际 {actual} 行 = 章节声明 {total} 条")

            for plevel, declared_count in [("P0", p0), ("P1", p1), ("P2", p2)]:
                actual_p = actual_by_priority.get((sid, plevel), 0)
                if actual_p != declared_count:
                    report.fail(f"{sid} {plevel}：表格 {actual_p} 行 ≠ 声明 {declared_count} 条")

    # 1h. 统计表（合计行）— 按表头动态解析，不硬编码技能数
    # 表头形如：| 优先级 | OR（总入口） | PW（隔墙） | ... | 合计 | 占比 |
    # 合计行形如：| **合计** | **8** | **18** | ... | **77** | 100% |
    stats_skill_order: List[str] = []
    header_line_match = re.search(
        r"^\|\s*优先级\s*\|(.+)\|\s*合计\s*\|", text, re.MULTILINE
    )
    if header_line_match:
        for cell_m in re.finditer(
            r"\b([A-Z]+)\s*(?:（[^）]*）)?", header_line_match.group(1)
        ):
            stats_skill_order.append(cell_m.group(1))

    total_line_match = re.search(r"^\|\s*\*\*合计\*\*\s*\|(.+)$", text, re.MULTILINE)
    if header_line_match and total_line_match:
        stats_values = [
            int(v) for v in re.findall(r"\*\*(\d+)\*\*", total_line_match.group(1))
        ]
        # 数值单元格 = 各技能列 + 合计列（末尾"占比"列无加粗数字）
        if len(stats_values) == len(stats_skill_order) + 1:
            stats_per_skill = dict(zip(stats_skill_order, stats_values[:-1]))
            stats_total = stats_values[-1]

            if stats_total != declared_total:
                report.fail(f"统计表合计 {stats_total} ≠ 头部声明 {declared_total}")
            else:
                report.ok(f"统计表合计 {stats_total} = 头部声明 {declared_total}")

            for sid in stats_skill_order:
                actual = actual_counts.get(sid, 0)
                if stats_per_skill[sid] != actual:
                    report.fail(
                        f"统计表 {sid} {stats_per_skill[sid]} ≠ 表格实际 {actual}"
                    )
                else:
                    report.ok(f"统计表 {sid} {stats_per_skill[sid]} = 表格实际 {actual}")
        else:
            report.fail(
                f"统计表数值单元格数 {len(stats_values)} 与表头技能列数 "
                f"{len(stats_skill_order)}+1 不匹配（表格结构可能已变化）"
            )
    elif total_line_match:
        report.warn("找到合计行但未找到统计表表头（格式可能变化）")
    else:
        report.warn("未找到统计表的合计行（可能格式变化）")

    # 1i. 头部声明分技能 vs 实际
    for sid, count in header_per_skill.items():
        actual = actual_counts.get(sid, 0)
        if actual != count:
            report.fail(f"头部声明 {sid} {count} 条 ≠ 表格实际 {actual} 行")
        else:
            report.ok(f"头部声明 {sid} {count} 条 = 表格实际 {actual} 行")


# ── 检查 2：接口契约必填字段 ─────────────────────────────
def check_interfaces(text: str, report: Report):
    report.section("接口契约 — IC-02/IC-03/IC-05/IC-06/IC-07/IC-08/IC-09/IC-10/IC-11/IC-12/IC-13/IC-14 Schema 必填字段")

    for ic_id in ["IC-02", "IC-03", "IC-05", "IC-06", "IC-07", "IC-08", "IC-09", "IC-10", "IC-11", "IC-12", "IC-13", "IC-14"]:
        # 提取 JSON Schema 块
        schema_pattern = re.compile(
            rf'\*请求 Schema（{re.escape(ic_id)}-Request）\*：\s*\n\s*```json\s*\n(.*?)```',
            re.DOTALL
        )
        m = schema_pattern.search(text)
        if not m:
            report.fail(f"{ic_id}：未找到请求 Schema JSON 块")
            continue

        try:
            schema = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            report.fail(f"{ic_id}：JSON Schema 解析失败 — {e}")
            continue

        # 顶层 required
        top_required = schema.get("required", [])
        if not top_required:
            report.fail(f"{ic_id}：顶层 required 为空")
            continue

        top_props = schema.get("properties", {})
        report.info(f"{ic_id}：顶层 required = {top_required}")

        for field in top_required:
            if field in top_props:
                report.ok(f"{ic_id}：必填字段 '{field}' 已定义")
            else:
                report.fail(f"{ic_id}：必填字段 '{field}' 在 required 中但 properties 未定义")

        # 嵌套 required
        for prop_name, prop_def in top_props.items():
            if isinstance(prop_def, dict) and prop_def.get("type") == "object":
                nested_required = prop_def.get("required", [])
                nested_props = prop_def.get("properties", {})
                for nf in nested_required:
                    if nf in nested_props:
                        report.ok(f"{ic_id}.{prop_name}：嵌套必填 '{nf}' 已定义")
                    else:
                        report.fail(f"{ic_id}.{prop_name}：嵌套必填 '{nf}' 在 properties 未定义")

        # $schema / $id
        if "$schema" not in schema:
            report.warn(f"{ic_id}：缺少 $schema 声明")
        if "$id" not in schema:
            report.warn(f"{ic_id}：缺少 $id 声明")

        # 枚举值完整性检查
        for prop_name, prop_def in top_props.items():
            if isinstance(prop_def, dict) and "enum" in prop_def:
                report.info(f"{ic_id}.{prop_name}：枚举值 = {prop_def['enum']}")

    # 额外：检查 IC 编号连续性
    ic_numbers = re.findall(r"##\s+(IC-\d+)", text)
    if ic_numbers:
        report.info(f"已定义接口编号：{ic_numbers}")


# ── 检查 3：标准索引状态 ─────────────────────────────────
def check_standards(text: str, report: Report):
    report.section("标准索引 — 状态合法性与核验时效")

    # 3a. 头部声明总数
    m_total = re.search(r"收录标准总数\*\*：(\d+)\s*条", text)
    if m_total:
        declared_total = int(m_total.group(1))
        report.info(f"头部声明收录总数：{declared_total} 条")
    else:
        declared_total = None
        report.warn("未找到头部'收录标准总数'声明")

    # 3b. 合法枚举值
    valid_status = {
        "现行有效", "即将实施", "过渡期",
        "已废止", "已废止（无替代）", "被部分替代",
        "被部分废止", "已废止（无直接替代）",
    }
    valid_verify = {
        "已官方核验", "待核验", "到期需复核", "无法核验"
    }

    # 3c. 解析标准表格行
    # 计数策略：按表头分流——表头含"核验日期/核验状态/核验结论"的为核验记录表，
    # 整表跳过；表头含"状态"列的为主表，主表内序号列为数字的行均计为 1 条标准
    # （覆盖 GB/行标/团标 T/XXX、图集、尺寸指南等全部条目形态）。
    # 范围：## 二、～## 七、（不含）。

    lines = text.split("\n")
    # 主体表区间：## 二、 ～ ## 七、（不含）
    body_start = body_end = None
    for i, line in enumerate(lines):
        if body_start is None and re.match(r"^##\s+二、", line):
            body_start = i
        elif body_start is not None and re.match(r"^##\s+七、", line):
            body_end = i
            break
    if body_start is None or body_end is None:
        report.fail("未定位到标准主体表区间（## 二、～## 七、），无法精确计数")
        body_start, body_end = 0, len(lines)

    invalid_status_found = []   # (std_id, suspect_value, line_no)
    no_status_rows = []          # (std_id, line_no)
    expired_review = []
    upcoming_impl = []           # 正常：未来实施
    overdue_status = []          # 异常：实施日期已过仍标"即将实施"
    premature_effective = []     # 异常：实施日期未到却标"现行有效"
    std_rows = []                # (std_id, line_no)
    today = datetime.now()
    six_months_ago = today - timedelta(days=183)

    sep_line = re.compile(r"^\|[\s:\-|]+\|$")
    status_bases = ("现行有效", "即将实施", "过渡期", "已废止", "被替代",
                    "被部分替代", "被部分废止")
    in_main_table = False     # 当前是否处于主表（含"状态"列）数据区
    std_names: Dict[str, str] = {}   # 编号 → 名称（主表名称列，供检查 5 复用）
    name_col: Optional[int] = None   # 当前主表的名称列号（按表头取值，非固定列）
    for idx in range(body_start, body_end):
        line = lines[idx].strip()
        if not line.startswith("|"):
            in_main_table = False
            continue
        if sep_line.match(line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue

        # 表头行识别：含"序号/标准编号/图集编号"表头字段
        if ("序号" in cells[0] or "标准编号" in cells[0] or "图集编号" in cells[0]
                or (len(cells) > 1 and ("标准编号" in cells[1]
                                        or "图集编号" in cells[1]))):
            header_joined = "|".join(cells)
            name_col = next(
                (i for i, c in enumerate(cells)
                 if "标准名称" in c or "图集名称" in c), None)
            if any(k in header_joined for k in ("核验日期", "核验状态", "核验结论")):
                in_main_table = False      # 核验记录表：不计入标准总数
                name_col = None
            elif "状态" in header_joined:
                in_main_table = True       # 主表：计入标准总数
            else:
                in_main_table = False
                name_col = None
            continue

        if not in_main_table or not cells[0].isdigit():
            continue

        std_id = cells[1].replace("**", "") if len(cells) > 1 else "?"
        line_no = idx + 1
        std_rows.append((std_id, line_no))
        if name_col is not None and name_col < len(cells):
            std_names.setdefault(std_id, cells[name_col].replace("**", "").strip())

        rest = cells[2:]
        # 状态抽取：按枚举前缀匹配（允许"现行有效（代替…）"等括号注记）
        status = None
        for c in rest:
            if any(c.startswith(b) for b in status_bases):
                status = c
                break
        if status is None:
            anchor_pos = None
            for j, c in enumerate(rest):
                if re.search(r"\d{4}-\d{2}-\d{2}", c) or re.fullmatch(r"\d{4}", c):
                    anchor_pos = j
            suspect = rest[anchor_pos + 1] if (
                anchor_pos is not None and anchor_pos + 1 < len(rest)
            ) else None
            if suspect:
                invalid_status_found.append((std_id, suspect, line_no))
            else:
                no_status_rows.append((std_id, line_no))
            continue

        # 时间状态双向检查（以行内实施日期为准）
        dates = re.findall(r"(\d{4}-\d{2}-\d{2})", line)
        impl_dates = []
        for d in dates:
            try:
                impl_dates.append(datetime.strptime(d, "%Y-%m-%d"))
            except ValueError:
                pass
        if status.startswith("即将实施"):
            if impl_dates and max(impl_dates) <= today:
                overdue_status.append(
                    (std_id, max(impl_dates).strftime("%Y-%m-%d"), line_no)
                )
            elif impl_dates:
                upcoming_impl.append(
                    (std_id, max(impl_dates).strftime("%Y-%m-%d"))
                )
        elif status.startswith("现行有效") and impl_dates and min(impl_dates) > today:
            premature_effective.append(
                (std_id, min(impl_dates).strftime("%Y-%m-%d"), line_no)
            )

    report.info(f"检测到标准表格行数（§二～§六主表）：{len(std_rows)} 行")

    # 核验日期只在"官方核验记录"区域检查
    verify_section_start = None
    verify_section_end = None
    for i, line in enumerate(lines):
        if "官方核验记录" in line and line.startswith("#"):
            verify_section_start = i + 1
        elif verify_section_start and line.startswith("## "):
            verify_section_end = i
            break
    if verify_section_start and not verify_section_end:
        verify_section_end = len(lines)

    if verify_section_start and verify_section_end:
        verify_text = "\n".join(lines[verify_section_start:verify_section_end])
        verify_std_pattern = re.compile(
            r"^\|\s*(?:\d+\s*\|\s*)?"
            r"((?:GB|JGJ|JC|JG|DB|T|RISN|HG|SJG|EN|ISO)[^|]*)"
            r"\|\s*(\d{4}-\d{2}-\d{2})",
            re.MULTILINE
        )
        for vm in verify_std_pattern.finditer(verify_text):
            std_id = vm.group(1).strip()
            review_date_str = vm.group(2)
            try:
                review_date = datetime.strptime(review_date_str, "%Y-%m-%d")
                if review_date < six_months_ago:
                    expired_review.append((std_id, review_date_str, 0))
            except ValueError:
                pass

    # 3e. 实际标准数 vs 声明数（精确解析后不应有差异，差异即 FAIL）
    actual_count = len(std_rows)
    if declared_total and actual_count != declared_total:
        report.fail(f"主体表标准行数 {actual_count} ≠ 头部声明 {declared_total}")
    elif declared_total:
        report.ok(f"主体表标准行数 {actual_count} = 头部声明 {declared_total}")

    # 3f. 报告结果
    if invalid_status_found:
        for std_id, suspect, line_no in invalid_status_found:
            report.fail(f"L{line_no} {std_id}：状态值 '{suspect}' 不在合法枚举内")
    else:
        report.ok("所有标准状态值均在合法枚举范围内")

    for std_id, line_no in no_status_rows:
        report.warn(f"L{line_no} {std_id}：未识别到状态列，请人工检查表格结构")

    for std_id, impl_date, line_no in overdue_status:
        report.fail(
            f"L{line_no} {std_id}：实施日期 {impl_date} 已过，"
            f"状态仍为'即将实施'（状态漂移，须更新）"
        )

    for std_id, impl_date, line_no in premature_effective:
        report.warn(
            f"L{line_no} {std_id}：实施日期 {impl_date} 未到，状态却为'现行有效'"
        )

    if expired_review:
        for std_id, date, line_no in expired_review:
            report.warn(f"{std_id}：核验日期 {date} 已超 6 个月，建议复核")
    else:
        report.ok("无超期未核验标准（6 个月内）")

    if upcoming_impl:
        for std_id, impl_date in upcoming_impl:
            report.info(f"{std_id}：即将于 {impl_date} 实施，关注过渡期安排")

    # 3g. 废止标准是否标注替代
    deprecated_pattern = re.compile(
        r"^\|\s*((?:GB|JGJ|JC|DB|EN|ISO)[/\s]?\s*T?\s*[\d]+(?:[.-]\d+)*[^|]*)"
        r"\|[^|]*已废止[^|]*\|",
        re.MULTILINE
    )
    for m in deprecated_pattern.finditer(text):
        std_id = m.group(1).strip()
        row_text = m.group(0)
        if "替代" not in row_text and "无替代" not in row_text:
            report.warn(f"{std_id}：标记为已废止但未注明替代标准")

    # 3h. 核验状态分布统计
    verify_counts = {v: 0 for v in valid_verify}
    for line in lines:
        for v in valid_verify:
            if v in line and "|" in line:
                verify_counts[v] = verify_counts.get(v, 0) + 1

    active_verify = {k: v for k, v in verify_counts.items() if v > 0}
    if active_verify:
        report.info(f"核验状态分布：{active_verify}")

    return actual_count, std_rows, std_names


# ── 检查 4：跨文件计数漂移反查 ────────────────────────────
def check_cross_file_drift(base_dir: Path, report: Report,
                           si_text: Optional[str], rl_text: Optional[str],
                           ic_text: Optional[str], std_actual: Optional[int]):
    """以治理本体动态统计值为基准，反查各文档中的手写计数/版本号。

    基准值全部来自本次运行对各注册表本体的解析结果，不信任任何手写计数。
    """
    report.section("跨文件漂移反查 — 手写计数 vs 本体统计")

    # 基准值提取
    rl_total = None
    registered_skills = None
    if rl_text:
        m = re.search(r"注册红线总数\*\*：(\d+)\s*条", rl_text)
        if m:
            rl_total = int(m.group(1))
        m = re.search(r"已注册技能数\*\*：(\d+)\s*/", rl_text)
        if m:
            registered_skills = int(m.group(1))
    ic_version = None
    if ic_text:
        m = re.search(r"契约版本\*\*：(v[\d.]+)", ic_text)
        if m:
            ic_version = m.group(1)

    report.info(
        f"本体基准：标准 {std_actual} 条 / 红线 {rl_total} 条 / "
        f"已注册技能 {registered_skills} / 契约 {ic_version}"
    )

    # 4a. standards-index §10.1 "维护 N 条标准"
    if si_text and std_actual is not None:
        m = re.search(r"维护\s*(\d+)\s*条标准", si_text)
        if m:
            v = int(m.group(1))
            if v != std_actual:
                report.fail(f"standards-index §10.1 写'维护 {v} 条标准' ≠ 本体 {std_actual} 条")
            else:
                report.ok(f"standards-index §10.1 '维护 {v} 条标准' = 本体统计")
        else:
            report.warn("standards-index 未找到 §10.1 '维护 N 条标准'表述（格式可能变化）")

    # 4b. SRE "完整 N 条目录"
    sre_path = base_dir / "standards-reasoning-rules.md"
    if sre_path.exists() and std_actual is not None:
        sre_text = sre_path.read_text(encoding="utf-8")
        m = re.search(r"完整\s*(\d+)\s*条目录", sre_text)
        if m:
            v = int(m.group(1))
            if v != std_actual:
                report.fail(f"SRE §2.4 写'完整 {v} 条目录' ≠ 本体 {std_actual} 条")
            else:
                report.ok(f"SRE §2.4 '完整 {v} 条目录' = 本体统计")
        else:
            report.warn("SRE 未找到'完整 N 条目录'表述（格式可能变化）")
    elif std_actual is not None:
        report.warn("standards-reasoning-rules.md 不存在，跳过 SRE 计数反查")

    # 4c. 项目策划方案索引（文档/）
    idx_path = base_dir.parent / "文档" / "项目策划方案索引.md"
    if idx_path.exists():
        idx_text = idx_path.read_text(encoding="utf-8")

        checks = []  # (描述, 手写值, 基准值)
        m = re.search(r"四层标准体系[^|\n]*共\s*(\d+)\s*条", idx_text)
        if m and std_actual is not None:
            checks.append(("项目索引·标准总数", int(m.group(1)), std_actual))

        for pat in (r"已注册红线\s*(\d+)\s*条",
                    r"redlines-registry\.md[^\n]*?（(\d+)\s*条、"):
            m = re.search(pat, idx_text)
            if m and rl_total is not None:
                checks.append(("项目索引·红线总数", int(m.group(1)), rl_total))
                break

        m = re.search(r"redlines-registry\.md[^\n]*?\d+\s*条[、，]\s*(\d+)\s*技能", idx_text)
        if m and registered_skills is not None:
            checks.append(("项目索引·已注册技能数", int(m.group(1)), registered_skills))

        m = re.search(r"interface-contracts\.md[^\n]*?\|\s*(v[\d.]+)\s*\|\s*$", idx_text, re.MULTILINE)
        if m and ic_version is not None:
            checks.append(("项目索引·契约版本", m.group(1), ic_version))

        if not checks:
            report.warn("项目策划方案索引中未定位到可反查的计数表述（格式可能变化）")
        for label, hand, base in checks:
            if hand != base:
                report.fail(f"{label} 手写值 '{hand}' ≠ 本体基准 '{base}'")
            else:
                report.ok(f"{label} '{hand}' = 本体基准")
    else:
        report.warn(f"项目策划方案索引不存在：{idx_path}")


# ── 检查 5：SRE 静态体检 T-A1 — T-A5 ─────────────────────
SEP_ROW_RE = re.compile(r"^\|[\s:\-|]+\|$")
ID_COL_ALIASES = ("标准编号", "图集编号")        # 图集编号是标准编号的合法别名
NAME_COL_ALIASES = ("标准名称", "图集名称")
STATUS_COLS = ("状态", "当前状态")
VERIFY_STATUS_COLS = ("核验结论",)
STD_ID_SHAPE = re.compile(
    r"^(?:GB|JGJ|JC|JG|DB|DBJ|SJG|HG|HJ|EN|ISO|RISN|T/|\d{2}[A-Z])")
VERSION_KEY_RE = re.compile(r"[-—]\d{4}$")
CJK_RUN_RE = re.compile(r"^([一-鿿]+)")


def md_cells(line: str) -> List[str]:
    return [c.strip().replace("**", "").strip()
            for c in line.strip().strip("|").split("|")]


def iter_md_tables(lines: List[str], lo: int, hi: int) -> List[Dict[str, Any]]:
    """表头感知地解析 markdown 表：表头 = 其后紧跟分隔行的那一行。

    无表头的连续块不产表（宁可漏检，也不猜列号）——被测代码 sre_reasoner.py:247
    的 parts[6] 固定列读法正是这里要避开的口径。
    """
    tables: List[Dict[str, Any]] = []

    def flush(group: List[Tuple[int, str]]):
        if len(group) >= 2 and SEP_ROW_RE.match(group[1][1]):
            tables.append({
                "header": md_cells(group[0][1]),
                "rows": [(n, md_cells(t)) for n, t in group[2:]
                         if not SEP_ROW_RE.match(t)],
            })

    group: List[Tuple[int, str]] = []
    for idx in range(max(0, lo), min(hi, len(lines))):
        raw = lines[idx].rstrip()
        if raw.strip().startswith("|"):
            group.append((idx + 1, raw))
        else:
            flush(group)
            group = []
    flush(group)
    return tables


def classify_index_table(header: List[str]) -> str:
    joined = "|".join(header)
    if "锚定ID" in joined:
        return "anchor"
    if any(k in joined for k in ("核验日期", "核验状态", "核验结论")):
        return "verify"
    if "状态" in joined:
        first = header[0] if header else ""
        if "序号" in first:
            return "main"
        if any(a in first for a in ID_COL_ALIASES):
            return "register"
    return "other"


def find_col(header: List[str], aliases, exact: bool = False) -> Optional[int]:
    for i, c in enumerate(header):
        if exact:
            if c in aliases:
                return i
        elif any(a in c for a in aliases):
            return i
    return None


def norm_std_id(raw: str) -> str:
    """编号归一：剥粗体/空白，切掉（2018 版）之类的括注与后附说明。"""
    s = (raw or "").strip()
    s = re.split(r"[（(，,；;、]", s)[0]
    return s.strip()


def find_section(lines: List[str], heading_pat: str) -> Tuple[Optional[int], Optional[int]]:
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m and re.search(heading_pat, m.group(2)):
            level = len(m.group(1))
            j = i + 1
            while j < len(lines):
                m2 = re.match(r"^(#+)\s", lines[j])
                if m2 and len(m2.group(1)) <= level:
                    break
                j += 1
            return i + 1, j
    return None, None


def parse_status_enum(lines: List[str]) -> Tuple[List[str], set]:
    """状态枚举取自索引 §1.1（SOT 文档），不取自门禁代码的手抄集合。"""
    lo, hi = find_section(lines, r"^1\.1\s")
    if lo is None:
        return [], set()
    values: List[str] = []
    started = False
    for tbl in iter_md_tables(lines, lo, hi):
        for _, cells in tbl["rows"]:
            first = cells[0] if cells else ""
            if "标准状态" in first:
                started = True
            elif "官方核验日期" in first:
                started = False
            if started:
                for c in cells:
                    values.extend(re.findall(r"`([^`]+)`", c))
    leads = [norm_std_id(v) for v in values]
    suffixes = {t[-1] for t in leads if t}
    return values, suffixes


def out_of_enum_status(cell: str, enum_vals: List[str], suffixes: set) -> Optional[str]:
    """返回越出枚举的状态用词；None 表示合法或根本不是状态表述。

    状态表述的形态判据：以枚举值前缀开头即合法；否则取行首连续中文词，
    仅当其末字落在「由枚举值派生的状态尾字集」内才认定为状态用词——
    据此把「条文级核验：…」这类说明性文字排除在检之外。
    """
    cell = (cell or "").strip()
    if not cell:
        return None
    for v in sorted(enum_vals, key=len, reverse=True):
        if cell.startswith(norm_std_id(v)):
            return None
    m = CJK_RUN_RE.match(cell)
    term = m.group(1) if m else ""
    if term and len(term) <= 8 and term[-1] in suffixes:
        return term
    return None


def extract_py_literals(text: str, names: List[str]) -> Dict[str, Any]:
    """AST 提取模块级字面量，不 import 被测代码（§3.1 静态组：不执行运行时代码）。"""
    out: Dict[str, Any] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    wanted = set(names)
    for node in ast.walk(tree):
        value = None
        targets: List[str] = []
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
            value = node.value
        if value is None:
            continue
        for t in targets:
            if t in wanted and t not in out:
                try:
                    out[t] = ast.literal_eval(value)
                except (ValueError, TypeError):
                    pass
    return out


def flatten_strings(obj: Any) -> List[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in flatten_strings(v)]
    if isinstance(obj, (list, tuple, set)):
        return [s for v in obj for s in flatten_strings(v)]
    return []


def std_id_refs(obj: Any) -> List[str]:
    """展平后的实标准编号（排除（外部 …技能协同）占位串与非编号文本）。"""
    return [norm_std_id(s) for s in flatten_strings(obj) if STD_ID_SHAPE.match(s.strip())]


def check_sre_static(base_dir: Path, runtime_dir: Path, report: Report,
                     si_text: Optional[str], std_rows: List[Tuple[str, int]],
                     std_names: Dict[str, str]):
    """T-A1—T-A5 静态体检。首轮一律 WARN（不计 fail_count），修复不等观察期。"""
    report.section("SRE 静态体检 — T-A1—T-A5（首轮 WARN，不打破 exit code 基线）")

    if not si_text:
        report.warn("standards-index.md 不可达，T-A1—T-A5 整体降级跳过")
        return

    sre_path = runtime_dir / "sre_reasoner.py"
    lits: Dict[str, Any] = {}
    if sre_path.exists():
        lits = extract_py_literals(
            sre_path.read_text(encoding="utf-8"),
            ["STANDARD_NAMES", "DOMAINS", "ANCHORS"])
        report.info(f"数据源：{sre_path}（AST 提取，未 import）")
    else:
        report.warn(f"运行时 sre_reasoner.py 不可达：{sre_path} → T-A1—T-A3 跳过，"
                    f"T-A4/T-A5 仍检（首轮降级，不 FAIL）")

    if not lits and not std_rows:
        return

    lines = si_text.split("\n")
    body_start = body_end = None
    for i, line in enumerate(lines):
        if body_start is None and re.match(r"^##\s+二、", line):
            body_start = i
        elif body_start is not None and re.match(r"^##\s+七、", line):
            body_end = i
            break
    if body_start is None or body_end is None:
        report.warn("未定位到索引主体表区间（## 二、～## 七、），T-A4 跳过")
        region_tables: List[Dict[str, Any]] = []
    else:
        region_tables = iter_md_tables(lines, body_start, body_end)

    main_tables = [t for t in region_tables
                   if classify_index_table(t["header"]) == "main"]
    verify_tables = [t for t in region_tables
                     if classify_index_table(t["header"]) == "verify"]

    # 索引侧动态集合（全部按表头列名取值）
    idx_ids: set = set()
    atlas_ids: set = set()
    for t in main_tables:
        id_col = find_col(t["header"], ID_COL_ALIASES)
        is_atlas = any(a in t["header"] for a in ("图集编号", "图集名称"))
        for _, cells in t["rows"]:
            if id_col is None or id_col >= len(cells) or not cells[id_col]:
                continue
            idx_ids.add(norm_std_id(cells[id_col]))
            if is_atlas:
                atlas_ids.add(norm_std_id(cells[id_col]))

    idx_names: Dict[str, str] = {norm_std_id(k): v for k, v in std_names.items()}

    signals: List[Dict[str, Any]] = []

    # ── T-A1 名称双源差分（判据：差分非空即报，不设数值阈值）────────
    sn = lits.get("STANDARD_NAMES")
    if isinstance(sn, dict):
        conflicts = []
        for key, sre_name in sn.items():
            nk = norm_std_id(key)
            idx_name = idx_names.get(nk)
            if idx_name is None or idx_name == sre_name:
                continue
            role_div = (("测量" in sre_name, "评价" in sre_name)
                        != ("测量" in idx_name, "评价" in idx_name))
            conflicts.append((nk, sre_name, idx_name, role_div))
        if conflicts:
            n_role = sum(1 for c in conflicts if c[3])
            signals.append({
                "id": "T-A1", "cat": "DRIFT",
                "ids": [c[0] for c in conflicts],
                "msg": (f"SRE STANDARD_NAMES 与索引主表名称差分 {len(conflicts)} 处"
                        f"（判据=差分非空即报，计数随键匹配情况变动，非断言常量；"
                        f"role_divergence {n_role} 处经 :506 改变 M4 角色与排序）"),
                "detail": [f"{c[0]}：SRE=「{c[1]}」/ 索引=「{c[2]}」"
                           + ("［role_divergence］" if c[3] else "")
                           for c in conflicts],
            })
        else:
            report.ok("T-A1：SRE 硬编码名称与索引主表名称零冲突")

    # ── T-A2 键闭合：DOMAINS 引用编号须都在索引主表内 ───────────────
    dm = lits.get("DOMAINS")
    if isinstance(dm, dict):
        refs = [r for r in std_id_refs(dm) if r not in atlas_ids]
        missing = sorted({r for r in refs if r not in idx_ids})
        if missing:
            signals.append({
                "id": "T-A2", "cat": "GAP", "ids": missing,
                "msg": (f"DOMAINS 引用的实标准编号 {len(missing)} 个不在索引主表"
                        f"（图集编号按 §四 行集动态豁免，占位串按编号形态排除）"),
                "detail": [f"{m}：DOMAINS 有引用 / 主表无收录" for m in missing],
            })
        else:
            report.ok("T-A2：DOMAINS 引用编号全部落在索引主表内（键闭合）")

        # ── T-A3 版本键完整性（图集动态豁免）───────────────────────
        pool = set(std_id_refs(dm))
        if isinstance(sn, dict):
            pool |= {norm_std_id(k) for k in sn.keys()}
        unversioned = sorted(x for x in pool
                             if x not in atlas_ids and not VERSION_KEY_RE.search(x))
        if unversioned:
            signals.append({
                "id": "T-A3", "cat": "DRIFT", "ids": unversioned,
                "msg": (f"标准类编号缺完整版本键（-YYYY）{len(unversioned)} 处，"
                        f"违索引 §1.2 第 6 条"),
                "detail": [f"{u}：SRE 侧无年份，主表收录形态见索引编号列"
                           for u in unversioned],
            })
        else:
            report.ok("T-A3：DOMAINS ∪ STANDARD_NAMES 的标准类编号均带版本键")

    # ── T-A4 索引本体自洽三查（各自独立成条，不合并计数）───────────
    enum_vals, enum_suffixes = parse_status_enum(lines)
    if not enum_vals:
        report.warn("T-A4：未从索引 §1.1 解析到状态枚举，③ 无法判据")
    # 状态取「不完整有效」的枚举值（由 §1.1 枚举派生，不手抄词表）
    partial = {v for v in enum_vals
               if not v.startswith(("现行有效", "即将实施", "过渡期"))}

    main_status: Dict[str, str] = {}
    for t in main_tables:
        id_col = find_col(t["header"], ID_COL_ALIASES)
        st_col = find_col(t["header"], STATUS_COLS, exact=True)
        if id_col is None or st_col is None:
            continue
        for _, cells in t["rows"]:
            if id_col < len(cells) and st_col < len(cells) and cells[id_col]:
                main_status[norm_std_id(cells[id_col])] = cells[st_col]

    def section_ids(heading_pat, status_aliases=STATUS_COLS):
        lo, hi = find_section(lines, heading_pat)
        if lo is None:
            return None, {}
        ids: Dict[str, str] = {}
        for t in iter_md_tables(lines, lo, hi):
            if classify_index_table(t["header"]) not in ("main", "register", "other", "verify"):
                continue
            id_col = find_col(t["header"], ID_COL_ALIASES)
            st_col = find_col(t["header"], status_aliases, exact=True)
            if id_col is None:
                continue
            for _, cells in t["rows"]:
                if id_col < len(cells) and cells[id_col]:
                    std_v = cells[st_col] if (st_col is not None and st_col < len(cells)) else ""
                    ids[norm_std_id(cells[id_col])] = std_v
        return (lo, hi), ids

    reg72_range, reg72 = section_ids(r"^7\.2")
    if reg72_range is None:
        report.warn("T-A4①：未定位到索引 §7.2，① 无法判据")
    if enum_vals and reg72:
        flagged = {i for i, s in main_status.items()
                   if any(s.startswith(norm_std_id(v)) for v in partial)}
        only_main = sorted(flagged - set(reg72))
        sub_terms = {v for v in partial if v.startswith("被部分替代")}
        main_sub = {i for i, s in main_status.items()
                    if any(s.startswith(norm_std_id(v)) for v in sub_terms)}
        reg_sub = {i for i, s in reg72.items()
                   if any(s.startswith(norm_std_id(v)) for v in sub_terms)}
        only_reg = sorted(reg_sub - main_sub)
        drift = only_main + [f"{i}（§7.2 记被部分替代，主表非该状态）" for i in only_reg]
        if drift:
            signals.append({
                "id": "T-A4①", "cat": "DRIFT", "ids": only_main + only_reg,
                "msg": (f"主表状态 ↔ §7.2 登记双向不一致 {len(drift)} 处"
                        f"（主表列 §7.2 缺 {len(only_main)}、§7.2 列主表缺 {len(only_reg)}）"),
                "detail": [f"{d}：主表状态=「{main_status.get(norm_std_id(d), '—')}」"
                           f" vs §7.2 登记集 {'含' if norm_std_id(d) in reg72 else '缺'}"
                           for d in drift],
            })
        else:
            report.ok("T-A4①：主表废止/被替代状态与 §7.2 登记双向一致")

    # ② 行结构：主表每行列数须等于该表表头列数
    if region_tables:
        malformed = []
        for t in main_tables:
            n_col = len(t["header"])
            for ln, cells in t["rows"]:
                if len(cells) != n_col:
                    malformed.append((ln, n_col, cells))
        if malformed:
            signals.append({
                "id": "T-A4②", "cat": "DRIFT", "ids": [],
                "msg": (f"主表行列数 ≠ 表头列数 {len(malformed)} 行"
                        f"（判据 len(cells)==len(header_cells)，列数由表头现算）"),
                "detail": [f"L{ln}：实测 {len(cells)} 单元 / 表头 {n_col} 列 → "
                           f"{cells}（列在此，不猜哪列错位）" for ln, n_col, cells in malformed],
            })
        else:
            report.ok("T-A4②：主表行列数与表头列数逐行一致")

    # ③ 术语一致：主表/核验记录表/§7.2/§7.3 的状态用词须落在 §1.1 枚举内
    if enum_vals:
        scope = list(main_tables) + list(verify_tables)
        for heading, kind in ((r"^7\.2", "register"), (r"^7\.3", "register")):
            lo, hi = find_section(lines, heading)
            if lo is not None:
                scope += [t for t in iter_md_tables(lines, lo, hi)
                          if classify_index_table(t["header"]) == "register"]
        offenders = []
        seen = set()
        for t in scope:
            kind = classify_index_table(t["header"])
            cols = VERIFY_STATUS_COLS if kind == "verify" else STATUS_COLS
            st_col = find_col(t["header"], cols, exact=True)
            id_col = find_col(t["header"], ID_COL_ALIASES)
            if st_col is None:
                continue
            for ln, cells in t["rows"]:
                if st_col >= len(cells):
                    continue
                term = out_of_enum_status(cells[st_col], enum_vals, enum_suffixes)
                if not term:
                    continue
                std = norm_std_id(cells[id_col]) if (id_col is not None
                                                     and id_col < len(cells)) else "?"
                if (ln, term) in seen:
                    continue
                seen.add((ln, term))
                offenders.append((ln, std, term))
        if offenders:
            signals.append({
                "id": "T-A4③", "cat": "DRIFT",
                "ids": [o[1] for o in offenders],
                "msg": (f"状态用词越出索引 §1.1 枚举（{len(enum_vals)} 值，"
                        f"枚举取自 SOT 文档）{len(offenders)} 处"),
                "detail": [f"L{ln} {std}：状态用词「{term}」不在枚举内"
                           for ln, std, term in offenders],
            })
        else:
            report.ok("T-A4③：索引内状态用词均落在 §1.1 枚举内")

    # ── T-A5 锚定集：Ⅰ 三源一致性守卫；Ⅱ 命中升档（函数体末段）─────
    anchor_srcs: Dict[str, Optional[set]] = {}
    lo, hi = find_section(lines, r"^10\.2")
    idx_anchors: set = set()
    if lo is not None:
        for t in iter_md_tables(lines, lo, hi):
            if classify_index_table(t["header"]) != "anchor":
                continue
            id_col = find_col(t["header"], ID_COL_ALIASES)
            if id_col is None:
                continue
            for _, cells in t["rows"]:
                if id_col < len(cells) and cells[id_col]:
                    idx_anchors.add(norm_std_id(cells[id_col]))
    anchor_srcs["索引 §10.2"] = idx_anchors or None

    rules_path = base_dir / "standards-reasoning-rules.md"
    rules_anchors: set = set()
    if rules_path.exists():
        rlines = rules_path.read_text(encoding="utf-8").split("\n")
        rlo, rhi = find_section(rlines, r"^2\.3")
        if rlo is not None:
            for t in iter_md_tables(rlines, rlo, rhi):
                if classify_index_table(t["header"]) != "anchor":
                    continue
                id_col = find_col(t["header"], ID_COL_ALIASES)
                if id_col is None:
                    continue
                for _, cells in t["rows"]:
                    if id_col < len(cells) and cells[id_col]:
                        rules_anchors.add(norm_std_id(cells[id_col]))
    else:
        report.warn(f"T-A5Ⅰ：standards-reasoning-rules.md 不可达（{rules_path}）")
    anchor_srcs["推理规则 §2.3"] = rules_anchors or None

    code_anchors = ({norm_std_id(a) for a in lits["ANCHORS"]}
                    if isinstance(lits.get("ANCHORS"), (set, list, tuple)) else None)
    anchor_srcs["sre_reasoner.ANCHORS"] = code_anchors

    known = {k: v for k, v in anchor_srcs.items() if v}
    if len(known) == 3:
        base_set = known["索引 §10.2"]
        drifts = [(k, v) for k, v in known.items() if v != base_set]
        if drifts:
            detail = [f"{k} 成员数 {len(v)}；与索引 §10.2 差集 "
                      f"缺 {sorted(base_set - v) or '无'} / 多 {sorted(v - base_set) or '无'}"
                      for k, v in anchor_srcs.items()]
            signals.append({
                "id": "T-A5Ⅰ", "cat": "DRIFT", "ids": [],
                "msg": (f"锚定集三源成员不一致：{[k for k, _ in drifts]}"),
                "detail": detail,
            })
        else:
            report.ok(f"T-A5Ⅰ：锚定集三源一致 "
                      f"{len(known['索引 §10.2'])} = "
                      f"{len(known['推理规则 §2.3'])} = "
                      f"{len(known['sre_reasoner.ANCHORS'])}，0 漂移（守卫上线即绿，非缺陷）")
    else:
        report.warn("T-A5Ⅰ：锚定三源中有源不可达 "
                    f"{[k for k, v in anchor_srcs.items() if not v]} → 本轮不判漂移")

    anchor_set = known.get("索引 §10.2")
    anchor_unknown = not anchor_set

    # 末段：A5-A 聚合——对本组已产出的每条信号叠加 anchor，再统一落报告
    anchored: List[str] = []
    for sig in signals:
        hits = sorted(set(sig["ids"]) & anchor_set) if anchor_set else []
        if anchor_unknown:
            tag = "｜anchor=unknown（锚定集不可达，不得静默填 false）"
        elif hits:
            tag = (f"｜anchor=true（命中 {'、'.join(hits)}，"
                   f"按 §4.5 升 S 级处置）")
            sig["hits"] = hits
            anchored.append(sig["id"])
        else:
            tag = "｜anchor=false"
        report.warn(f"{sig['id']} [{sig['cat']}] {sig['msg']}{tag}")
        for i, d in enumerate(sig["detail"], 1):
            report.info(f"{sig['id']}·{i}/{len(sig['detail'])} {d}")

    if anchor_set:
        if anchored:
            hit_ids = sorted({h for sig in signals for h in sig.get("hits", [])})
            signals_clean = anchor_set - set(hit_ids)
            report.warn(f"T-A5Ⅱ [DEGRADE] 锚定集 {len(anchor_set)} 条中 "
                        f"{len(hit_ids)} 条被静态组信号命中（命中信号 {len(anchored)} 条："
                        f"{'、'.join(anchored)}；本项只聚合已实装的静态组 T-A1—T-A4，"
                        f"行为组 T-B1—T-B7 未实装，故计数低于设计 §3.1 的全组实测值，"
                        f"不得据此判漏报）（升档标注器，不新增缺陷事实）"
                        f"｜anchor=true（定义使然）")
            report.info(f"T-A5Ⅱ·命中编号 {hit_ids}")
            report.info(f"T-A5Ⅱ·本组未触及的锚定条目 {sorted(signals_clean)}")
        else:
            report.ok("T-A5Ⅱ：静态组信号未命中任何锚定标准（修复后可转正向断言）")
    else:
        report.warn("T-A5Ⅱ：锚定集不可达 → 本组信号 anchor 全部标 unknown，"
                    "升档依据缺失，须按 §4.3 降级态处理")


# ── 主流程 ────────────────────────────────────────────────
def main():
    # Windows 终端 UTF-8 兼容
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    import argparse
    parser = argparse.ArgumentParser(
        description="装配式装修技能合集 — 治理文件契约校验"
    )
    parser.add_argument(
        "--dir", type=str, default=str(DEFAULT_BASE),
        help="治理文件所在目录（默认：_专题_技能合集策划/）"
    )
    parser.add_argument(
        "--runtime-dir", type=str, default=str(SRE_DIR),
        help="运行时技能目录（默认：~/.qoder/skills/prefab-standards-reviewer/，"
             "检查 5 的数据源；不可达时降级为 WARN）"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="显示详细信息"
    )
    args = parser.parse_args()

    base_dir = Path(args.dir)
    if not base_dir.exists():
        print(f"[ERROR] 目录不存在: {base_dir}")
        sys.exit(1)
    runtime_dir = Path(args.runtime_dir)

    report = Report()

    # 检查 1：红线注册表
    rl_path = base_dir / "redlines-registry.md"
    rl_text = read_file(rl_path, "红线注册表")
    if rl_text:
        check_redlines(rl_text, report)
    else:
        report.section("红线注册表 — 计数一致性")
        report.fail("文件不存在，跳过")

    # 检查 2：接口契约
    ic_path = base_dir / "interface-contracts.md"
    ic_text = read_file(ic_path, "接口契约")
    if ic_text:
        check_interfaces(ic_text, report)
    else:
        report.section("接口契约 — IC-02/IC-03/IC-05/IC-06/IC-07/IC-08/IC-09/IC-10/IC-11/IC-12/IC-13/IC-14 Schema 必填字段")
        report.fail("文件不存在，跳过")

    # 检查 3：标准索引
    si_path = base_dir / "standards-index.md"
    si_text = read_file(si_path, "标准索引")
    std_actual = None
    std_rows: List[Tuple[str, int]] = []
    std_names: Dict[str, str] = {}
    if si_text:
        std_actual, std_rows, std_names = check_standards(si_text, report)
    else:
        report.section("标准索引 — 状态合法性与核验时效")
        report.fail("文件不存在，跳过")

    # 检查 4：跨文件计数漂移反查
    check_cross_file_drift(base_dir, report, si_text, rl_text, ic_text, std_actual)

    # 检查 5：SRE 静态体检 T-A1—T-A5（首轮一律 WARN，不计 fail_count）
    check_sre_static(base_dir, runtime_dir, report, si_text, std_rows, std_names)

    # 输出报告
    fail_count = report.print_report()
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
