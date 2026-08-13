"""
SRE Reasoner —— 标准推理引擎参考实现
=====================================
版本：v1.2（2026-08-13）
依据：standards-reasoning-rules.md v1.2 + interface-contracts.md IC-10 v1.5.8

最小接口：
    reason(project_type, space_type, location=None, system=None,
           demands=None, return_trace=False) -> dict

输出符合 IC-10-Response Schema v1.5.8，包含：
- 适用标准集
- 推理路径
- 证据对象（至少一条）
- 未覆盖领域（可选）
- 决策轨迹（return_trace=True 时）
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# M1 编号前缀分类协议（standards-reasoning-rules.md §1.2 / §1.4）
# ---------------------------------------------------------------------------

PREFIX_PATTERNS: list[tuple[str, str, str, str, str]] = [
    # (正则, 标准类型, 默认层级, 默认权限, 地域范围)
    (r"^GB\s+55\d{3}", "全文强制性国标", "L1", "red_line", "全国"),
    (r"^GB\s+50\d{3}", "含强制性条文的国标", "L1", "red_line", "全国"),
    (r"^GB\s+5\d{4}", "含强制性条文的国标", "L1", "red_line", "全国"),
    (r"^GB/T", "推荐性国标", "L2", "binding_support", "全国"),
    (r"^JG\b", "行业标准（建设）", "L2", "binding_support", "全国"),
    (r"^JGJ\b", "行业标准（建设）", "L2", "binding_support", "全国"),
    (r"^JG/T", "推荐性行业标准（建设）", "L2", "binding_support", "全国"),
    (r"^JGJ/T", "推荐性行业标准（建设）", "L2", "binding_support", "全国"),
    (r"^JC\b", "行业标准（建材）", "L2", "binding_support", "全国"),
    (r"^JC/T", "推荐性行业标准（建材）", "L2", "binding_support", "全国"),
    (r"^HG\b", "行业标准（化工）", "L2", "binding_support", "全国"),
    (r"^HG/T", "推荐性行业标准（化工）", "L2", "binding_support", "全国"),
    (r"^DB\d{2}/", "地方标准", "L3", "binding_support", "对应省份"),
    (r"^DBJ\b", "地方建设标准", "L3", "binding_support", "对应省份"),
    (r"^T/", "团体标准", "L4", "reference", "全国（管辖地采纳后适用）"),
    (r"^\d+CJ", "图集", "L3", "reference", "全国或区域"),
    (r"^\d+J\b", "图集", "L3", "reference", "全国或区域"),
    (r"^\d+ZJ", "图集", "L3", "reference", "全国或区域"),
    (r"^RISN-TG", "技术导则", "L2", "reference", "全国"),
]

PROVINCE_MAP: dict[str, str] = {
    "11": "北京", "31": "上海", "44": "广东",
    "33": "浙江", "35": "福建", "46": "海南",
    "32": "江苏", "61": "陕西", "41": "河南",
}

ACOUSTIC_SUBDOMAINS = {"acoustic", "acoustic(impact)", "acoustic(贡献)", "acoustic(吸声)", "acoustic(边界提示)"}


# ---------------------------------------------------------------------------
# M2 锚定集（standards-reasoning-rules.md §2.3）
# ---------------------------------------------------------------------------

ANCHORS: set[str] = {
    "GB 55031-2022", "GB 55037-2022", "GB 55038-2025", "GB 50210-2018", "GB 50118-2010",
    "GB/T 50121-2005", "JGJ/T 491-2021", "DB11/T 1553-2025", "T/CSUS 40-2022",
    "07CJ03-1", "08J931",
    "GB/T 23451-2023", "GB 8624-2012",
}


# ---------------------------------------------------------------------------
# M3 场景→领域激活表（standards-reasoning-rules.md §3.2 Step 1）
# 键：(项目类型, 空间类型)；值：候选域集列表
# ---------------------------------------------------------------------------

ACTIVATION_TABLE: dict[tuple[str, str], list[str]] = {
    ("住宅", "分户墙"): ["acoustic", "fire", "acceptance", "prefab"],
    ("住宅", "户内隔墙"): ["acoustic", "fire", "acceptance"],
    ("酒店", "客房隔墙"): ["acoustic", "fire", "acceptance", "prefab"],
    ("医院", "病房"): ["acoustic", "fire", "acceptance", "environmental"],
    ("医院", "诊疗室"): ["acoustic", "fire", "acceptance", "environmental"],
    ("医院", "病房/诊疗室"): ["acoustic", "fire", "acceptance", "environmental"],
    ("学校", "教室"): ["acoustic", "fire", "acceptance"],
    ("学校", "实验室"): ["acoustic", "fire", "acceptance"],
    ("学校", "教室/实验室"): ["acoustic", "fire", "acceptance"],
    ("办公", "办公室"): ["acoustic", "fire", "acceptance"],
    ("办公", "会议室"): ["acoustic", "fire", "acceptance"],
    ("办公", "办公室/会议室"): ["acoustic", "fire", "acceptance"],
    ("商业", "商铺"): ["fire", "acceptance"],
    ("商业", "展厅"): ["fire", "acceptance"],
    ("商业", "商铺/展厅"): ["fire", "acceptance"],
    ("医院", "病房/手术部墙面"): ["fire", "environmental", "acceptance", "prefab"],
    ("酒店", "客房墙面"): ["acceptance", "prefab", "acoustic(边界提示)"],
    ("住宅", "户内墙面"): ["prefab(认定)", "acceptance", "environmental"],
    ("学校", "教室墙面"): ["fire", "environmental", "acceptance"],
    ("办公", "办公墙面"): ["acceptance", "environmental", "prefab"],
    ("厨卫湿区", "墙板"): ["prefab", "waterproof(外部协同)", "acceptance"],
    ("住宅", "分户楼板"): ["acoustic(impact)", "fire", "acceptance", "prefab"],
    ("住宅", "楼地面"): ["acoustic(impact)", "acceptance", "prefab"],
    ("酒店", "客房地面"): ["acoustic(impact)", "acceptance", "prefab"],
    ("办公", "办公地面"): ["acceptance", "prefab"],
    ("医院", "病房地面"): ["acoustic(impact)", "acceptance", "environmental"],
    ("学校", "教室地面"): ["acoustic(impact)", "acceptance"],
    ("医院", "手术部/洁净吊顶"): ["fire", "environmental", "acceptance", "prefab"],
    ("医院", "病房吊顶"): ["fire", "acceptance", "prefab"],
    ("酒店", "客房吊顶"): ["acoustic(贡献)", "fire", "acceptance", "prefab"],
    ("住宅", "厨卫集成吊顶"): ["acceptance", "prefab", "environmental", "waterproof(边界)"],
    ("住宅", "户内吊顶"): ["acceptance", "prefab"],
    ("学校", "教室吊顶"): ["acoustic(吸声)", "fire", "acceptance"],
    ("办公", "办公吊顶"): ["acoustic(吸声)", "fire", "acceptance"],
}

# 空间类型归一化别名
SPACE_ALIASES: dict[str, str] = {
    "卫生间": "厨卫湿区",
    "厨房": "厨卫湿区",
}


# ---------------------------------------------------------------------------
# M3 Step 2 领域→标准族映射（简化核心族）
# ---------------------------------------------------------------------------

DOMAINS: dict[str, Any] = {
    "acoustic": {
        "住宅": ["GB 55038-2025", "GB 50118-2010", "GB/T 50121-2005"],
        "默认": ["GB 50118-2010", "GB/T 50121-2005"],
        "轻钢龙骨": ["GB/T 19889.1", "JG/T 544-2018", "07CJ03-1", "08J931"],
        "条板": ["GB/T 23451-2023"],
        "吊顶": ["GB/T 11981-2024", "GB/T 9775-2025", "JC/T 564.1-2018", "GB/T 25998-2020", "07CJ03-1", "08J931"],
    },
    "acoustic(impact)": {
        "住宅": ["GB 55038-2025", "GB 50118-2010", "GB/T 50121-2005"],
        "默认": ["GB 50118-2010", "GB/T 50121-2005"],
        "浮筑地面": ["GB/T 19889.7-2022", "GB/T 19889.8-2006", "GB/T 45305.3-2026", "08J931"],
        "架空地面": ["08J931"],
    },
    "fire": {
        "全部": ["GB 55037-2022", "GB 50016-2014", "GB 50222-2017"],
        "板材": ["GB 8624-2012", "07CJ03-1"],
        "吊顶": ["GB/T 11981-2024", "GB/T 9775-2025", "JC/T 564.1-2018", "GB/T 25998-2020", "07CJ03-1"],
    },
    "acceptance": {
        "全部": ["GB 50210-2018", "GB 55032-2022", "07CJ03-1"],
        "浙江": ["DB33/T 1168-2019"],
        "北京": ["DB11/T 1553-2025"],
        "广东": ["DBJ/T 15-208-2020"],
        "吊顶": ["GB/T 11981-2024", "GB/T 9775-2025", "JC/T 564.1-2018", "GB/T 25998-2020", "07CJ03-1"],
    },
    "prefab": {
        "全国": ["GB/T 51129-2017", "JGJ/T 491-2021", "RISN-TG 055-2025"],
        "浙江": ["DB33/T 1259-2021"],
        "北京": ["DB11/T 1553-2025"],
        "福建": ["DBJ/T 13-428-2023"],
        "深圳": ["SJG 159-2024"],
        "墙面饰面系统": ["T/CECS 1018-2022", "JG/T 579-2021", "JG/T 578-2021"],
    },
    "environmental": {
        "医院/学校": ["GB 18580-2025", "GB 18582-2020", "T/CSUS 03-2019"],
        "默认": ["GB 18580-2025"],
        "吊顶板材": ["GB 18580-2025", "GB 6566-2010"],
    },
    "waterproof(外部协同)": {
        "默认": ["（外部 waterproofing-expert 技能协同）"],
    },
    "waterproof(边界)": {
        "默认": ["（外部 waterproofing-expert 技能边界咨询）"],
    },
    "prefab(认定)": {
        "默认": ["GB/T 51129-2017", "JGJ/T 491-2021"],
    },
}


# ---------------------------------------------------------------------------
# 标准元数据缓存（优先从 standards-index.md 加载，失败时 fallback）
# ---------------------------------------------------------------------------

STANDARD_NAMES: dict[str, str] = {
    "GB 55031-2022": "民用建筑通用规范",
    "GB 55037-2022": "建筑防火通用规范",
    "GB 55038-2025": "住宅项目规范",
    "GB 50210-2018": "建筑装饰装修工程质量验收标准",
    "GB 50118-2010": "民用建筑隔声设计规范",
    "GB 50016-2014": "建筑设计防火规范（2018 年版）",
    "GB 50222-2017": "建筑内部装修设计防火规范",
    "GB 55032-2022": "建筑与市政工程施工质量控制通用规范",
    "GB/T 50121-2005": "建筑隔声评价标准",
    "GB/T 19889.1": "声学 建筑和建筑构件隔声测量方法",
    "GB/T 19889.7-2022": "声学 建筑和建筑构件隔声测量方法 第7部分：楼板撞击声隔声的现场测量",
    "GB/T 19889.8-2006": "声学 建筑和建筑构件隔声测量方法 第8部分：重质标准楼板覆面层撞击声改善的实验室测量",
    "GB/T 45305.3-2026": "声学 建筑构件隔声的实验室测量 第3部分：撞击声隔声测量",
    "GB/T 23451-2023": "建筑用轻质隔墙条板",
    "GB 8624-2012": "建筑材料及制品燃烧性能分级",
    "JGJ/T 491-2021": "装配式内装修技术标准",
    "JG/T 544-2018": "轻钢龙骨式复合墙体",
    "GB/T 11981-2024": "建筑用轻钢龙骨",
    "GB/T 9775-2025": "纸面石膏板",
    "JC/T 564.1-2018": "纤维增强硅酸钙板 第1部分：无石棉硅酸钙板",
    "GB/T 25998-2020": "矿物棉装饰吸声板",
    "GB/T 51129-2017": "装配式建筑评价标准",
    "RISN-TG 055-2025": "装配式内装修技术导则",
    "DB11/T 1553-2025": "装配式剪力墙结构设计规程",
    "DB33/T 1168-2019": "装配式住宅建筑评价标准",
    "DBJ/T 15-208-2020": "广东省装配式建筑评价标准",
    "DB33/T 1259-2021": "浙江省装配式建筑评价标准",
    "DBJ/T 13-428-2023": "福建省装配式建筑评价标准",
    "SJG 159-2024": "装配式装修评价标准",
    "T/CECS 1018-2022": "装配式住宅建筑装修技术规程",
    "JG/T 579-2021": "建筑用集成墙面",
    "JG/T 578-2021": "建筑用轻质高强陶瓷板",
    "GB 18580-2025": "室内装饰装修材料 人造板及其制品中甲醛释放限量",
    "GB 18582-2020": "建筑用墙面涂料中有害物质限量",
    "GB 6566-2010": "建筑材料放射性核素限量",
    "T/CSUS 03-2019": "医院建筑室内装修工程技术标准",
    "T/CSUS 40-2022": "住宅建筑室内振动与噪声控制技术标准",
    "07CJ03-1": "轻钢龙骨石膏板隔墙、吊顶",
    "08J931": "隔声、吸声构造",
}

STANDARD_STATUS: dict[str, str] = {}


def _load_standards_index() -> None:
    """尝试从 ../shared/standards-index.md 加载标准状态。"""
    candidates = [
        Path(__file__).parent.parent / "shared" / "standards-index.md",
        Path(__file__).parent.parent / "standards-index.md",
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 7:
                continue
            # 匹配 | 序号 | 标准编号 | 标准名称 | ... | 状态 | ...
            if re.match(r"^\d+$", parts[1]):
                std_no = parts[2]
                name = parts[3]
                status = parts[6]
                if std_no:
                    STANDARD_NAMES.setdefault(std_no, name)
                    STANDARD_STATUS[std_no] = status


def _standard_name(std_no: str) -> str:
    return STANDARD_NAMES.get(std_no, std_no)


def _standard_status(std_no: str) -> str:
    return STANDARD_STATUS.get(std_no, "现行有效")


# ---------------------------------------------------------------------------
# M1 分类
# ---------------------------------------------------------------------------

def classify_standard(std_no: str, evidence_list: list[dict]) -> dict[str, Any]:
    """对单个标准编号执行 M1 五步分类。"""
    std_no_norm = std_no.strip()
    matched = None
    for pat, std_type, level, authority, scope in PREFIX_PATTERNS:
        if re.match(pat, std_no_norm):
            matched = (std_type, level, authority, scope)
            break

    if matched is None:
        evidence_list.append(_evidence(
            "degradation", "standards-reasoning-rules.md §1.4 / §五 M6",
            f"标准编号={std_no_norm}",
            f"前缀不可识别，降级为 unknown_type / reference / inferred",
            "inferred"
        ))
        return {
            "标准编号": std_no_norm,
            "标准类型": "unknown_type",
            "层级": "L4",
            "权限": "reference",
            "地域范围": "未知",
            "性能领域": [],
            "分类置信度": "inferred",
        }

    std_type, level, authority, scope = matched

    # 地域范围细化
    actual_scope = scope
    if std_no_norm.startswith(("DB", "DBJ")):
        m = re.search(r"DB\s*(\d{2})", std_no_norm)
        if m:
            province_code = m.group(1)
            province = PROVINCE_MAP.get(province_code, province_code)
            actual_scope = province
        else:
            actual_scope = "待确认省份"

    # 性能领域推断（简化）
    domains: list[str] = []
    if any(k in std_no_norm for k in ["55037", "50016", "50222", "防火", "耐火", "燃烧"]):
        domains.append("fire")
    if any(k in std_no_norm for k in ["50118", "55038", "50121", "19889", "45305", "隔声", "声学"]):
        domains.append("acoustic")
    if any(k in std_no_norm for k in ["55031", "50210", "55032", "验收", "质量"]):
        domains.append("acceptance")
    if any(k in std_no_norm for k in ["491", "1553", "装配式", "装配化"]):
        domains.append("prefab")
    if any(k in std_no_norm for k in ["8624", "23451", "544", "产品"]):
        domains.append("product")
    if any(k in std_no_norm for k in ["18580", "18582", "6566", "室内", "空气", "甲醛"]):
        domains.append("environmental")

    evidence_list.append(_evidence(
        "classification", "standards-reasoning-rules.md §1.2 / §1.4",
        f"标准编号={std_no_norm}",
        f"类型={std_type}, 层级={level}, 权限={authority}, 地域={actual_scope}, 领域={domains}",
        "deterministic" if std_type != "unknown_type" else "inferred"
    ))

    return {
        "标准编号": std_no_norm,
        "标准类型": std_type,
        "层级": level,
        "权限": authority,
        "地域范围": actual_scope,
        "性能领域": domains,
        "分类置信度": "deterministic",
    }


# ---------------------------------------------------------------------------
# M3 场景推理
# ---------------------------------------------------------------------------

def _activate_domains(
    project_type: str,
    space_type: str,
    demands: list[str] | None,
    evidence_list: list[dict],
) -> tuple[set[str], str]:
    """M3 Step 1 / Step 1a：返回激活域集与裁定说明。"""
    # 先尝试精确匹配，再尝试空间类型归一化
    key = (project_type, space_type)
    candidates = ACTIVATION_TABLE.get(key)
    if candidates is None and space_type in SPACE_ALIASES:
        key = (project_type, SPACE_ALIASES[space_type])
        candidates = ACTIVATION_TABLE.get(key)

    if candidates is None:
        # 任意 | 任意 最小集
        candidates = ["fire", "acceptance"]
        evidence_list.append(_evidence(
            "activation", "standards-reasoning-rules.md §3.2 Step 1（最小集）",
            f"项目类型={project_type}, 空间类型={space_type}",
            "未命中场景表，使用最小集 fire + acceptance",
            "inferred"
        ))
    else:
        evidence_list.append(_evidence(
            "activation", "standards-reasoning-rules.md §3.2 Step 1",
            f"项目类型={project_type}, 空间类型={space_type}",
            f"命中场景行，候选域={candidates}",
            "deterministic"
        ))

    # 最小集始终激活
    activated = set(candidates) | {"fire", "acceptance"}

    # Step 1a 性能需求裁定（仅 acoustic 子域族）
    arbitration_note = ""
    if demands:
        acoustic_demands = {"隔声", "撞击声", "吸声"}
        has_acoustic = bool(set(demands) & acoustic_demands)
        if has_acoustic:
            # 增补对应子域
            if "楼板" in space_type or "地面" in space_type or "分户楼板" in space_type:
                activated.add("acoustic(impact)")
                arbitration_note = "性能需求含声学类，增补 acoustic(impact)"
            elif "吊顶" in space_type:
                activated.add("acoustic(贡献)")
                arbitration_note = "性能需求含声学类，增补 acoustic(贡献)"
            elif "教室" in space_type or "办公" in space_type:
                activated.add("acoustic(吸声)")
                arbitration_note = "性能需求含声学类，增补 acoustic(吸声)"
            else:
                activated.add("acoustic")
                arbitration_note = "性能需求含声学类，增补 acoustic"
        else:
            # 过滤候选集中的 acoustic 子域（边界提示除外）
            filtered = {d for d in activated if d not in ACOUSTIC_SUBDOMAINS or d == "acoustic(边界提示)"}
            removed = activated - filtered
            activated = filtered
            if removed:
                arbitration_note = f"性能需求不含声学类，过滤 {sorted(removed)}"

        if arbitration_note:
            evidence_list.append(_evidence(
                "arbitration", "standards-reasoning-rules.md §3.2 Step 1a",
                f"性能需求={demands}",
                arbitration_note,
                "deterministic"
            ))

    return activated, arbitration_note


def _map_domain_to_standards(
    domain: str,
    project_type: str,
    location: str | None,
    system: str | None,
    evidence_list: list[dict],
) -> list[str]:
    """M3 Step 2：将单个领域映射到标准族。"""
    mapping = DOMAINS.get(domain, {})
    standards: list[str] = []

    # 基础族
    if project_type == "住宅" and "住宅" in mapping:
        standards.extend(mapping["住宅"])
    elif "全部" in mapping:
        standards.extend(mapping["全部"])
    elif "默认" in mapping:
        standards.extend(mapping["默认"])
    elif "医院/学校" in mapping and project_type in ("医院", "学校"):
        standards.extend(mapping["医院/学校"])

    # 地点附加
    if location and location in mapping:
        standards.extend(mapping[location])

    # 构造体系附加
    if system and system in mapping:
        standards.extend(mapping[system])

    # 特殊：墙面饰面系统
    if domain == "prefab" and system and "墙面" in system:
        standards.extend(mapping.get("墙面饰面系统", []))

    # 去重保序
    seen = set()
    unique: list[str] = []
    for s in standards:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    evidence_list.append(_evidence(
        "mapping", "standards-reasoning-rules.md §3.2 Step 2",
        f"领域={domain}, 项目类型={project_type}, 所在地={location}, 构造体系={system}",
        f"标准族={unique}",
        "deterministic" if unique else "inferred"
    ))
    return unique


# ---------------------------------------------------------------------------
# M4 适用性裁判
# ---------------------------------------------------------------------------

def _apply_applicability(
    standards: list[dict],
    location: str | None,
    evidence_list: list[dict],
) -> list[dict]:
    """M4 LA/GS/TA/MD：分配角色、地域适用性、时间状态。"""
    result: list[dict] = []
    for std in standards:
        std_no = std["标准编号"]
        level = std["层级"]
        authority = std["权限"]

        # 地域适用性（LA-1 / LA-3）
        if std_no.startswith(("DB", "DBJ")):
            province = std.get("地域范围", "未知")
            if location and province in (location, location.rstrip("省市") + "省", location.rstrip("省市") + "市"):
               地域适用性 = "项目所在地适用"
            elif location:
                地域适用性 = "不适用仅作对比"
            else:
                地域适用性 = "待确认"
        elif std_no.startswith("T/"):
            地域适用性 = "全国（合同/地方采纳后适用）"
        else:
            地域适用性 = "全国"

        # 时间状态（TA 规则组）
        status = _standard_status(std_no)
        时间状态 = status
        if status == "被部分替代":
            时间状态 = "过渡期"
        elif status.startswith("已废止"):
            时间状态 = "已废止"

        # 角色分配（Step 4）
        if level == "L1":
            role = "mandatory_check"
        elif level in ("L2", "L3") and authority == "binding_support":
            role = "design_basis"
        elif "测量" in _standard_name(std_no) or "评价" in _standard_name(std_no):
            role = "verification_reference"
        elif level == "L3" or "图集" in std["标准类型"]:
            role = "construction_guide"
        elif "评价" in std["标准类型"] or "51129" in std_no or "SJG" in std_no:
            role = "prefab_evaluation"
        else:
            role = "reference"

        evidence_list.append(_evidence(
            "applicability", "standards-reasoning-rules.md §四 M4 / §3.2 Step 4",
            f"标准={std_no}, 层级={level}, 权限={authority}, 所在地={location}",
            f"地域适用性={地域适用性}, 时间状态={时间状态}, 角色={role}",
            "deterministic" if 地域适用性 != "待确认" else "inferred"
        ))

        result.append({
            "标准编号": std_no,
            "标准名称": _standard_name(std_no),
            "层级": level,
            "权限": authority,
            "角色": role,
            "地域适用性": 地域适用性,
            "时间状态": 时间状态,
        })

    return result


def _role_priority(role: str) -> int:
    order = ["mandatory_check", "design_basis", "verification_reference", "construction_guide", "prefab_evaluation"]
    return order.index(role) if role in order else 99


# ---------------------------------------------------------------------------
# 证据对象与决策轨迹
# ---------------------------------------------------------------------------

_evidence_counter = 0


def _evidence(
    evidence_type: str,
    rule_source: str,
    input_fact: str,
    output_conclusion: str,
    confidence: str,
) -> dict:
    global _evidence_counter
    _evidence_counter += 1
    return {
        "证据ID": f"EVID-{_evidence_counter:03d}",
        "证据类型": evidence_type,
        "规则来源": rule_source,
        "输入事实": input_fact,
        "输出结论": output_conclusion,
        "置信度": confidence,
    }


def _build_trace(
    project_type: str,
    space_type: str,
    location: str | None,
    system: str | None,
    demands: list[str] | None,
    activated: set[str],
    standards: list[dict],
    arbitration_note: str,
) -> str:
    lines = [
        f"Step 0 输入: 项目类型={project_type}, 空间类型={space_type}, 所在地={location or '未提供'}, 构造体系={system or '未提供'}, 性能需求={demands or '按规范'}",
        f"Step 1 激活域: {', '.join(sorted(activated))}",
        f"Step 1a 裁定: {arbitration_note or '性能需求未提供或不含声学类，按候选域原样保留'}",
        f"Step 2 族映射: 共涉及 {len(standards)} 条标准",
        "Step 3 权限裁决: L1 优先于 L2/L3/L4；地方标准严于国标时优先",
        "Step 4 角色分配: 按 mandatory_check → design_basis → verification_reference → construction_guide → prefab_evaluation 分配",
        "Step 5 排序输出: 按角色优先级排序",
        "Step 6 标注: 地域适用性与时间状态已标注",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def reason(
    project_type: str,
    space_type: str,
    location: str | None = None,
    system: str | None = None,
    demands: list[str] | None = None,
    return_trace: bool = False,
) -> dict:
    """
    执行标准推理引擎（SRE）。

    参数与 IC-10-Request v1.5.8 对齐。
    """
    global _evidence_counter
    _evidence_counter = 0
    evidence_list: list[dict] = []

    # M6 降级：项目地点未提供时 LA-4 追问
    uncovered: list[str] = []
    if not location:
        evidence_list.append(_evidence(
            "degradation", "standards-reasoning-rules.md §4.1 LA-4 / §五 M6",
            "项目所在地未提供",
            "跳过地方标准适用性判定，提示追问项目所在地",
            "deterministic"
        ))
        uncovered.append("地方标准适用性（需确认项目所在地）")

    # Step 1 / 1a
    activated, arbitration_note = _activate_domains(project_type, space_type, demands, evidence_list)

    # Step 2
    raw_standards: list[str] = []
    for domain in sorted(activated):
        raw_standards.extend(_map_domain_to_standards(domain, project_type, location, system, evidence_list))

    # 去重
    seen = set()
    unique_raw: list[str] = []
    for s in raw_standards:
        if s not in seen and not s.startswith("（"):
            seen.add(s)
            unique_raw.append(s)

    # M1 分类
    classified = [classify_standard(s, evidence_list) for s in unique_raw]

    # M4 适用性裁判
    applied = _apply_applicability(classified, location, evidence_list)

    # Step 5 排序
    applied.sort(key=lambda x: (_role_priority(x["角色"]), x["层级"], x["标准编号"]))

    # 推理路径
    reasoning_path = (
        f"场景({project_type}|{space_type}) → "
        f"激活域({', '.join(sorted(activated))}) → "
        f"标准族({len(applied)}条) → "
        f"角色排序({', '.join(dict.fromkeys(s['角色'] for s in applied))})"
    )

    response: dict[str, Any] = {
        "适用标准集": applied,
        "推理路径": reasoning_path,
        "证据对象": evidence_list,
    }

    if uncovered:
        response["未覆盖领域"] = uncovered

    if return_trace:
        response["决策轨迹"] = _build_trace(
            project_type, space_type, location, system, demands,
            activated, applied, arbitration_note,
        )

    return response


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _load_standards_index()
    import sys

    args = sys.argv[1:]
    if len(args) < 2:
        print("用法: python sre_reasoner.py <项目类型> <空间类型> [项目所在地] [构造体系] [性能需求,逗号分隔] [--trace]")
        sys.exit(1)

    project_type, space_type = args[0], args[1]
    location = args[2] if len(args) > 2 and not args[2].startswith("-") else None
    system = args[3] if len(args) > 3 and not args[3].startswith("-") else None
    demands = args[4].split(",") if len(args) > 4 and not args[4].startswith("-") else None
    return_trace = "--trace" in args

    result = reason(project_type, space_type, location, system, demands, return_trace)
    print(json.dumps(result, ensure_ascii=False, indent=2))
