#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能仓备份同步脚本
sync_skill_backup.py v1.0（2026-08-07）

用途：将 skills 仓（~/.qoderwork/skills）中装配式装修合集相关的运行时技能
与治理文件镜像备份到项目仓 技能仓备份/ 目录，随项目仓推送获得异地副本，
弥补运行时技能文件（SKILL/reference/examples 定稿本体）仅存于本地的缺口。

备份范围：
  1. 合集技能目录 15 个（注册表 12 技能 + QA + WF + 治理/核验辅助 2 个）：
     OR/PW/WS/CL/FL/BK/ST/MI/AC/ME/SR/QA/WF 对应目录 +
     prefab-governance-sync、scanned-standard-clause-verify
  2. skills 根治理文件：standards-index.md、platform-adapter-reference.md
  3. shared/ 治理镜像 6 文件（不含 *_pre_* 历史备份）
     change-governance / glossary / interface-contracts /
     platform-adapter-reference / redlines-registry / standards-index

不备份：系统安装的通用技能（lark/docx/pdf 等）、_pre_* 备份文件、
ACE 与 SRE（其文件本体在项目仓 _专题_ACE开发/ 与 _专题_技能合集策划/，
已由项目仓自身承载）。

更新机制（何时运行）：
  - 每次涉及运行时技能文件或治理文件的 CG 变更发布后运行一次；
  - 每月至少运行一次 --check 核对漂移；
  - 运行后随项目仓提交推送（提交信息注明"技能仓备份同步"）。

恢复方法：将 技能仓备份/ 下各技能目录与 shared/ 复制回
~/.qoderwork/skills/ 对应位置即可。

用法：
  python sync_skill_backup.py            # 增量镜像同步 + 生成同步说明.md
  python sync_skill_backup.py --check    # 只比对不写盘，输出差异清单

