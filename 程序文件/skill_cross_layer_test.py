#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_cross_layer_test.py — 检查 9「技能件跨层内容一致性」专项测试（第九门禁，CG-20260920-005）

口径沿 index_ref_consistency_test.py（第八门禁）／cross_layer_eol_test.py（第七门禁）：
  - clean 态对真实仓断言：零 FAIL、[OK] 恰 2 条（D 自洽＋字节全等）、纳入判据 62 件、漂移 0／单层缺失 0
  - 每一类违法都须能被注入并复红（「修净后的守卫须仍能失败」），负向注入以临时目录两镜像层
    ＋内存内 ignored_override 直调 check_skill_cross_layer，不落治理件、不改运行时技能件、不对临时面建 git 仓
  - 控制例 C1—C5 证排除面（gitignore 结构判据）、双向互查、降级分支、空跑守卫均非恒真

临时层落点：`D:/Qoder-Files/_tmp-scripts/skill_cross_layer_scratch/`（工作区外，落 C 盘违反临时文件纪律；
落本仓内会被 sync 当新增件带进镜像）。

用法：python -B 程序文件/skill_cross_layer_test.py
依赖：Python 3.8+（仅标准库）
"""

import atexit
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_governance as V  # noqa: E402

SCRATCH_ROOT = Path("D:/Qoder-Files/_tmp-scripts/skill_cross_layer_scratch")
SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)

SKILL_DIRS_2 = "SKILL_DIRS = ['skill-a', 'skill-b']"


def run(runtime_files=None, backup_files=None, *, runtime_exists=True,
        backup_exists=True, skill_dirs_text=SKILL_DIRS_2,
        ignored_override=None, git_probe=V.git_ignored):
    """在临时根下铺两层文件树后直调 check_skill_cross_layer，返回分级读数。

    runtime_files／backup_files：{相对路径: 字节}，键形如 'skill-a/SKILL.md'。
    ignored_override：None 走 git check-ignore（临时面无 git → 由调用方显式给集合绕过）；
    集合则直接采用（相对 backup 根的正斜杠路径，含技能目录前缀）。
    """
    root = Path(tempfile.mkdtemp(prefix="xlayer-", dir=str(SCRATCH_ROOT)))
    atexit.register(shutil.rmtree, root, True)
    rt = root / "runtime"
    bk = root / "backup"

    def lay(base, tree):
        base.mkdir(parents=True, exist_ok=True)
        for rel, data in (tree or {}).items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)

    if runtime_exists:
        lay(rt, runtime_files)
    else:
        rt = root / "no-runtime-here"
    if backup_exists:
        lay(bk, backup_files)
    else:
        bk = root / "no-backup-here"

    rep = V.Report()
    V.check_skill_cross_layer(
        None, rep, runtime_skills_dir=rt, backup_dir=bk,
        ignored_override=ignored_override, sync_text_override=skill_dirs_text,
        git_probe=git_probe)
    items = [it for s in rep.sections for it in s["items"]]
    return {
        "fail": [m for lv, m in items if lv == "FAIL"],
        "warn": [m for lv, m in items if lv == "WARN"],
        "info": [m for lv, m in items if lv == "INFO"],
        "ok":   [m for lv, m in items if lv == "PASS"],
        "_root": root,
    }


def tidy(*trees):
    """把若干同构 {rel: bytes} 合并成两层一致内容（clean 注入用）。"""
    merged = {}
    for t in trees:
        merged.update(t)
    return merged


CLEAN_RT = {
    "skill-a/SKILL.md": b"# A\n",
    "skill-a/reference.md": b"ref-a\n",
    "skill-b/SKILL.md": b"# B\n",
}
CLEAN_BK = dict(CLEAN_RT)
CLEAN_IGNORED = set()  # 临时面无 git 概念，全纳入


class TestRealRepoCleanBaseline(unittest.TestCase):
    """真实仓 clean 态：以模块默认层跑一次，钉当前覆盖面读数。"""

    def setUp(self):
        self.rep = V.Report()
        V.check_skill_cross_layer(None, self.rep)
        self.items = [it for s in self.rep.sections for it in s["items"]]
        self.fail = [m for lv, m in self.items if lv == "FAIL"]
        self.ok = [m for lv, m in self.items if lv == "PASS"]
        self.info = [m for lv, m in self.items if lv == "INFO"]

    def test_zero_fail(self):
        self.assertEqual(self.fail, [], f"真实仓 clean 态不应有 FAIL：{self.fail}")

    def test_two_ok_rows(self):
        # D 比对集自洽 ＋ 运行时↔镜像 纳入判据字节全等 ＝ 2 条 [OK]
        self.assertEqual(len(self.ok), 2, self.ok)

    def test_judged_62_no_drift(self):
        joined = "\n".join(self.ok)
        self.assertIn("纳入判据 62 件字节全等", joined)
        self.assertIn("漂移 0／单层缺失 0", joined)

    def test_coverage_boundary_disclosed(self):
        # 覆盖面边界／哈希口径／与检查 8 关系，三条 INFO 须逐条披露（不覆盖面＝披露而非机算）
        joined = "\n".join(self.info)
        self.assertIn("覆盖面边界", joined)
        self.assertIn("不做 eol／编码归一", joined)
        self.assertIn("OBS-2", joined)


class TestDriftAndOneside(unittest.TestCase):
    def test_clean_injection_is_quiet(self):
        r = run(runtime_files=CLEAN_RT, backup_files=CLEAN_BK,
                ignored_override=CLEAN_IGNORED)
        self.assertEqual(r["fail"], [], r["fail"])
        self.assertTrue(any("漂移 0／单层缺失 0" in m for m in r["ok"]), r["ok"])

    def test_byte_drift_fails(self):
        bk = dict(CLEAN_BK)
        bk["skill-a/SKILL.md"] = b"# A changed\n"
        r = run(runtime_files=CLEAN_RT, backup_files=bk, ignored_override=CLEAN_IGNORED)
        self.assertTrue(any("跨层漂移 skill-a/SKILL.md" in m for m in r["fail"]), r["fail"])

    def test_oneside_backup_only_fails(self):
        # C3(a)：镜像独有件（运行时缺）须复红，证「单层缺失」判据非恒真
        rt = dict(CLEAN_RT)
        bk = dict(CLEAN_BK)
        bk["skill-b/extra.md"] = b"only in mirror\n"   # 镜像独有 → 运行时缺
        r = run(runtime_files=rt, backup_files=bk, ignored_override=CLEAN_IGNORED)
        self.assertTrue(any("单层缺失 skill-b/extra.md" in m and "运行时缺" in m
                            for m in r["fail"]), r["fail"])

    def test_oneside_runtime_only_fails(self):
        # C3(b)：运行时独有件（镜像缺＝sync 漏跑）须复红
        rt = dict(CLEAN_RT)
        rt["skill-a/only-rt.md"] = b"not synced yet\n"
        r = run(runtime_files=rt, backup_files=CLEAN_BK, ignored_override=CLEAN_IGNORED)
        self.assertTrue(any("单层缺失 skill-a/only-rt.md" in m and "漏跑" in m
                            for m in r["fail"]), r["fail"])


class TestExclusionFace(unittest.TestCase):
    """排除面＝gitignore 结构判据：被忽略件即便单层缺失也不入判据（C1）。"""

    def test_gitignored_oneside_not_judged(self):
        rt = dict(CLEAN_RT)
        rt["skill-a/sre_regression_report.json"] = b"{\"local\": true}\n"  # 运行时独有但 gitignored
        r = run(runtime_files=rt, backup_files=CLEAN_BK,
                ignored_override={"skill-a/sre_regression_report.json"})
        self.assertEqual(r["fail"], [], r["fail"])
        self.assertTrue(any("纳入判据 3 件" in m for m in r["ok"]), r["ok"])

    def test_control_c1_exclusion_has_teeth(self):
        # 同一文件若从不忽略集里去掉 → 立刻复红，证「排除」这一步非恒真
        rt = dict(CLEAN_RT)
        rt["skill-a/sre_regression_report.json"] = b"{\"local\": true}\n"
        r = run(runtime_files=rt, backup_files=CLEAN_BK, ignored_override=set())
        self.assertTrue(any("单层缺失 skill-a/sre_regression_report.json" in m
                            for m in r["fail"]), r["fail"])


class TestBidirectionalDeclaration(unittest.TestCase):
    def test_missing_mirror_dir_fails(self):
        # C4(a)：SKILL_DIRS 声明 skill-b 但镜像无该目录 → D 漏配（证双向互查「漏配」侧有牙）
        bk = {"skill-a/SKILL.md": b"# A\n", "skill-a/reference.md": b"ref-a\n"}
        r = run(runtime_files=CLEAN_RT, backup_files=bk, ignored_override=CLEAN_IGNORED)
        self.assertTrue(any("D 漏配" in m and "skill-b" in m for m in r["fail"]), r["fail"])

    def test_extra_mirror_dir_fails(self):
        # C4(b)：镜像有但不属 SKILL_DIRS → D 越界（证双向互查「越界」侧有牙）
        bk = dict(CLEAN_BK)
        bk["skill-z/SKILL.md"] = b"# Z\n"   # 镜像有但不属 SKILL_DIRS → D 越界
        r = run(runtime_files=CLEAN_RT, backup_files=bk, ignored_override=CLEAN_IGNORED)
        self.assertTrue(any("D 越界" in m and "skill-z" in m for m in r["fail"]), r["fail"])

    def test_control_c2_shared_dir_not_flagged(self):
        # shared/ 属治理面（检查 6 管辖），本检查显式豁免，不得判越界
        bk = dict(CLEAN_BK)
        bk["shared/change-governance.md"] = b"gov\n"
        r = run(runtime_files=CLEAN_RT, backup_files=bk, ignored_override=CLEAN_IGNORED)
        self.assertFalse(any("越界" in m and "shared" in m for m in r["fail"]), r["fail"])


class TestDegradation(unittest.TestCase):
    def test_runtime_unreachable_warns_not_fails(self):
        r = run(runtime_exists=False, backup_files=CLEAN_BK,
                ignored_override=CLEAN_IGNORED)
        self.assertEqual(r["fail"], [], r["fail"])
        self.assertTrue(any("运行时技能目录不可达" in m for m in r["warn"]), r["warn"])

    def test_backup_missing_fails(self):
        r = run(runtime_files=CLEAN_RT, backup_exists=False)
        self.assertTrue(any("技能仓备份镜像目录不存在" in m for m in r["fail"]), r["fail"])

    def test_empty_skill_dirs_warns(self):
        r = run(runtime_files=CLEAN_RT, backup_files=CLEAN_BK,
                skill_dirs_text="SKILL_DIRS = []")
        self.assertEqual(r["fail"], [], r["fail"])
        self.assertTrue(any("AST 现读 SKILL_DIRS" in m for m in r["warn"]), r["warn"])

    def test_git_unavailable_warns_not_fails(self):
        # ignored_override=None 且 git_probe 返回 None → 排除面无真值源，降级不判红
        real = V.git_toplevel
        V.git_toplevel = lambda cwd: cwd  # 令 relative_to 成立，只测 git_probe 为 None 一支
        try:
            r = run(runtime_files=CLEAN_RT, backup_files=CLEAN_BK,
                    ignored_override=None, git_probe=lambda root, rels: None)
        finally:
            V.git_toplevel = real
        self.assertEqual(r["fail"], [], r["fail"])
        self.assertTrue(any("git 不可达" in m for m in r["warn"]), r["warn"])

    def test_not_in_worktree_warns(self):
        real = V.git_toplevel
        V.git_toplevel = lambda cwd: None
        try:
            r = run(runtime_files=CLEAN_RT, backup_files=CLEAN_BK, ignored_override=None)
        finally:
            V.git_toplevel = real
        self.assertEqual(r["fail"], [], r["fail"])
        self.assertTrue(any("不在任何 git 工作树内" in m for m in r["warn"]), r["warn"])


class TestEmptyJudgedGuard(unittest.TestCase):
    """C5：两层目录都在但判据集为空（内容全被忽略）→ 不得判绿，须 FAIL。"""

    def test_all_ignored_judged_zero_fails(self):
        rt = {"skill-a/SKILL.md": b"# A\n", "skill-b/SKILL.md": b"# B\n"}
        r = run(runtime_files=rt, backup_files=dict(rt),
                ignored_override={"skill-a/SKILL.md", "skill-b/SKILL.md"})
        self.assertFalse(any("漂移 0" in m for m in r["ok"]), r["ok"])
        self.assertTrue(any("纳入判据 0 件" in m for m in r["fail"]), r["fail"])


class TestHelperFunctions(unittest.TestCase):
    def test_walk_layer_files_relative_keys(self):
        root = Path(tempfile.mkdtemp(prefix="walk-", dir=str(SCRATCH_ROOT)))
        atexit.register(shutil.rmtree, root, True)
        (root / "skill-a" / "nested").mkdir(parents=True)
        (root / "skill-a" / "SKILL.md").write_bytes(b"x\n")
        (root / "skill-a" / "nested" / "deep.md").write_bytes(b"y\n")
        (root / "not-a-skill").mkdir()
        (root / "not-a-skill" / "z.md").write_bytes(b"z\n")
        got = V._walk_layer_files(root, ["skill-a"])
        self.assertEqual(sorted(got), ["skill-a/SKILL.md", "skill-a/nested/deep.md"])

    def test_git_ignored_empty_input_is_empty_set(self):
        self.assertEqual(V.git_ignored(Path("."), []), set())


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    unittest.main(verbosity=2)
