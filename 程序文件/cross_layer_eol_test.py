#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cross_layer_eol_test.py — 检查 6 (C)「副本 ↔ HEAD 前像行尾形态」专项测试（CG-20260919-001）

口径沿 pending_ledger_test.py（检查 7 专项）：
  - 负向注入以合成字节／一次性临时 git 仓直调，不落盘、不改任何治理件
  - 每一类失效形态都必须能被注入并复红（「修净后的守卫须仍能失败」），否则该断言属恒真＝空跑
  - 另含对本仓真实治理件副本的 clean 态断言（(C) 只比形态，不随内容编辑转红）

覆盖：
  纯函数层  eol_form 五类判定（无行尾分隔符／纯 LF／纯 CRLF／仅 CR 无 LF／混合行尾）
            ＋「真实内容编辑不误报」「无行尾符时 LF/CRLF 物理不可分」的已知边界
  取数层    HEAD 前像实读、HEAD 无对象、git 不可达三态互不混淆
  集成层    临时 git 仓复现 PL-020 事故形态：各副本字节全等（(A)(B) 必绿）而集体偏离 HEAD
            → (C) 独立报红；clean 仓零 FAIL；单副本漂移只报该副本；不可达降级为 WARN 不静默
  真实面    本仓 15 个 git 可见副本 clean 态零 FAIL；判据用真实 HEAD blob 注入体仍能失败

临时仓落点：`D:/Qoder-Files/_tmp-scripts/`（工作区外的临时面）——落本仓内会成嵌套 git 仓，
落 C 盘违反临时文件纪律；清理须先解 .git 对象的只读位，否则 Windows 下 rmtree 报 WinError 5。