依赖：Python 3.8+（仅标准库）
"""

import sys
import io
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# ── 路径与范围 ────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DST = PROJECT_ROOT / "技能仓备份"
SRC = Path.home() / ".qoderwork" / "skills"

SKILL_DIRS = [
    "prefab-interior-systems-orchestrator",      # OR 总入口
    "prefab-partition-wall-solution",            # PW 隔墙
    "prefab-wall-surface-system",                # WS 墙面
    "prefab-ceiling-system",                     # CL 吊顶
    "prefab-floor-system",                       # FL 楼地面
    "prefab-bathroom-kitchen-system",            # BK 厨卫
    "prefab-storage-system",                     # ST 收纳
    "prefab-mep-integration-system",             # MI 机电集成
    "prefab-acceptance-checklist-generator",     # AC 验收清单
    "prefab-interior-materials-expert",          # ME 材料专家
    "prefab-standards-reviewer",                 # SR 标准复核
    "skill-qa-tester",                           # QA 测试工具
    "waterproofing-expert",                      # WF 防水协作
    "prefab-governance-sync",                    # 治理同步流程
    "scanned-standard-clause-verify",            # S1 条文核验流水线
]

ROOT_FILES = [
    "standards-index.md",
    "platform-adapter-reference.md",
]

SHARED_FILES = [
    "change-governance.md",
    "glossary.md",
    "interface-contracts.md",
    "platform-adapter-reference.md",
    "redlines-registry.md",
    "standards-index.md",
]

MANIFEST_NAME = "同步说明.md"


# ── 工具 ─────────────────────────────────────────────────
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(root: Path, exclude_artifacts: bool = True):
    """返回 root 下全部文件的相对路径字典。
    始终跳过 _pre_* 备份与清单自身；exclude_artifacts=True 时另跳过
    隐藏文件与 .bak（用于源范围收集）；目标侧扫描传 False，
    以便镜像清理能发现并删除多余的产物文件。"""
    out = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if "_pre_" in p.name or p.name == MANIFEST_NAME:
            continue
        if exclude_artifacts and (p.name.startswith(".") or p.name.endswith(".bak")):
            continue
        out[p.relative_to(root).as_posix()] = p
    return out


def collect_scope():
    """收集备份范围内的源文件 → (源路径, 备份内相对路径)"""
    scope = {}
    for d in SKILL_DIRS:
        src_dir = SRC / d
        for rel, p in walk_files(src_dir).items():
            scope[f"{d}/{rel}"] = p
    for fn in ROOT_FILES:
        p = SRC / fn
        if p.exists():
            scope[fn] = p
    for fn in SHARED_FILES:
        p = SRC / "shared" / fn
        if p.exists():
            scope[f"shared/{fn}"] = p
    return scope


def sync(check_only: bool) -> int:
    # 强制 UTF-8 输出，避免中文终端 GBK 乱码
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    if not SRC.exists():
        print(f"[错误] skills 源目录不存在：{SRC}")
        return 1

    scope = collect_scope()
    missing_src = [d for d in SKILL_DIRS if not (SRC / d).exists()]
    if missing_src:
        print(f"[警告] 以下技能目录在源中不存在，跳过：{missing_src}")

    # 目标侧现有文件（已镜像部分）
    dst_files = walk_files(DST, exclude_artifacts=False)

    added, updated, removed, same = [], [], [], []
    for rel, src_p in sorted(scope.items()):
        dst_p = DST / rel
        src_h = sha256(src_p)
        if rel in dst_files:
            dst_h = sha256(dst_files[rel])
            if src_h == dst_h:
                same.append(rel)
                continue
            updated.append(rel)
        else:
            added.append(rel)
        if not check_only:
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_p, dst_p)

    # 目标侧多余文件（源中已删除）→ 镜像清理
    for rel in sorted(set(dst_files) - set(scope)):
        removed.append(rel)
        if not check_only:
            (DST / rel).unlink()

    # 清理空目录
    if not check_only:
        for d in sorted([p for p in DST.rglob("*") if p.is_dir()],
                        key=lambda x: len(x.parts), reverse=True):
            try:
                d.rmdir()
            except OSError:
                pass

    mode = "检查模式（未写盘）" if check_only else "同步完成"
    print(f"== 技能仓备份{mode} ==")
    print(f"范围：{len(scope)} 个文件（技能目录 {len(SKILL_DIRS)} 个 + 根治理文件 + shared 6 文件）")
    print(f"一致 {len(same)} | 新增 {len(added)} | 更新 {len(updated)} | 移除 {len(removed)}")
    for label, lst in (("新增", added), ("更新", updated), ("移除", removed)):
        for rel in lst:
            print(f"  [{label}] {rel}")

    # 生成同步说明（仅同步模式）
    if not check_only:
        dst_files = walk_files(DST, exclude_artifacts=False)
        lines = [
            "# 技能仓备份 — 同步说明",
            "",
            f"> 最后同步：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}（sync_skill_backup.py v1.0）",
            f"> 源目录：`{SRC.as_posix()}`",
            "> 备份目的：运行时技能文件本体（SKILL/reference/examples）仅存于 skills 仓本地，",
            "> 本目录随项目仓推送提供异地副本。恢复时将各目录复制回 skills 仓对应位置即可。",
            ">",
            "> 更新机制：① 每次涉及运行时技能文件或治理文件的 CG 变更发布后运行一次同步；",
            "> ② 每月至少一次 `--check` 核对漂移；③ 同步后随项目仓提交推送。",
            ">",
            "> 范围说明：仅含合集相关 15 个技能目录 + 根治理文件 + shared 治理 6 文件；",
            "> 不含系统通用技能（lark/docx/pdf 等）与 `*_pre_*` 历史备份；",
            "> ACE 与 SRE 文件本体在项目仓 _专题_ACE开发/ 与 _专题_技能合集策划/，不重复备份。",
            "",
            f"文件总数：{len(dst_files)}",
            "",
            "| 文件（备份内相对路径） | SHA-256 | 字节 |",
            "|---|---|---|",
        ]
        for rel, p in sorted(dst_files.items()):
            lines.append(f"| {rel} | {sha256(p)} | {p.stat().st_size} |")
        (DST / MANIFEST_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"清单已写入：{DST / MANIFEST_NAME}")

    return 0


def main():
    check_only = "--check" in sys.argv
    return sync(check_only)


if __name__ == "__main__":
    sys.exit(main())
