# -*- coding: utf-8 -*-
"""CG-20260926-005 批登记脚本：冻结基准 v4 §二 2A 的 H-1a／H-1b 可复跑凭据。

把 CG-20260926-004 记录 §七 披露的「未固化为仓内脚本的 stdin 内联复算」落为仓内凭据，
并按 v4 §二 2A-补 的五步规程出差异归类表。`--selftest` 跑五项负向注入，证本配方能失败
（恒真配方即空跑，不作凭据）。

用法：
  python -B 程序文件/脚本/cg20260926_005_h1_recompute.py            # 复算＋比对＋归类
  python -B 程序文件/脚本/cg20260926_005_h1_recompute.py --selftest # 负向注入自证
退出码：0＝复算命中登记值且归类完备；1＝任一判据不成立。
"""
import hashlib
import io
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s.encoding and _s.encoding.lower() != "utf-8":
        wrapped = io.TextIOWrapper(_s.buffer, encoding="utf-8")
        if _s is sys.stdout:
            sys.stdout = wrapped
        else:
            sys.stderr = wrapped

ROOT = Path(__file__).resolve().parents[2]
RT = Path.home() / ".qoder" / "skills"
V4 = ROOT / "_专题_技能合集策划" / "行为与专业证据层冻结基准_v4.md"
FROZEN = "36dee02"
V3_BASE = "08069b0"
V3_H1 = "413ab919b5f406e5f4d90d10a36a08222c22746dc50b1eec49fa8bb4ab5f386d"
MACHINE_LOCAL_BY_NAME = "prefab-standards-reviewer/sre_regression_report.json"

def gov_table_from_v4():
    """归类基线表**从 v4 §二 2A-补 现读**，不在脚本里手抄——本仓反复登记的「手抄副本漂移」失效族
    （条文存在≠机制生效）正是这么来的：v4 表改了而脚本没改，脚本仍按旧档判即产假绿。
    解析不到即抛错停批，不静默退回内置默认。"""
    t = V4.read_text(encoding="utf-8")
    try:
        i = t.index("**冻结时点归类基线表")
        seg = t[i:t.index("### 2B", i)]
    except ValueError as e:
        raise RuntimeError(f"v4 归类基线表节锚取不到（节名或 §2B 标题改了？）：{e}")
    gov, skill_band = {}, None
    for line in seg.split("\n"):
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] == "层":
            continue
        layer, units, band = cells[0], cells[1], cells[2].strip("*").strip()
        if "技能目录" in layer:
            skill_band = band
            continue
        prefix = "shared/" if "shared" in layer else ""
        for fn in re.findall(r"`([^`]+\.md)`", units):
            gov[prefix + fn] = band
    if not gov or skill_band != "行为面":
        raise RuntimeError(f"v4 基线表解析结果不完整：gov={len(gov)} 件，技能目录档＝{skill_band}")
    return gov, skill_band


GOV_CLASS, SKILL_BAND = gov_table_from_v4()

sha = lambda b: hashlib.sha256(b).hexdigest()


def git(*a, binary=False, inp=None):
    return subprocess.run(["git", *a], input=inp, capture_output=True, cwd=ROOT,
                          text=not binary, encoding=None if binary else "utf-8")


@lru_cache(maxsize=None)
def _ns(commit):
    """按 v4 §二 2A H-1a 行：脚本版本亦属取物基准，取该 commit 的 blob 后内存 exec，不落临时件。"""
    r = git("cat-file", "blob", f"{commit}:程序文件/sync_skill_backup.py")
    if r.returncode != 0:
        raise RuntimeError(f"取不到 {commit} 的 sync_skill_backup.py blob")
    ns = {"__name__": "ssb_frozen", "__file__": str(ROOT / "程序文件" / "sync_skill_backup.py")}
    exec(compile(r.stdout, f"<blob {commit}:sync_skill_backup.py>", "exec"), ns)
    return ns


@lru_cache(maxsize=None)
def _excluded(keys):
    """一次 `git check-ignore --stdin -z` 取全排除面（逐件起子进程在 72 件规模下慢到不可用）。
    -z 令输出以 NUL 分隔且不转义非 ASCII，故中文前缀可直接回切。"""
    paths = "\0".join(f"技能仓备份/{k}" for k in keys) + "\0"
    r = git("check-ignore", "--stdin", "-z", inp=paths)
    out = set()
    for p in r.stdout.split("\0"):
        p = p.strip().replace("\\", "/")
        if p.startswith("技能仓备份/"):
            out.add(p.split("/", 1)[1])
    return frozenset(out)


def excluded_structural(keys):
    return set(_excluded(tuple(sorted(keys))))


@lru_cache(maxsize=None)
def blob(commit, key):
    r = git("cat-file", "blob", f"{commit}:技能仓备份/{key}", binary=True)
    return r.stdout if r.returncode == 0 else None


