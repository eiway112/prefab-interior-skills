#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门禁临时面单源（gate_scratch）——门禁测试件的临时仓／临时镜像落点与自清规则。

落点：`工作区根/_整理与清理/<YYYY-MM-DD>/门禁临时面-<件名>/`

为什么是这里（三条判据，缺一不可）：
  1. 不得落本仓内——临时 git 仓会成嵌套仓，且会被 `sync_skill_backup.py` 当新增件带进镜像；
  2. 不得落 C 盘／系统 temp——临时文件纪律要求落在工作区根以内的既有治理目录；
  3. 不得在工作区根新建常驻目录——根目录只允许出现《_管理规范/文件与项目管理规范》§一
     登记的目录，由 `_工具/workspace_health.py::check_root_dir_whitelist` 机算（未登记即 FAIL）。
     `_整理与清理/` 是已登记的过渡性文件容器，其定义即"可定期清理"，且根仓 `.gitignore`
     整目录排除，故临时面落此既不进版本控制、也不给根目录增加任何新条目。

自清：进程退出时 rmtree 本件自己的临时面，并回收因此变空的日期目录（止于 `_整理与清理/`，
该目录本体常驻，不回收）。日期目录已有他物时 `rmdir` 失败即止，不误删。
Windows 下 git 把 object 文件写成只读，直接 rmtree 报 WinError 5，故清理前统一解只读位。

用法：
    import gate_scratch
    SCRATCH_ROOT = gate_scratch.scratch_dir("cross_layer_eol")
依赖：Python 3.8+（仅标准库）
"""

import atexit
import datetime
import os
import shutil
import stat
from pathlib import Path

PROGRAM_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROGRAM_DIR.parent
WORKSPACE_ROOT = REPO_ROOT.parent
TRANSIENT_ROOT = WORKSPACE_ROOT / "_整理与清理"


def force_rmtree(target):
    """解只读位后 rmtree；target 不存在即静默返回。"""
    target = Path(target)
    if not target.exists():
        return
    for dirpath, dirnames, filenames in os.walk(target):
        for n in dirnames + filenames:
            try:
                os.chmod(os.path.join(dirpath, n), stat.S_IWRITE)
            except OSError:
                pass
    shutil.rmtree(target, onerror=lambda func, path, _exc: (
        os.chmod(path, stat.S_IWRITE), func(path)))


def _prune_empty_dirs(start, stop):
    """自 start 逐级 rmdir，遇非空／到达 stop 即止。"""
    cur = Path(start)
    stop = Path(stop)
    while cur != stop and cur.parent != cur:
        try:
            cur.rmdir()
        except OSError:
            return
        cur = cur.parent


def _cleanup(root):
    force_rmtree(root)
    _prune_empty_dirs(Path(root).parent, TRANSIENT_ROOT)


def scratch_dir(gate_name):
    """返回（并创建）指定门禁件的临时面根目录，同时登记进程退出自清。

    gate_name 用 ASCII（其下会建临时 git 仓与拷贝运行时技能件，路径含中文虽已验证可用，
    但临时面无中文命名收益）；容器名 `门禁临时面-` 用中文，符合根目录以下业务层命名要求。
    """
    today = datetime.date.today().isoformat()
    root = TRANSIENT_ROOT / today / ("门禁临时面-" + gate_name)
    root.mkdir(parents=True, exist_ok=True)
    atexit.register(_cleanup, root)
    return root
