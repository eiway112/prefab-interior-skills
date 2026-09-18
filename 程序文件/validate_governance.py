#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装配式装修技能合集 — 治理文件契约校验脚本
validate_governance.py v1.9.0

校验七项一致性与完整性：
  1. redlines-registry.md  — 红线计数一致性（声明 vs 实际 vs 统计表，统计表按表头动态解析）
  2. interface-contracts.md — IC-02/IC-03/IC-05/IC-06/IC-07/IC-08/IC-09/IC-10/IC-11/IC-12/IC-13/IC-14 JSON Schema 必填字段完整性
  3. standards-index.md     — 标准状态枚举合法性（实际落检）+ 时间状态双向检查
                              （实施日期已过仍标"即将实施"→FAIL）+ 复查维护提醒及依据记录预警
  4. 跨文件漂移反查          — 项目索引/SRE/standards-index §10.1 中的手写计数
                              与注册表本体动态统计值比对，不一致即 FAIL
  5. SRE 静态体检 T-A1—T-A5  — 运行时 sre_reasoner.py 硬编码字面量（AST 提取，不 import）
                              与 standards-index.md 双源一致性 + 索引本体自洽 + 锚定集守卫
                              首轮一律 WARN（不计 fail_count），不打破 exit code 基线；
                              T-A1 自 v1.8.0 起升 FAIL 档（计 fail_count）——§6.3.3 ③(b)
                              前置（①②③ 全落地归零，CG-20260918-001）已满足，见 CG-20260918-002
                              判据见《文档/SRE确定性体检设计方案_v1.0.md》§3.1
  6. 跨层一致性比对          — 三层模型（L1 开发源 / 运行时根 SOT / shared 镜像 / 技能仓备份）
                              两条独立断言：(A) L1 → 该件声明的全部下游副本字节全等
                              （抓跨批落后），(B) 运行时层 ↔ 技能仓备份同层全等
                              （抓 sync_skill_backup.py 漏跑或半跑）
                              比对集按文件逐个声明分层归属，不用目录 glob，故 *_pre* 回退件
                              天然不入比对；基准取本次实读字节，不读 同步说明.md 的哈希清单
                              （那是被测同步工具自身的产物，作基准属自指）
                              运行时目录不可达 → 涉及该层的项降级 WARN 不 FAIL（同检查 5 口径），
                              且被跳过的 (文件@层) 组合逐条列出，不只报总数
                              比对集成员另与 sync_skill_backup.py 的 ROOT_FILES ∪ SHARED_FILES
                              做双源交叉校验（AST 提取，不 import），漏配即 FAIL
  7. 遗留存活性台账（PENDING-TTL 本仓化，CG-20260918-005）
                              — 读 change-governance.md §十一 台账表，把「登记即永久免检」
                              改为到期由治具求值（与检查 3 的核验时效同构）
                              FAIL 档（同机字面、无外部真值依赖，故首轮即 FAIL）：台账表/必需列
                              缺失、编号非法或重复、状态出三值枚举、日期不可解析、待处置行缺到期日、
                              登记日期晚于到期日、已闭合/已裁定不做行缺处置依据、来源与处置列引用的
                              CG 编号不在 §九 变更日志内（键闭合）
                              WARN/INFO 档：到期日早于今天 → 聚合一条 WARN＋逐条 INFO 披露
                              （到期不等于失效、不等于必须关闭，只触发「须重新裁定：处置/续期/改判不做」，
                              沿 CG-20260917-009「不因单纯到期增加失败」口径）；30 天内到期 → INFO 预警；
                              待处置行 TTL 超 §11.1 上限 180 天 → WARN（续期须写明理由）
                              覆盖面限制：只做「台账 → §九」方向键闭合，不反查 CG 行散文里声明的遗留
                              （散文字面无稳定形态，正则会产假信号），故「新遗留漏登记」仍靠人工，
                              与 §11.3 第 3 条同口径显式披露

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

v1.6.0 变更（2026-09-16，CG-20260916-010）：
  - 新增检查 6：治理文件跨层一致性比对（承接 CG-20260916-006 ⑧(a) 与 -009 遗留 (c)——
    `standards-index.md` 那次 6,689 B 跨批漂移此前只能靠人工发现，因校验面无任何跨层比对）
  - 新增 CROSS_LAYER_SET（逐文件声明归属层）与 check_cross_layer()；派生层路径常量
    REPO_BACKUP_DIR / REPO_BACKUP_SHARED_DIR
  - RUNTIME_SHARED_DIR 自 v1.5 起声明后零引用（死常量），本批由检查 6 消费，
    即"校验面不含跨层一致性比对"这一登记缺口闭合
  - 检查 6 的层路径取模块常量（三层模型为固定结构），不受 --runtime-dir 影响；
    该选项只重定位检查 5 的 sre_reasoner.py 数据源
  - 档位：同机字面哈希比对、无外部真值依赖，故落地即 FAIL 档（不计入首轮 WARN 组）