@lru_cache(maxsize=None)
def rt_bytes(key):
    p = RT / key
    return p.read_bytes() if p.is_file() else None


def aggregate(pairs):
    return sha("\n".join(f"{k}:{sha(v)}" for k, v in sorted(pairs)).encode("utf-8"))


@lru_cache(maxsize=None)
def scope(commit):
    ns = _ns(commit)
    return tuple(sorted(ns["collect_scope"]())), frozenset(ns["SKILL_DIRS"])


def h1a(commit, *, on_missing="raise", exclude=None, script_commit=None):
    """H-1a：冻结版脚本键集 ∖ 结构判据排除件，字节取该 commit 的镜像 blob。
    on_missing＝raise（v4 口径）／skip（v3 未禁的漏检支，仅供自证）。"""
    sc = script_commit or commit
    keys, _ = scope(sc)
    ex = excluded_structural(keys) if exclude is None else set(exclude)
    out = []
    for k in keys:
        if k in ex:
            continue
        b = blob(commit, k)
        if b is None:
            if on_missing == "raise":
                raise MissingBlob(k, commit)
            continue
        out.append((k, b))
    return aggregate(out), [k for k, _ in out]


def h1b(*, from_blob_commit=None):
    """H-1b：键集与字节同源同时点（当次工作树脚本 + 运行时层现读）。
    from_blob_commit 仅供自证——把字节侧换回 blob 即退化为 H-1a 同义反复。"""
    keys, _ = scope(FROZEN)
    ex = excluded_structural(keys)
    out = []
    for k in keys:
        if k in ex:
            continue
        if from_blob_commit:
            b = blob(from_blob_commit, k)
            if b is None:
                raise MissingBlob(k, from_blob_commit)
        else:
            b = rt_bytes(k)
            if b is None:
                raise MissingBlob(k, "runtime")
        out.append((k, b))
    return aggregate(out), [k for k, _ in out]


class MissingBlob(Exception):
    pass


def classify(key, skill_dirs, gov=GOV_CLASS):
    """v4 §二 2A-补 第 2／3／4 步：技能目录机械判据；治理层查基线表；未列件即停。"""
    head = key.split("/")[0]
    if head in skill_dirs:
        return "行为面"
    if key in gov:
        return gov[key]
    raise UnlistedUnit(key)


class UnlistedUnit(Exception):
    pass


def attribution(key, base):
    r = git("log", "--format=%h %s", f"{base}..HEAD", "--", f"技能仓备份/{key}")
    return [l for l in r.stdout.splitlines() if l.strip()]


def diff_table(base_a, base_b):
    """三态分层：a 侧＝blob(base_a)（H-1a 侧），b 侧＝运行时现读（H-1b 侧）。
    base_b 只决定 b 侧键集取自哪个脚本版本（R4：脚本版本属取物基准）。"""
    keys_a, sdirs = scope(base_a)
    keys_b, _ = scope(base_b)
    A = {k for k in keys_a if k not in excluded_structural(keys_a)}
    B = {k for k in keys_b if k not in excluded_structural(keys_b)}
    rows = []
    for k in sorted(A | B):
        if k not in A:
            rows.append((k, "新增件", classify(k, sdirs)))
            continue
        if k not in B:
            rows.append((k, "撤件", classify(k, sdirs)))
            continue
        ba = blob(base_a, k)
        bb = rt_bytes(k)
        if ba is None:
            rows.append((k, "取物缺失", classify(k, sdirs)))
        elif bb is None:
            rows.append((k, "运行时缺件", classify(k, sdirs)))
        else:
            rows.append((k, "字节漂移" if ba != bb else "全等", classify(k, sdirs)))
    return rows


def registered_value():
    m = re.search(r"^\| \*\*H-1a [^\n]*?\| `([0-9a-f]{64})`", V4.read_text(encoding="utf-8"), re.M)
    if not m:
        raise RuntimeError("v4 §二 2A 的 H-1a 登记值取不到（登记面行形制变了？）")
    return m.group(1)


