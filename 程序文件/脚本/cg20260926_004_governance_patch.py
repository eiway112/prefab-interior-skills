# -*- coding: utf-8 -*-
"""CG-20260926-004 治理登记面写入（冻结基准 H-1 检测力诊断，C 级取证批）：头部快照轮换＋§九 新行。

形制沿 cg20260926_002／_003 两个同批同构件（每批自留一份可复跑凭据，故不互相导入：
那两份的 sha256 已被各自执行记录引用，抽公共件会使被引用件字节改变即与记录不符）。
安全口径＝唯一锚命中数＝1 再写；写后自检（新行存在／旧行降级且唯一／行列数＝表头现读／
收尾竖线在位／CR 计数不变／纯 LF）；复跑幂等退出。仓根由脚本位置派生，不硬编码盘符。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / '程序文件'))
import validate_governance as vg  # noqa: E402

CG = REPO / '_专题_技能合集策划' / 'change-governance.md'
assert CG.exists(), f'治理面未找到：{CG}'
PREV, HERE = 'CG-20260926-003', 'CG-20260926-004'
OLD_HEAD_ANCHOR = f'> **最后更新**：2026-09-26，{PREV}（'
DEMOTED_ANCHOR = f'> **此前更新（历史快照）**：2026-09-26，{PREV}（'

NEW_HEAD = (
    '> **最后更新**：2026-09-26，CG-20260926-004（**C 级取证批**，冻结机制修订线第一步，承接 PL-049）：'
    '以三值复算检验「H-1 恒为同值、对『被测对象已变』失去检测力」这一原述真伪并量化其后果——'
    '① 按基准 §二 2A 取法列复算得 `413ab919…`，与登记值**逐字 MATCH**、缺 blob 0 件（配方正确、可跨会话复现）；'
    '② 同键集取今日运行时字节得 `86ebac9e…`≠登记值，**36/71 件已变**而硬项不动；'
    '③ 今日按字面重跑（现版脚本 72 键 × 冻结基 blob）仍得登记值 `413ab919…`＝**硬项恒真实测成立**。'
    '另检出 PL-049 未载的第二失效模式：冻结基后进入生效路径的 `shared/data-classification.md` 在冻结基无 blob，'
    '复算者只能「跳过＝静默吞掉真实被测件」或「不跳过＝配方不可原样复算」，两支皆缺陷；'
    '并查明 H-1 键集取当次运行时在场文件、字节取仓内镜像冻结 blob＝跨时点跨层混取，'
    '且取法列未指明**脚本版本**（现版 8 个 SHARED_FILES→72 键、冻结版 7 个→71 键，取错即产假红）。'
    '36 件差异逐件 commit 归因**未归因 0 件**，故「偏移可全额归因」不必以放弃检测力换取。'
    'v4 最小修订案 R1—R5 已成形为**提案**（H-1 拆 H-1a／H-1b、两枚同源取数、按行为面／登记面归类判据、'
    '脚本版本入取物基准、排除面改结构判据），**基准件本体零改**——其落地属 B 级改判据、须发起人定级并留前版。'
    '§九 CG 行 147→**148**；台账 **82 行不变**、PL-049 仍待处置（本批不闭合）。'
    '历史快照保留如下，终态以本批执行记录为准。\n>\n'
)

CG_ROW = (
    f'| {HERE} | 2026-09-26 | '
    'C 级（定级依据＝§一 C 级「文档结构优化、措辞改善、格式统一等不影响功能和准确性的变更」——'
    '写面仅本文件登记面与 `记录/` 取证件，**零改基准件正文、零改判据与硬项口径、零动技能件与台账状态**；'
    '基准件 v4 的实质修订属 B 级（改评估判据即改行为比较口径），须走 §二 四步并留前版，见'
    '`_专题_技能合集策划/行为与专业证据层冻结基准_v3.md` §一 第 2 条，本批不落） | '
    '① 复算＝三值对照（全部脚本现算、无手抄）：值 A 按 2A 取法列复算 `413ab919b5f406e5f4d90d10a36a08222c22746dc50b1eec49fa8bb4ab5f386d` '
    '与登记值**逐字 MATCH**、缺 blob 0 件；值 C 同键集×今日运行时字节 `86ebac9ee7f62c5716e7fd2bd2d113f5c2e4070796154bd4325b5cb912c8c23e`'
    '（≠登记值，**36/71 件内容有差异**）；值 D 今日按字面重跑（现版脚本 72 键×冻结基 blob、None 者跳过）**仍等于登记值** '
    '⇒ PL-049 原述「H-1 恒为同值、对『被测对象已变』失去检测力」由定性升为实测。'
    '② 新检出（PL-049 未载）＝`shared/data-classification.md`（CG-20260923-001 纳入 SHARED_FILES）在冻结基无 blob，'
    '复算二难：跳过即静默吞掉一个真实进入生效路径的被测件（值 D 恰因跳过而与登记值相等）、不跳过则配方在冻结基后不可原样复算。'
    '③ 口径缺陷＝H-1 键集取当次运行时在场文件、字节取 `git cat-file blob 08069b0:技能仓备份/…`，'
    '二者仅在冻结那刻全等；且取法列「件集直接调用脚本自身取数」未指明脚本版本（现版 72 键／冻结版 71 键），取错版本即产假红。'
    '④ 归因＝36 件差异逐件对 `08069b0..HEAD` 的镜像改动做 commit 归因，**未归因件数 0**（每件 1—21 次），'
    '证明恢复检测力与「不把纯登记变化误当技术行为变化」可并存（§五 该行验收标准），无需以恒真换安宁。'
    '⑤ 提案 R1—R5 成形但**不落判据**＝H-1 拆 H-1a（冻结时点，原样保留）／H-1b（实跑被测对象，键集与字节同源现读）、'
    '不等时按行为面／登记面归类判定（行为面非空触发另批升版重新冻结、登记面非空只归因 CG）、'
    '「脚本版本亦属取物基准」入取法列、机器本地件排除改结构判据（沿检查 9 `git check-ignore` 先例）。'
    '不做的两件＝不重排 §三 33 题与 §四 评分线（基准 §一 第 1 条禁止执行中修改）、不合并软项 S-1／S-2 | '
    '影响范围＝`记录/2026-09-26_CG-20260926-004_冻结基准H1检测力诊断执行记录.md`（新建）＋本文件登记面；'
    '该记录件与 `成果/` 同不在检查 10 扫描面 57 键内（键集现读不含 `记录/`），故本批不触发新键登记，'
    '仅治理镜像面因本文件指纹再漂须按列判 N 重登。PL-049 状态**不变**（本批仅诊断与提案，不构成闭合凭据）。'
    '零改面＝`行为与专业证据层冻结基准_v1/v2/v3.md`（判据本体）、15 技能目录全部内容件、契约／红线／索引／分类判据本体、'
    '校验器与十二门禁判据、§九 历史 CG 行、§11.2 台账全部 82 行、冻结基准、`素材/` | '
    '已登记（发起人 2026-09-26「开。请根据优先级启动，我需要开新线」；本线取证半面不需外部输入故先行启动，'
    'v4 修订属 B 级改判据、待发起人定级后另批执行）；'
    '§九 CG 行 147→**148**、台账 **82 行不变**、状态分布零改；'
    '写面与验收读数以 记录/2026-09-26_CG-20260926-004_冻结基准H1检测力诊断执行记录.md 为准；'
    'commit 随本批（T1），push 不随批（T2，须发起人当轮明文整句） |\n'
)


def main():
    raw = CG.read_bytes()
    text = raw.decode('utf-8')
    lf_before, cr_before = text.count('\n'), text.count('\r')
    if cr_before:
        print('本文件含 CR，与既有纯 LF 形态不符，停')
        return 1
    if f'| {HERE} | ' in text:
        print(f'已登记（§九 {HERE} 行存在），幂等退出')
        return 0
    if text.count(OLD_HEAD_ANCHOR) != 1:
        print(f'头部锚命中 {text.count(OLD_HEAD_ANCHOR)}，非唯一，停')
        return 1
    out = text.replace(OLD_HEAD_ANCHOR, DEMOTED_ANCHOR, 1)
    out = out.replace(DEMOTED_ANCHOR, NEW_HEAD + DEMOTED_ANCHOR, 1)

    lines = out.split('\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(f'| {PREV} | ')]
    if len(idx) != 1:
        print(f'§九 {PREV} 行命中 {len(idx)}，停')
        return 1
    header = next((h for h in lines[:idx[0]] if h.startswith('| 变更编号 |')), None)
    if header is None:
        print('§九 表头未现读找到，停（不猜列数）')
        return 1
    ncol = len(vg.md_cells(header))
    body = CG_ROW.rstrip('\n')
    if len(vg.md_cells(body)) != ncol:
        print(f'本批行列数 {len(vg.md_cells(body))} ≠ 表头 {ncol}，停')
        return 1
    lines.insert(idx[0] + 1, body)
    out = '\n'.join(lines)

    CG.write_bytes(out.encode('utf-8'))
    check = CG.read_bytes().decode('utf-8')
    now = [l for l in check.split('\n') if l.startswith(f'| {HERE} | ')]
    print('写入完成：')
    print(f'  头部新行存在＝{f"> **最后更新**：2026-09-26，{HERE}（" in check}')
    print(f'  旧行已降级且唯一＝{check.count(DEMOTED_ANCHOR) == 1}')
    print(f'  §九 新行唯一＝{len(now) == 1}')
    print(f'  §九 新行列数＝{len(vg.md_cells(now[0]))}（表头 {ncol}）｜收尾竖线在位＝{now[0].rstrip().endswith("|")}')
    print(f'  行数 {lf_before} → {check.count(chr(10))}（预期 +3＝头部两物理行＋§九 一行）')
    print(f'  CR 计数 {cr_before} → {check.count(chr(13))}（预期不变 0）')
    print(f'  字节 {len(raw)} → {len(out.encode("utf-8"))}')
    return 0


sys.exit(main())