v1.8.0 变更（2026-09-18，CG-20260918-002）：
  - T-A1 名称双源差分由 WARN 升 FAIL 档（计 fail_count）：设计方案 §6.3.3 ③(b) 的
    升档前置「①②全落地归零」已随 CG-20260918-001 的 13 处名称差分清零满足（门禁实测
    转「零冲突」OK），本批另线完成代码级半步；clean 态读数不变（该路径本即 report.ok），
    仅差分非空时阻断 exit code
  - 反向注入自证：--runtime-dir 临时副本注入 1 处名称值 → T-A1 FAIL＋exit 1；检查 6 的
    层路径取模块常量、不受 --runtime-dir 影响，注入态保持绿（两案互不掩盖）
  - 其余信号（T-A2—T-A5）维持首轮 WARN，升档时点各自依 §6.3.3 前置，不随本批扩面

v1.9.0 变更（2026-09-18，CG-20260918-005）：
  - 新增检查 7「遗留存活性台账」：读 change-governance.md §十一 的 PL-nnn 台账表，
    使遗留事项具备到期日与机算求值（动因＝梳理报告 §四.1／裁定 3：此前遗留由散文承担、
    无到期日无机算，属「登记即永久免检」；CG-20260917-009 已在核验日期面确立
    「到期由治具求值，不由散文自报」，本批把同一原则落到遗留面）
  - 分档：结构性违法（表/列缺失、编号非法或重复、状态出枚举、日期不可解析、待处置缺到期日、
    登记晚于到期、闭合无依据、CG 键不闭合）首轮即 FAIL 档并计 fail_count——同机字面比对、
    无外部真值依赖，与检查 6 同理；单纯到期只 WARN＋INFO 披露，不计 fail_count
  - 状态枚举取三值闭集（待处置/已闭合/已裁定不做），TTL 口径取 §11.1（常规 90 天／
    事件驱动 180 天／限期明写），常量 LEDGER_TTL_DEFAULT／LEDGER_TTL_EVENT 与散文同源同值
  - 专项测试 程序文件/pending_ledger_test.py（第六门禁）：clean 态零 FAIL＋到期 WARN 不计失败、
    八类结构违法逐类注入自证、TTL 边界（到期日＝今天不超期、次日超期）、键闭合双向、
    续期超上限 WARN；负向注入用合成文本直调 check_pending_ledger，不落盘、不改治理件

用法：
  python validate_governance.py
  python validate_governance.py --dir <项目根目录>
  python validate_governance.py --runtime-dir <运行时技能目录>
  python validate_governance.py --verbose