# ── 负向注入自证 ──────────────────────────────────────────────
def selftest():
    fails = []

    def check(name, ok, detail):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}：{detail}")
        if not ok:
            fails.append(name)

    print("负向注入自证（证 v4 配方能失败，非恒真）")

    # N1 脚本版本错取即产假红（R4）
    true_val, _ = h1a(FROZEN)
    wrong, _ = h1a(FROZEN, script_commit=V3_BASE)
    check("N1 脚本版本属取物基准", wrong != true_val,
          f"冻结版脚本→{true_val[:12]}…，错取 {V3_BASE} 版脚本→{wrong[:12]}…，两值不等即本条有牙")

    # N2 键集与字节跨版本混取：v4 口径必中断；跳过支复现漏检（E3）
    try:
        h1a(V3_BASE, script_commit=FROZEN, on_missing="raise")
        check("N2a v4 禁跳过", False, "现版键集×旧基 blob 走 raise 支未中断＝禁令无牙")
    except MissingBlob as e:
        check("N2a v4 禁跳过", "data-classification" in str(e), f"raise 支如实中断于「{e.args[0]}」")
    skip_val, skip_keys = h1a(V3_BASE, script_commit=FROZEN, on_missing="skip")
    check("N2b 跳过支＝漏检", skip_val == V3_H1 and len(skip_keys) == 71,
          f"同参数改跳过：72 候选件吞掉 1 件后以 {len(skip_keys)} 件聚合得 {skip_val[:12]}… "
          f"＝与 v3 登记值逐字相等，被吞件在读数上不可见")

    # N3 H-1b 字节侧若取 blob 即退化为 H-1a 同义反复；取运行时才恢复检测力（E2）
    same, _ = h1b(from_blob_commit=FROZEN)
    check("N3a 取 blob 即失检测力", same == true_val,
          f"H-1b 字节侧改回 blob（同基线）即与 H-1a 恒等＝{same[:12]}…，同义反复")
    rows = diff_table(V3_BASE, FROZEN)
    drift = [r for r in rows if r[1] == "字节漂移"]
    new = [r for r in rows if r[1] == "新增件"]
    check("N3b 取运行时恢复检测力", len(drift) == 36 and len(new) == 1,
          f"同基线取运行时现字节：漂移 {len(drift)} 件／新增 {len(new)} 件（撤件 0）")

    # N4 排除面：结构判据与文件名单件集等价；撤掉排除即产他值
    keys, _ = scope(FROZEN)
    check("N4a 排除面集等价", excluded_structural(keys) == {MACHINE_LOCAL_BY_NAME},
          f"git check-ignore 命中 {sorted(excluded_structural(keys))}，与 v3 文件名硬列同集")
    over = excluded_structural(keys) | {"shared/glossary.md"}
    over_val, over_keys = h1a(FROZEN, exclude=over)
    check("N4b 排除面有牙", over_val != true_val and len(over_keys) == 71,
          f"排除面多吞 1 件即得 {over_val[:12]}… ≠ 登记值 {true_val[:12]}…（{len(over_keys)} 件）；"
          f"反向漏排则该机器本地件在镜像无 blob、复算直接中断，非静默降值")

    # N5 归类完备性：基线表少一行即须停批（第 4 步双向互查）
    try:
        classify("shared/glossary.md", set(),
                 gov={k: v for k, v in GOV_CLASS.items() if k != "shared/glossary.md"})
        check("N5 完备性有牙", False, "基线表删件后未报未列件＝第 4 步无牙")
    except UnlistedUnit as e:
        check("N5 完备性有牙", True, f"从基线表删 `shared/glossary.md` 即报未列件：{e}")

    # N6 登记面判据不得用「命中数 > 0」（本批实测反例）
    hits = ref_hits("change-governance.md")
    check("N6 命中数判据被证伪", len(hits) > 0 and GOV_CLASS["shared/change-governance.md"] == "登记面",
          f"change-governance.md 命中 {len(hits)} 处仍落登记面（命中即行为面即误判）")

    print(f"\n自证读数：{'全部通过' if not fails else '失败项=' + ','.join(fails)}")
    return 1 if fails else 0


def ref_hits(filename):
    _, sdirs = scope(FROZEN)
    out = []
    for d in sorted(sdirs):
        p = RT / d
        if not p.is_dir():
            continue
        for f in sorted(p.rglob("*")):
            if f.suffix not in (".md", ".py") or not f.is_file():
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if filename in line:
                    out.append((f.relative_to(RT).as_posix(), i, line.strip()))
    return out


def main():
    if "--selftest" in sys.argv:
        return selftest()
    reg = registered_value()
    val, keys = h1a(FROZEN)
    bval, bkeys = h1b()
    print(f"H-1a（基线 {FROZEN}，{len(keys)} 件）＝{val}")
    print(f"v4 §二 2A 登记值            ＝{reg}")
    print(f"H-1b（运行时现读，{len(bkeys)} 件）＝{bval}")
    print(f"登记值相符＝{val == reg}｜H-1a==H-1b＝{val == bval}")
    rows = diff_table(FROZEN, FROZEN)
    st = {}
    for _, kind, band in rows:
        st[(kind, band)] = st.get((kind, band), 0) + 1
    print("\n差异归类（v4 §二 2A-补 三态×两档）")
    for (kind, band), n in sorted(st.items()):
        print(f"  {kind:6s} {band:4s} {n} 件")
    unattr = [(k, kind) for k, kind, band in diff_table(V3_BASE, FROZEN)
              if kind in ("字节漂移", "新增件", "撤件") and not attribution(k, V3_BASE)]
    print(f"\n以 {V3_BASE} 为基的漂移件归因：未归因 {len(unattr)} 件 {unattr[:3]}")
    ok = val == reg and not unattr
    print(f"\n总判：{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