用法：python -B 程序文件/cross_layer_eol_test.py
依赖：Python 3.8+（仅标准库）＋ git 可执行（不可达时集成组按降级态断言，不回判 FAIL）
"""

import atexit
import os
import shutil
import subprocess
import stat
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_governance as V  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parent
SCRATCH_ROOT = Path("D:/Qoder-Files/_tmp-scripts/cross_layer_eol_scratch")
SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)

LF_TEXT = b"line one\nline two\nline three\n"
CRLF_TEXT = LF_TEXT.replace(b"\n", b"\r\n")


def rmtree_force(target: Path):
    """git 把 object 文件写成只读，Windows 下直接 rmtree 会 WinError 5。"""
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


def run_report(files):
    rep = V.Report()
    rep.section("test")
    checked = V.check_head_eol_form(files, rep)
    items = rep.sections[0]["items"]
    return (checked,
            [m for lv, m in items if lv == "FAIL"],
            [m for lv, m in items if lv == "WARN"],
            [m for lv, m in items if lv == "INFO"])


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd),
                          capture_output=True, check=True)


class EolFormPure(unittest.TestCase):
    """纯函数五类判定：不数内容、不归一，故与正文改动解耦。"""

    def test_pure_lf(self):
        self.assertEqual(V.eol_form(LF_TEXT), "纯 LF")

    def test_pure_crlf(self):
        self.assertEqual(V.eol_form(CRLF_TEXT), "纯 CRLF")

    def test_lone_cr(self):
        self.assertEqual(V.eol_form(b"a\rb\rc"), "仅 CR 无 LF")

    def test_mixed_crlf_and_lf(self):
        self.assertEqual(V.eol_form(b"a\r\nb\nc\r\n"), "混合行尾")

    def test_mixed_cr_inside(self):
        self.assertEqual(V.eol_form(b"a\r\nb\rc\n"), "混合行尾")

    def test_missing_final_newline_is_distinct(self):
        self.assertEqual(V.eol_form(b"a\nb\nc"), "混合行尾")

    def test_one_crlf_line_in_lf_file_is_caught(self):
        """事故的最小形态：一行被写成 CRLF，其余不变。"""
        mixed = LF_TEXT.replace(b"line two\n", b"line two\r\n")
        self.assertEqual(V.eol_form(mixed), "混合行尾")
        self.assertNotEqual(V.eol_form(mixed), V.eol_form(LF_TEXT))

    def test_whole_file_lf_to_crlf_is_caught(self):
        self.assertNotEqual(V.eol_form(CRLF_TEXT), V.eol_form(LF_TEXT))

    def test_real_content_edit_does_not_change_form(self):
        """行尾订正之外的日常编辑（加行、改正文）不得报红——否则判据与编辑流互斥。"""
        self.assertEqual(V.eol_form(LF_TEXT + b"line four\n"), V.eol_form(LF_TEXT))

    def test_no_terminator_is_its_own_form(self):
        """空文件与单行无行尾符同归「无行尾分隔符」：此时 LF/CRLF 物理不可分，判据不假装能分。"""
        for data in (b"", b"only line", b"only line with CR\r inside is another case".replace(b"\r", b"")):
            self.assertEqual(V.eol_form(data), "无行尾分隔符")
        self.assertNotEqual(V.eol_form(b"only line"), V.eol_form(b"only line\n"))

    def test_forms_are_declared_enumeration(self):
        seen = {V.eol_form(x) for x in
                (b"", b"a", b"a\n", b"a\r\n", b"a\rb", b"a\r\nb\nc", b"a\nb")}
        self.assertTrue(seen <= set(V.EOL_FORMS), f"产出未声明形态：{seen - set(V.EOL_FORMS)}")
        self.assertEqual(
            {"无行尾分隔符", "纯 LF", "纯 CRLF", "仅 CR 无 LF", "混合行尾"}, set(V.EOL_FORMS))


class HeadBlobReader(unittest.TestCase):
    def setUp(self):
        self._real_run = V.subprocess.run

    def tearDown(self):
        V.subprocess.run = self._real_run

    def test_reads_real_head_blob(self):
        rel = "_专题_技能合集策划/glossary.md"
        blob, status = V.git_head_blob(REPO_ROOT, rel)
        self.assertEqual(status, "ok")
        self.assertEqual(V.eol_form(blob), "纯 LF")

    def test_missing_path_reports_no_head_not_crash(self):
        blob, status = V.git_head_blob(REPO_ROOT, "_专题_技能合集策划/不存在的文件.md")
        self.assertIsNone(blob)
        self.assertEqual(status, "no_head")

    def test_git_unavailable_is_not_no_head(self):
        """HEAD 有对象而取回失败（git 不可达）须落第三态，不得混入 no_head 后静默不判。"""
        def fake(*args, **kwargs):
            raise OSError("git not installed")

        V.subprocess.run = fake
        blob, status = V.git_head_blob(REPO_ROOT, "_专题_技能合集策划/glossary.md")
        self.assertIsNone(blob)
        self.assertEqual(status, "git_unavailable")

    def test_real_repo_resolves_toplevel(self):
        self.assertEqual(V.git_toplevel(V.DEFAULT_BASE).resolve(), REPO_ROOT.resolve())


class ScratchRepoIntegration(unittest.TestCase):
    """临时 git 仓：证明「跨层同漂移」这一 (A)(B) 盲区由 (C) 独立抓住。"""

    def setUp(self):
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="repo-", dir=str(SCRATCH_ROOT)))
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "test@local")
        git(self.root, "config", "user.name", "test")
        self.l1 = self.root / "治理"
        self.repo = self.root / "镜像" / "shared"
        self.l1.mkdir(parents=True)
        self.repo.mkdir(parents=True)
        self.f = self.l1 / "a.md"
        self.g = self.repo / "a.md"
        self.files = {"a.md@L1": self.f, "a.md@REPO_SHARED": self.g}
        atexit.register(rmtree_force, self.root)

    def tearDown(self):
        rmtree_force(self.root)

    def commit_head(self, data: bytes):
        self.f.write_bytes(data)
        self.g.write_bytes(data)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "base")

    def test_clean_repo_is_quiet(self):
        self.commit_head(LF_TEXT)
        checked, fails, warns, _ = run_report(self.files)
        self.assertEqual(checked, 2)
        self.assertEqual((fails, warns), ([], []))

    def test_same_drift_across_layers_still_fails(self):
        """核心用例（PL-020 事故形态）：两层副本字节全等 → (A)(B) 结构上必绿，(C) 仍报红。"""
        self.commit_head(LF_TEXT)
        self.f.write_bytes(CRLF_TEXT)
        self.g.write_bytes(CRLF_TEXT)
        self.assertEqual(V.sha256_file(self.f), V.sha256_file(self.g))   # 互等成立
        checked, fails, warns, _ = run_report(self.files)
        self.assertEqual(checked, 2)                                    # 不判红≠不计项
        self.assertEqual(len(fails), 2)
        for m in fails:
            self.assertIn("纯 LF", m)                                   # HEAD 基准出现在报红里
            self.assertIn("纯 CRLF", m)                                 # 工作区漂移态
        self.assertEqual(warns, [])

    def test_partial_drift_reports_only_the_drifted_copy(self):
        self.commit_head(LF_TEXT)
        self.g.write_bytes(CRLF_TEXT)
        checked, fails, _, _ = run_report(self.files)
        self.assertEqual(checked, 2)
        self.assertEqual(len(fails), 1)
        self.assertIn("a.md@REPO_SHARED", fails[0])

    def test_new_uncommitted_copy_is_disclosed_not_judged(self):
        git(self.root, "commit", "-q", "--allow-empty", "-m", "empty head")
        self.f.write_bytes(CRLF_TEXT)
        self.g.write_bytes(CRLF_TEXT)
        checked, fails, warns, infos = run_report(self.files)
        self.assertEqual((checked, fails, warns), (0, [], []))
        self.assertTrue(any("HEAD 无该路径对象" in m for m in infos))

    def test_no_head_covers_untracked_on_disk_variant(self):
        """git 对「磁盘有、HEAD 无」报 `exists on disk, but not in 'HEAD'`，
        对「从未入库」报 `does not exist in 'HEAD'`——两式都属新增未提交件，须同归 no_head。"""
        git(self.root, "commit", "-q", "--allow-empty", "-m", "empty head")
        for name, blob_status in (("brand-new.md", "no_head"),        # 磁盘也无
                                  ("on-disk.md", "no_head")):         # 磁盘有：先落文件再取数
            (self.root / name).write_bytes(b"x\ny\n")
            _blob, status = V.git_head_blob(self.root, name)
            self.assertEqual(status, blob_status, name)

    def test_repo_without_any_commit_is_git_unavailable_not_no_head(self):
        """无提交的仓（HEAD 不可解析）报 `invalid object name 'HEAD'`，不得落 no_head 静默。"""
        root = Path(tempfile.mkdtemp(prefix="nocommit-", dir=str(SCRATCH_ROOT)))
        self.addCleanup(rmtree_force, root)
        git(root, "init", "-q")
        (root / "a.md").write_bytes(b"x\n")
        _blob, status = V.git_head_blob(root, "a.md")
        self.assertEqual(status, "git_unavailable")

    def test_unreachable_dir_degrades_to_warn_not_silent(self):
        """无 git 面 → 聚合一条 WARN 并列出被跳过项，不得静默当通过。

        不依赖「找一个不在任何仓内的目录」：本机 D:\\Qoder-Files 本身是工作树，
        临时目录的仓外性随机器拓扑翻转，故直接置 toplevel 取数为 None（同函数同分支）。
        """
        p = self.l1 / "b.md"
        p.write_bytes(LF_TEXT)
        real = V.git_toplevel
        V.git_toplevel = lambda _cwd: None
        try:
            checked, fails, warns, _ = run_report({"b.md@L1": p})
        finally:
            V.git_toplevel = real
        self.assertEqual((checked, fails), (0, []))
        self.assertEqual(len(warns), 1)
        self.assertIn("无法取得 HEAD 前像", warns[0])
        self.assertIn("b.md@L1", warns[0])


class RealRepoCleanState(unittest.TestCase):
    """真实面：本仓声明表内 git 可见副本的 clean 态断言。"""

    def declared_git_visible(self):
        layer_dir = {"L1": V.DEFAULT_BASE, "REPO_ROOT": V.REPO_BACKUP_DIR,
                     "REPO_SHARED": V.REPO_BACKUP_SHARED_DIR}
        out = {}
        for name, layers, _ in V.CROSS_LAYER_SET:
            for layer in ("L1", "REPO_ROOT", "REPO_SHARED"):
                if layer in layers:
                    out[f"{name}@{layer}"] = layer_dir[layer] / name
        return out

    def test_shape_matches_declaration(self):
        """7 件声明表 → 6 件有 L1 ＋ 7 件在 REPO_SHARED ＋ 2 件在 REPO_ROOT ＝ 15。"""
        self.assertEqual(len(self.declared_git_visible()), 15)

    def test_real_repo_head_eol_form_is_clean(self):
        files = self.declared_git_visible()
        missing = [str(p) for p in files.values() if not p.is_file()]
        self.assertEqual(missing, [], "声明表副本缺失会让 (C) 静默少判")
        checked, fails, warns, _ = run_report(files)
        self.assertEqual(checked, 15)
        self.assertEqual((fails, warns), ([], []))

    def test_judge_still_fails_on_real_head_blob(self):
        """防恒真：以真实 HEAD 前像为注入体，同法取数、同字面比对。"""
        rel = "_专题_技能合集策划/change-governance.md"
        head, status = V.git_head_blob(REPO_ROOT, rel)
        self.assertEqual(status, "ok")
        wt = Path(REPO_ROOT / rel).read_bytes()
        self.assertEqual(V.eol_form(head), V.eol_form(wt))
        self.assertNotEqual(V.eol_form(head.replace(b"\n", b"\r\n")), V.eol_form(head))


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    unittest.main(verbosity=2)