依赖：Python 3.8+（仅标准库）
"""

import ast
import hashlib
import re
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# ── 默认路径 ──────────────────────────────────────────────
# 脚本位于 _src/，治理文件位于 _专题_技能合集策划/
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE = SCRIPT_DIR.parent / "_专题_技能合集策划"

# ── 运行时技能目录（L2 SOT / L3 镜像，检查 5 与检查 6 的数据源）──
RUNTIME_SKILLS = Path.home() / ".qoder" / "skills"
SRE_DIR = RUNTIME_SKILLS / "prefab-standards-reviewer"
RUNTIME_SHARED_DIR = RUNTIME_SKILLS / "shared"

# ── 仓内镜像（运行时技能的 git 侧副本，检查 6 的数据源）────
REPO_BACKUP_DIR = SCRIPT_DIR.parent / "技能仓备份"
REPO_BACKUP_SHARED_DIR = REPO_BACKUP_DIR / "shared"

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
        print("  层别：本报告全部为【机检层】＝存在性/一致性（字段有无·枚举合法·哈希相等·日期到期）")
        print("        【判断层】＝真伪抽样（场景级期望值断言·红线行为守恒）见 sre_regression_test.py")
        print("  判读：机检零 ERROR ≠ 内容正确（整改方案 §6.3 门禁分层，CG-20260917-004）")
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
# §1.1A 的维护周期派生天数，只用于复查提醒，不裁定标准效力。
REVIEW_DAYS_MANDATORY = 92
REVIEW_DAYS_OTHER = 183
# 强制性国标档的归属判据：索引 §二 小节标题「第一层级：强制性国标（红线标准）」。
MANDATORY_HEADING_MARK = "第一层级"


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
    ledger_rows = []             # (std_id, line_no, 是否强制性国标档) — 核验时效台账
    upcoming_impl = []           # 正常：未来实施
    overdue_status = []          # 异常：实施日期已过仍标"即将实施"
    premature_effective = []     # 异常：实施日期未到却标"现行有效"
    std_rows = []                # (std_id, line_no)
    today = datetime.now()

    sep_line = re.compile(r"^\|[\s:\-|]+\|$")
    status_bases = ("现行有效", "即将实施", "过渡期", "已废止", "被替代",
                    "被部分替代", "被部分废止")
    in_main_table = False     # 当前是否处于主表（含"状态"列）数据区
    in_l1_section = False     # 当前是否处于 §二「第一层级：强制性国标」小节（92 天档）
    std_names: Dict[str, str] = {}   # 编号 → 名称（主表名称列，供检查 5 复用）
    name_col: Optional[int] = None   # 当前主表的名称列号（按表头取值，非固定列）
    for idx in range(body_start, body_end):
        line = lines[idx].strip()
        if line.startswith("## "):
            in_l1_section = MANDATORY_HEADING_MARK in line
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
        ledger_rows.append((std_id, line_no, in_l1_section))
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

    # 核验日期现读（整改方案 P1 item 9）：遍历全文凡表头判为 verify 的表，按**列名**取
    # 「核验日期」。旧实现以 `#` 标题定位"官方核验记录"区域，而索引里该标题是粗体行
    # （`**官方核验记录**（已核验标准）：`），锚点命中 0 处 → expired_review 恒为空 →
    # 无条件打印"无超期未核验标准"，属恒真空跑守卫（到期实际由索引散文承载）。
    verify_dates: Dict[str, str] = {}
    verify_states: Dict[str, str] = {}
    for tbl in iter_md_tables(lines, 0, len(lines)):
        if classify_index_table(tbl["header"]) != "verify":
            continue
        i_vid = find_col(tbl["header"], ID_COL_ALIASES, exact=True)
        i_vdate = find_col(tbl["header"], ("核验日期",), exact=True)
        i_vstate = find_col(tbl["header"], ("核验状态",), exact=True)
        if i_vid is None:
            continue
        for _, cells in tbl["rows"]:
            if i_vid >= len(cells):
                continue
            m_date = (re.search(r"\d{4}-\d{2}-\d{2}", cells[i_vdate])
                      if i_vdate is not None and i_vdate < len(cells) else None)
            for one in cells[i_vid].split("／"):
                sid = norm_std_id(one)
                if not STD_ID_SHAPE.match(sid):
                    continue
                if i_vstate is not None and i_vstate < len(cells):
                    verify_states[sid] = cells[i_vstate].replace("**", "").strip()
                if m_date and (sid not in verify_dates or m_date.group(0) > verify_dates[sid]):
                    verify_dates[sid] = m_date.group(0)

    ledger: Dict[bool, Dict[str, list]] = {
        True: {"在期": [], "超期": [], "无日期": []},
        False: {"在期": [], "超期": [], "无日期": []},
    }
    ledger_no_id: List[Tuple[str, int]] = []
    invalid_verify_dates: List[Tuple[str, str]] = []
    for raw_id, line_no, mandatory in ledger_rows:
        sid = norm_std_id(raw_id)
        if not STD_ID_SHAPE.match(sid):
            ledger_no_id.append((raw_id, line_no))
            continue
        date_str = verify_dates.get(sid)
        tier = REVIEW_DAYS_MANDATORY if mandatory else REVIEW_DAYS_OTHER
        if date_str is None:
            ledger[mandatory]["无日期"].append(sid)
            continue
        try:
            age = (today - datetime.strptime(date_str, "%Y-%m-%d")).days
        except ValueError:
            invalid_verify_dates.append((sid, date_str))
            ledger[mandatory]["无日期"].append(sid)
            continue
        if age < 0:
            invalid_verify_dates.append((sid, date_str))
            ledger[mandatory]["无日期"].append(sid)
            continue
        if age > tier:
            ledger[mandatory]["超期"].append((sid, date_str, age, tier))
        else:
            ledger[mandatory]["在期"].append((sid, date_str, age, tier))

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

    tier_label = {True: "强制性国标", False: "其余标准"}
    for mandatory in (True, False):
        bucket = ledger[mandatory]
        tier = REVIEW_DAYS_MANDATORY if mandatory else REVIEW_DAYS_OTHER
        total = sum(len(v) for v in bucket.values())
        report.info(
            f"核验时效台账·{tier_label[mandatory]}（{tier} 天档）：共 {total} 条 → "
            f"在期 {len(bucket['在期'])}／已核验但超期 {len(bucket['超期'])}"
            f"／无「核验日期」记录 {len(bucket['无日期'])}")
        if bucket["无日期"]:
            report.info(f"  无「核验日期」清单：{'、'.join(sorted(bucket['无日期']))}")
        boundary = [sid for sid, _, age, t in bucket["在期"] if age == t]
        if boundary:
            report.info(
                f"  档位边界（今日恰第 {tier} 天仍在期、次日转超期）：{'、'.join(sorted(boundary))}")
    for mandatory in (True, False):
        for sid, date_str, age, tier in ledger[mandatory]["超期"]:
            report.info(
                f"{sid}：复查提醒，核验日期 {date_str} 距今 {age} 天，超{tier_label[mandatory]}"
                f"维护周期（{tier} 天）；不据此判标准失效或降低既有依据确定性，"
                f"须安排复查；不代表本次已核实最新状态")
    scheduled_reviews = {sid for sid, state in verify_states.items() if state == "到期需复核"}
    overdue_reviews = {sid for m in (True, False) for sid, _, _, _ in ledger[m]["超期"]}
    for sid in sorted(scheduled_reviews - overdue_reviews):
        report.info(f"{sid}：复查提醒，核验状态=到期需复核，已有显式复查任务；"
                    "是否具备可复用依据仍按有效日期及核验记录判定，不以任务登记替代核验")
    for sid, date_str in invalid_verify_dates:
        report.warn(f"{sid}：核验日期 {date_str} 不可解析或晚于当前日期，记录须核实")
    no_date_total = sum(len(ledger[m]["无日期"]) for m in (True, False))
    if no_date_total:
        report.warn(
            f"无有效「核验日期」记录 {no_date_total} 条（强制性国标 "
            f"{len(ledger[True]['无日期'])}／其余 {len(ledger[False]['无日期'])}）："
            f"依据链未确认，不等于标准已失效或已超期；出口二选一——补足真实核验记录，"
            f"或接受 SRE 降低确定性输出（standards-index.md §1.1A，"
            f"运行时侧降级见 sre_reasoner._verification_confirmed）")
    if not overdue_reviews and not scheduled_reviews:
        report.info(
            f"无到期复查任务（{tier_label[True]} {REVIEW_DAYS_MANDATORY} 天／"
            f"{tier_label[False]} {REVIEW_DAYS_OTHER} 天，从日期现算且核对显式任务；不代表状态重新核验）")
    if ledger_no_id:
        report.info(
            f"无编号条目 {len(ledger_no_id)} 处（指南类，官方无编号）不入编号台账："
            f"行号 {[ln for _, ln in ledger_no_id]}")

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
    """T-A1—T-A5 静态体检。T-A1 自 v1.8.0 起 FAIL 档（CG-20260918-002）；其余首轮一律 WARN（不计 fail_count），修复不等观察期。"""
    report.section("SRE 静态体检 — T-A1—T-A5（T-A1 自 v1.8.0 起 FAIL 档；其余首轮 WARN）")

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
            # 机检层只裁「关键词存在性差分」（测量/评价 在两源名称中出现与否不同），不裁其是否改角色。
            # 名称仅在 sre_reasoner.py:697（非 L1 且非 L2/L3-binding_support 支）参与 verification_reference 判定；
            # 当前 flagged 的 DB/DBJ 属 L2/binding_support，角色在 :695-696 即定为 design_basis、永不到达 :697，
            # 反事实实测去掉名称「测量/评价」角色不变（断点8，CG-20260917-004）。真伪归判断层，机检层不作因果声称。
            kw_div = (("测量" in sre_name, "评价" in sre_name)
                      != ("测量" in idx_name, "评价" in idx_name))
            conflicts.append((nk, sre_name, idx_name, kw_div))
        if conflicts:
            n_kw = sum(1 for c in conflicts if c[3])
            signals.append({
                "id": "T-A1", "cat": "DRIFT",
                "ids": [c[0] for c in conflicts],
                "msg": (f"SRE STANDARD_NAMES 与索引主表名称差分 {len(conflicts)} 处"
                        f"（判据=差分非空即报，计数随键匹配情况变动，非断言常量；"
                        f"其中『测量/评价』关键词差分 {n_kw} 处——机检层只报关键词存在性、不裁是否改角色："
                        f"名称仅在 sre_reasoner.py:697 非 L1 且非 L2/L3-binding_support 支参与 verification_reference 判定，"
                        f"当前 flagged 属 L2/binding_support→角色恒 design_basis，反事实实测名称差分不改角色"
                        f"〔断点8 订正，CG-20260917-004〕）"),
                "detail": [f"{c[0]}：SRE=「{c[1]}」/ 索引=「{c[2]}」"
                           + ("［关键词差分·实测不改角色］" if c[3] else "")
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
        # v1.8.0（CG-20260918-002）：T-A1 升档——§6.3.3 ③(b) 前置已满足（CG-20260918-001 归零），
        # 名称差分非空即 FAIL 并计 fail_count；其余信号仍首轮 WARN，升档时点各自依其前置。
        if sig["id"] == "T-A1":
            report.fail(f"{sig['id']} [{sig['cat']}] {sig['msg']}{tag}")
        else:
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


# ── 检查 6：治理文件跨层一致性比对 ────────────────────────
# 归属层逐文件声明（不用目录 glob）。某层无此件属声明事实而非缺失，出处写在各行备注里。
CROSS_LAYER_SET = [
    ("standards-index.md",
     ("L1", "RT_ROOT", "RT_SHARED", "REPO_ROOT", "REPO_SHARED"),
     "五层字节全等＝本表通过态。注意 prefab-governance-sync:40 约定「根含 SOT 声明＋镜像说明、"
     "镜像为 shared 措辞，只同步正文」，而该头部差异未被维持（CG-20260916-006 ⑧(b) 既存偏差）；"
     "若日后恢复头部约定，本件须同批改为本体比对＋头部豁免，否则假红"),
    ("change-governance.md",
     ("L1", "RT_SHARED", "REPO_SHARED"),
     ""),
    ("glossary.md",
     ("L1", "RT_SHARED", "REPO_SHARED"),
     ""),
    ("interface-contracts.md",
     ("L1", "RT_SHARED", "REPO_SHARED"),
     ""),
    ("redlines-registry.md",
     ("L1", "RT_SHARED", "REPO_SHARED"),
     "运行时只有 shared/ 镜像一处（prefab-governance-sync 三层映射表特例行）"),
    ("standards-reasoning-rules.md",
     ("L1", "RT_SHARED", "REPO_SHARED"),
     ""),
    ("platform-adapter-reference.md",
     ("RT_ROOT", "RT_SHARED", "REPO_ROOT", "REPO_SHARED"),
     "SOT 直接建于运行时根、项目仓无开发副本（技能合集总入口策划方案 文件清单）；"
     "根↔镜像的头部差异系技能约定，故只比同层（RT_ROOT↔REPO_ROOT、RT_SHARED↔REPO_SHARED）"),
]
RUNTIME_LAYERS = ("RT_ROOT", "RT_SHARED")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_cross_layer(base_dir: Path, report: Report):
    """三层模型的字节一致性。两条断言各自独立，故一条红不掩盖另一条。

    (A) L1 → 该件声明的全部下游副本：抓 CG-20260916-006 那类跨批落后。
    (B) 运行时层 ↔ 技能仓备份同层：抓 sync_skill_backup.py 漏跑或半跑。
    """
    report.section("治理文件跨层一致性 — (A) L1→下游副本 ／ (B) 运行时↔技能仓备份")

    layer_dir = {"L1": base_dir, "RT_ROOT": RUNTIME_SKILLS, "RT_SHARED": RUNTIME_SHARED_DIR,
                 "REPO_ROOT": REPO_BACKUP_DIR, "REPO_SHARED": REPO_BACKUP_SHARED_DIR}

    # 双源交叉校验：本表成员须等于被测同步脚本的管辖范围，否则「脚本管、本表漏」会静默放过
    sync_path = SCRIPT_DIR / "sync_skill_backup.py"
    declared = {name for name, _, _ in CROSS_LAYER_SET}
    if sync_path.is_file():
        lits = extract_py_literals(
            sync_path.read_text(encoding="utf-8"), ["ROOT_FILES", "SHARED_FILES"])
        scope = set(lits.get("ROOT_FILES") or []) | set(lits.get("SHARED_FILES") or [])
        if scope:
            for miss in sorted(scope - declared):
                report.fail(f"{miss}：在 sync_skill_backup.py 管辖范围内而 CROSS_LAYER_SET 未声明"
                            f" → 该件的跨层漂移不经门禁（漏配）")
            for extra in sorted(declared - scope):
                report.fail(f"{extra}：在 CROSS_LAYER_SET 内而不属 sync_skill_backup.py 范围"
                            f" → 声明表越界，须核归属或让该脚本纳管")
            if scope == declared:
                report.ok(f"比对集与 sync_skill_backup.py 管辖范围成员一致（{len(scope)} 件）")
        else:
            report.warn(f"未能从 {sync_path.name} 提取 ROOT_FILES/SHARED_FILES → 本项不判")
    else:
        report.warn(f"sync_skill_backup.py 不可达：{sync_path} → 范围交叉校验本项不判")

    unreachable = {k for k in RUNTIME_LAYERS if not layer_dir[k].is_dir()}
    if unreachable:
        report.warn(f"运行时目录不可达：{'、'.join(sorted(unreachable))} → 涉该层各项本轮不判，"
                    f"只降级不判红（检查 5 同口径）；L1 与 `技能仓备份/` 属本仓固定面，缺失仍判 FAIL")
    skipped: List[str] = []

    digest: Dict[Tuple[str, str], Optional[str]] = {}
    for name, layers, _note in CROSS_LAYER_SET:
        for layer in layers:
            if layer in unreachable:
                digest[(name, layer)] = None
                skipped.append(f"{name}@{layer}")
                continue
            path = layer_dir[layer] / name
            if path.is_file():
                digest[(name, layer)] = sha256_file(path)
            elif not layer_dir[layer].is_dir():
                digest[(name, layer)] = None
                report.fail(f"{name}：声明归属 {layer} 层，该层目录不存在（{layer_dir[layer]}）")
            else:
                digest[(name, layer)] = None
                report.fail(f"{name}：声明归属 {layer} 层，实际无此件（{path}）")

    for name, _layers, note in CROSS_LAYER_SET:
        if note:
            report.info(f"{name}：{note}")

    a_checked = b_checked = 0

    for name, layers, note in CROSS_LAYER_SET:
        if "L1" not in layers:
            report.info(f"{name}：无 L1 归属 → 不入 (A) 链")
            continue
        l1 = digest[(name, "L1")]
        if l1 is None:
            continue          # 不可读已在上一步 FAIL
        for layer in layers:
            if layer == "L1":
                continue
            other = digest[(name, layer)]
            if other is None:
                continue      # 降级或已 FAIL，不重复计项
            a_checked += 1
            if other == l1:
                report.ok(f"(A) {name}：{layer} = L1（{l1[:16]}）")
            else:
                report.fail(f"(A) {name}：{layer} {other[:16]} ≠ L1 {l1[:16]}"
                            f" → 跨层落后，须由 prefab-governance-sync 按 L1→下游带平")

    for name, layers, _note in CROSS_LAYER_SET:
        for rt, repo in (("RT_ROOT", "REPO_ROOT"), ("RT_SHARED", "REPO_SHARED")):
            if rt not in layers or repo not in layers:
                continue
            h_rt, h_repo = digest[(name, rt)], digest[(name, repo)]
            if h_rt is None or h_repo is None:
                continue
            b_checked += 1
            if h_rt == h_repo:
                report.ok(f"(B) {name}：{rt} = {repo}（{h_rt[:16]}）")
            else:
                report.fail(f"(B) {name}：{rt} {h_rt[:16]} ≠ {repo} {h_repo[:16]}"
                            f" → sync_skill_backup.py 漏跑或半跑")

    if skipped:
        report.warn(f"降级不判项 {len(skipped)} 处：{'、'.join(skipped)}"
                    f"（运行时不可达所致，非该层与 L1 一致）")
    report.info(f"(A) 比对 {a_checked} 项 ／ (B) 比对 {b_checked} 项；"
                f"比对集逐文件声明（{len(CROSS_LAYER_SET)} 件），不 glob 故回退件不入")
    report.info("覆盖面边界：本检查只覆盖上表声明的治理件；技能目录内各件"
                "（SKILL.md／reference.md／examples.md 等）与机器本地产物"
                "（如 sre_regression_report.json）不经本检查")
    report.info("哈希口径：sha256 取原始字节、不做 eol／编码归一。跨机若 core.autocrlf=true "
                "会使 `技能仓备份/` 层转 CRLF 而产假红（本机复算：git config core.autocrlf=false，"
                "治理件 CR 字节 0，唯 platform-adapter-reference.md 四层同为 CRLF=26 且同层互等）")
    report.info(f"层路径：L1={base_dir} ／ 运行时={RUNTIME_SKILLS} ／ 仓内镜像={REPO_BACKUP_DIR}"
                f"（本检查取模块常量，不受 --runtime-dir 影响）")
    if not unreachable and a_checked + b_checked == 0:
        report.fail("(A)(B) 零比对项且非降级态 —— 声明表或层路径已失效，本检查不得判绿")


# ── 检查 7：遗留存活性台账（PENDING-TTL 本仓化，CG-20260918-005）──
LEDGER_TTL_DEFAULT = 90        # §11.1 常规：登记日期 + 90 天
LEDGER_TTL_EVENT = 180         # §11.1 事件驱动：登记日期 + 180 天（口径上限）
LEDGER_SOON_DAYS = 30          # 到期预警窗口
LEDGER_ID_SHAPE = re.compile(r"^PL-\d{3}$")
LEDGER_STATUS_ENUM = ("待处置", "已闭合", "已裁定不做")
LEDGER_CLOSED_STATES = ("已闭合", "已裁定不做")
LEDGER_BLANK = {"", "—", "–", "-", "－", "无", "N/A", "n/a"}
LEDGER_DATE_SHAPE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEDGER_COLS = (
    ("编号", ("编号",)),
    ("事项", ("事项",)),
    ("来源登记", ("来源",)),
    ("登记日期", ("登记日期",)),
    ("到期日", ("到期日", "到期")),
    ("状态", ("状态",)),
    ("处置批次／依据", ("处置", "依据")),
)
CG_ID_SHAPE = re.compile(r"CG-\d{8}-\d{3}")


def ledger_blank(raw: str) -> bool:
    return (raw or "").strip() in LEDGER_BLANK


def ledger_date(raw: str):
    """可解析则返回 datetime，空值与非法格式一律返回 None（调用方按是否 blank 区分两种）。"""
    s = (raw or "").strip()
    if not LEDGER_DATE_SHAPE.match(s):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None


def collect_cg_log_ids(lines: List[str]) -> set:
    """§九 变更日志出现过的全部 CG 编号 —— 检查 7 键闭合的真值源（不取手抄集合）。

    不用 iter_md_tables：§九 存在跨物理行断行的历史行（实测 :317—:318），表头感知解析
    在断点处把其后各行判为「无表头块」而整块不产表，断点之后的 CG 编号全部不可见
    （实测只读到 72 个、止于 CG-20260916-008）。此处按「行首第一列含 CG 编号」逐行取，
    对断行免疫；断行本身作为缺陷登记于台账 PL-016，不在本检查内静默修复。
    """
    lo, hi = find_section(lines, r"^九、变更日志")
    ids = set()
    if lo is None:
        return ids
    for idx in range(lo, min(hi, len(lines))):
        raw = lines[idx].strip()
        if not raw.startswith("|"):
            continue
        first = raw.strip("|").split("|")[0]
        ids.update(CG_ID_SHAPE.findall(first))
    return ids


def check_pending_ledger(text: str, report: Report):
    lines = text.splitlines()
    report.section("遗留存活性台账 — 结构合法性与到期披露（检查 7，FAIL 档）")

    lo, hi = find_section(lines, r"^十一、遗留存活性台账")
    if lo is None:
        report.fail("未找到 §十一「遗留存活性台账」章节 —— 遗留事项失去到期机算面")
        return

    ledger = None
    for tbl in iter_md_tables(lines, lo, hi):
        if (find_col(tbl["header"], ("编号",)) is not None
                and find_col(tbl["header"], ("到期日", "到期")) is not None):
            ledger = tbl
            break
    if ledger is None:
        report.fail("§十一 内未找到台账表（须含「编号」与「到期日」两列；表头感知解析，不猜列号）")
        return

    cols: Dict[str, int] = {}
    missing: List[str] = []
    for name, aliases in LEDGER_COLS:
        i = find_col(ledger["header"], aliases)
        if i is None:
            missing.append(name)
        else:
            cols[name] = i
    if missing:
        report.fail(f"台账表缺必需列 {'、'.join(missing)}（实读表头：{'|'.join(ledger['header'])}）")
        return

    cg_ids = collect_cg_log_ids(lines)
    if not cg_ids:
        report.fail("§九 变更日志未解析出任何 CG 编号 —— 键闭合失去真值源，本检查不得判绿")
        return

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    shape_bad: List[Tuple[int, str]] = []
    dup_ids: List[str] = []
    status_bad: List[Tuple[int, str, str]] = []
    date_bad: List[Tuple[int, str, str, str]] = []
    pending_no_due: List[Tuple[int, str]] = []
    order_bad: List[Tuple[int, str, str, str]] = []
    closed_no_basis: List[Tuple[int, str, str]] = []
    dangling: List[Tuple[int, str, str, str]] = []
    src_empty: List[Tuple[int, str]] = []
    colcount_bad: List[Tuple[int, int]] = []
    overdue: List[Tuple[str, str, int]] = []
    soon: List[Tuple[str, str, int]] = []
    over_ttl: List[Tuple[str, int]] = []
    seen: set = set()
    n_pending = n_closed = n_refused = 0

    for line_no, cells in ledger["rows"]:
        if len(cells) != len(ledger["header"]):
            colcount_bad.append((line_no, len(cells)))

        def cell(name: str, _cells=cells) -> str:
            i = cols[name]
            return _cells[i].strip() if i < len(_cells) else ""

        pid = cell("编号")
        if not LEDGER_ID_SHAPE.match(pid):
            shape_bad.append((line_no, pid))
        elif pid in seen:
            dup_ids.append(pid)
        else:
            seen.add(pid)

        status = cell("状态")
        if status not in LEDGER_STATUS_ENUM:
            status_bad.append((line_no, pid, status))
        elif status == "待处置":
            n_pending += 1
        elif status == "已闭合":
            n_closed += 1
        else:
            n_refused += 1

        reg_raw, due_raw = cell("登记日期"), cell("到期日")
        reg = ledger_date(reg_raw)
        if reg is None:
            date_bad.append((line_no, pid, "登记日期", reg_raw))
        if ledger_blank(due_raw):
            due = None
            if status == "待处置":
                pending_no_due.append((line_no, pid))
        else:
            due = ledger_date(due_raw)
            if due is None:
                date_bad.append((line_no, pid, "到期日", due_raw))
        if reg is not None and due is not None and due < reg:
            order_bad.append((line_no, pid, reg_raw, due_raw))

        basis = cell("处置批次／依据")
        if status in LEDGER_CLOSED_STATES and ledger_blank(basis):
            closed_no_basis.append((line_no, pid, status))

        for col_name in ("来源登记", "处置批次／依据"):
            raw = cell(col_name)
            if col_name == "来源登记" and ledger_blank(raw):
                src_empty.append((line_no, pid))
            for cid in CG_ID_SHAPE.findall(raw):
                if cid not in cg_ids:
                    dangling.append((line_no, pid, col_name, cid))

        if status == "待处置" and due is not None:
            left = (due - today).days
            if left < 0:
                overdue.append((pid, due_raw, -left))
            elif left <= LEDGER_SOON_DAYS:
                soon.append((pid, due_raw, left))
            if reg is not None and (due - reg).days > LEDGER_TTL_EVENT:
                over_ttl.append((pid, (due - reg).days))

    report.ok(f"台账表就位：{len(ledger['rows'])} 行 × {len(ledger['header'])} 列，"
              f"必需 {len(LEDGER_COLS)} 列齐备（编号／事项／来源登记／登记日期／到期日／状态／处置依据）")
    report.ok(f"状态分布：待处置 {n_pending} ／ 已闭合 {n_closed} ／ 已裁定不做 {n_refused}"
              f"（三值闭集 {'/'.join(LEDGER_STATUS_ENUM)}）")

    if colcount_bad:
        for ln, n in colcount_bad:
            report.fail(f"L{ln} 行列数 {n} ≠ 表头列数 {len(ledger['header'])}")
    else:
        report.ok(f"行列数与表头列数逐行一致（{len(ledger['rows'])} 行）")

    if shape_bad:
        for ln, pid in shape_bad:
            report.fail(f"L{ln} 编号 '{pid}' 不合 PL-nnn 形制（台账编号须跨批唯一且可机读）")
    else:
        report.ok(f"编号形制全部合法（PL-nnn，{len(seen)} 个）")
    if dup_ids:
        report.fail(f"编号重复 {len(dup_ids)} 处：{'、'.join(dup_ids)}")
    else:
        report.ok("编号零重复")

    if status_bad:
        for ln, pid, st in status_bad:
            report.fail(f"L{ln} {pid}：状态 '{st}' 不在三值枚举内")
    else:
        report.ok("状态值全部落在 §11.1 三值枚举内")

    if date_bad:
        for ln, pid, col_name, raw in date_bad:
            report.fail(f"L{ln} {pid}：{col_name} '{raw}' 不可解析（须 YYYY-MM-DD，"
                        f"空值只允许 '—' 且仅限已闭合／已裁定不做行的到期日）")
    else:
        report.ok("登记日期与到期日字面全部可解析")
    if pending_no_due:
        for ln, pid in pending_no_due:
            report.fail(f"L{ln} {pid}：状态为待处置但到期日为空 —— 失去 TTL 约束即回到"
                        f"「登记即永久免检」")
    else:
        report.ok(f"待处置行到期日全部非空（{n_pending} 行）")
    if order_bad:
        for ln, pid, reg_raw, due_raw in order_bad:
            report.fail(f"L{ln} {pid}：登记日期 {reg_raw} 晚于到期日 {due_raw}")
    else:
        report.ok("日期链方向合法（登记日期 ≤ 到期日）")

    if closed_no_basis:
        for ln, pid, st in closed_no_basis:
            report.fail(f"L{ln} {pid}：状态 '{st}' 但处置批次／依据为空 —— 无依据的终态不采信")
    else:
        report.ok(f"已闭合／已裁定不做行依据全部非空（{n_closed + n_refused} 行）")

    if src_empty:
        for ln, pid in src_empty:
            report.fail(f"L{ln} {pid}：来源登记为空 —— 遗留事项失去可回溯登记来源，"
                        f"无法判断其是否已被后续批次处置")
    else:
        report.ok(f"来源登记列全部非空（{len(ledger['rows'])} 行）")

    if dangling:
        for ln, pid, col_name, cid in dangling:
            report.fail(f"L{ln} {pid}：{col_name} 引用的 '{cid}' 不在 §九 变更日志内"
                        f"（键闭合，真值源＝§九 实读 {len(cg_ids)} 个 CG 编号）")
    else:
        report.ok(f"来源／处置列引用的 CG 编号全部落在 §九 变更日志内"
                  f"（键闭合，真值源实读 {len(cg_ids)} 个）")

    if overdue:
        report.warn(f"待处置且已超到期日 {len(overdue)} 项 —— 触发 §11.1「须重新裁定」义务"
                    f"（三择一：处置／续期并写明理由／改判不做）；到期不等于失效，不计 fail_count")
        for pid, due_raw, days in overdue:
            report.info(f"  超期 {pid}：到期日 {due_raw}，已过 {days} 天")
    else:
        report.ok(f"待处置项零超期（{n_pending} 项，判据＝到期日 ≥ 今天）")
    for pid, due_raw, left in soon:
        report.info(f"  预警 {pid}：{left} 天内到期（{due_raw}），窗口 {LEDGER_SOON_DAYS} 天")
    if over_ttl:
        report.warn(f"待处置行 TTL 超 §11.1 上限 {LEDGER_TTL_EVENT} 天共 {len(over_ttl)} 项："
                    + "、".join(f"{pid}（{d} 天）" for pid, d in over_ttl)
                    + " —— 续期合法但须在处置批次／依据列写明续期理由")
    else:
        report.ok(f"待处置行 TTL 均未超口径上限（常规 {LEDGER_TTL_DEFAULT} 天／"
                  f"事件驱动 {LEDGER_TTL_EVENT} 天／限期明写）")

    report.info("覆盖面限制（§11.3）：只做「台账 → §九」方向键闭合，不反查 CG 行散文声明的遗留"
                "（散文字面无稳定形态，正则会产假信号），故「新遗留漏登记进台账」仍靠人工")
    report.info("口径：到期由治具求值、不由散文自报（CG-20260917-009 同构）；"
                "到期只披露不否定既有登记，单纯到期不增加 fail_count")


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

    # 检查 5：SRE 静态体检 T-A1—T-A5（T-A1 自 v1.8.0 起 FAIL 档；其余首轮 WARN）
    check_sre_static(base_dir, runtime_dir, report, si_text, std_rows, std_names)

    # 检查 6：治理文件跨层一致性（FAIL 档，计入 fail_count）
    check_cross_layer(base_dir, report)

    # 检查 7：遗留存活性台账（PENDING-TTL 本仓化，FAIL 档，计入 fail_count）
    cg_path = base_dir / "change-governance.md"
    cg_text = read_file(cg_path, "变更治理规则")
    if cg_text:
        check_pending_ledger(cg_text, report)
    else:
        report.section("遗留存活性台账 — 结构合法性与到期披露（检查 7，FAIL 档）")
        report.fail("文件不存在，跳过")

    # 输出报告
    fail_count = report.print_report()
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
