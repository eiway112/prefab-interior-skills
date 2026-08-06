#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装配式装修技能合集 — 治理文件契约校验脚本
validate_governance.py v1.1

校验四类治理文件的一致性和完整性：
  1. redlines-registry.md  — 红线计数一致性（声明 vs 实际 vs 统计表，统计表按表头动态解析）
  2. interface-contracts.md — IC-08/IC-10 JSON Schema 必填字段完整性
  3. standards-index.md     — 标准状态枚举合法性（实际落检）+ 时间状态双向检查
                              （实施日期已过仍标"即将实施"→FAIL）+ 核验过期预警
  4. 跨文件漂移反查          — 项目索引/SRE/standards-index §10.1 中的手写计数
                              与注册表本体动态统计值比对，不一致即 FAIL

v1.1 变更（2026-08-06，CG-20260806-008）：
  - 修复 §十一/十二 统计表硬编码 6 技能导致 WS 加入后误判合计（改为按表头动态解析）
  - 修复标准编号解析器遗漏 T/团标、JG/T、HG/T、SJG、RISN-TG、DBJ、图集编号（46→全量识别）
  - 修复非法状态检查空实现（现按行实际抽取状态单元格并比对枚举）
  - 新增时间状态反向检查：实施日期 ≤ 今天但状态仍为"即将实施" → FAIL
  - 新增检查 4：跨文件计数漂移反查（计数以脚本统计本体为准）

用法：
  python validate_governance.py
  python validate_governance.py --dir <项目根目录>
  python validate_governance.py --verbose

依赖：Python 3.8+（仅标准库）
"""

import re
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ── 默认路径 ──────────────────────────────────────────────
# 脚本位于 _src/，治理文件位于 _专题_技能合集策划/
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE = SCRIPT_DIR.parent / "_专题_技能合集策划"

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
        r"^##\s+[三四五六七八九十]+、已注册红线：(.+?)（(\w+)）",
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
    report.section("接口契约 — IC-08/IC-10 Schema 必填字段")

    for ic_id in ["IC-08", "IC-10"]:
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
            if any(k in header_joined for k in ("核验日期", "核验状态", "核验结论")):
                in_main_table = False      # 核验记录表：不计入标准总数
            elif "状态" in header_joined:
                in_main_table = True       # 主表：计入标准总数
            else:
                in_main_table = False
            continue

        if not in_main_table or not cells[0].isdigit():
            continue

        std_id = cells[1].replace("**", "") if len(cells) > 1 else "?"
        line_no = idx + 1
        std_rows.append((std_id, line_no))

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

    return actual_count


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
        "--verbose", action="store_true",
        help="显示详细信息"
    )
    args = parser.parse_args()

    base_dir = Path(args.dir)
    if not base_dir.exists():
        print(f"[ERROR] 目录不存在: {base_dir}")
        sys.exit(1)

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
        report.section("接口契约 — IC-08/IC-10 Schema 必填字段")
        report.fail("文件不存在，跳过")

    # 检查 3：标准索引
    si_path = base_dir / "standards-index.md"
    si_text = read_file(si_path, "标准索引")
    std_actual = None
    if si_text:
        std_actual = check_standards(si_text, report)
    else:
        report.section("标准索引 — 状态合法性与核验时效")
        report.fail("文件不存在，跳过")

    # 检查 4：跨文件计数漂移反查
    check_cross_file_drift(base_dir, report, si_text, rl_text, ic_text, std_actual)

    # 输出报告
    fail_count = report.print_report()
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
