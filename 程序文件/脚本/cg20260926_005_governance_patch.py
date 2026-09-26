# -*- coding: utf-8 -*-
"""CG-20260926-005 治理登记面写入（冻结基准 v4 落地，B 级）：头部快照轮换＋§九 新行＋§11.2 台账 PL-049 闭合。

形制沿 cg20260926_004_governance_patch.py（每批自留一份可复跑凭据，不互相导入）。
安全口径＝唯一锚命中数＝1 再写；写后自检（新行存在／旧行降级且唯一／§九 行列数＝表头现读／
台账行列数不变且状态列转档／CR 计数不变／纯 LF）；复跑幂等退出。仓根由脚本位置派生，不硬编码盘符。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / '程序文件'))
import validate_governance as vg  # noqa: E402

CG = REPO / '_专题_技能合集策划' / 'change-governance.md'
assert CG.exists(), f'治理面未找到：{CG}'
PREV, HERE = 'CG-20260926-004', 'CG-20260926-005'
OLD_HEAD_ANCHOR = f'> **最后更新**：2026-09-26，{PREV}（'
DEMOTED_ANCHOR = f'> **此前更新（历史快照）**：2026-09-26，{PREV}（'

NEW_HEAD = (
    '> **最后更新**：2026-09-26，CG-20260926-005（**B 级**，冻结机制修订线第二步＝落判据，闭合 PL-049）：'
    '按上一批提案 R1—R5 新建 `_专题_技能合集策划/行为与专业证据层冻结基准_v4.md`，v3 冻结态留档不改写。'
    '核心＝原恒真的硬项 H-1 拆两枚：**H-1a**（冻结时点指纹，基线由 `08069b0` 推进到 `36dee02`，'
    '新登记值 `751164809b54e4ab98de38cf6e0b316fcea4220b78eb918f2b76513c5410d5ac`、72 件＝62 技能目录件＋8 `shared/`＋2 根治理件）'
    '＋**H-1b**（实跑时点指纹，**不钉固定值**、键集与字节同源取 `~/.qoder/skills/` 现读）；'
    '新立 §二 2A-补 五步差异归类规程（三态分层→技能目录机械判据→治理层逐件落判→基线表完备性双向互查→触发口径），'
    '取法列补入「脚本版本亦属取物基准」，机器本地件排除由文件名硬列改 `git check-ignore` 结构判据'
    '（实测与旧口径**集等价**、对本枚读数为 no-op）；另把 §4.3 第 8 条的基准版本枚举由「v1／v2／v3」扩为含 v4'
    '（不扩则该条按字面无法指挥实跑标注本版）。**落地偏差两处（据实登记，非照抄提案）**＝'
    '① **R1 原话「不动既有复算基」未照搬**——H-1a 基线推进到 `36dee02`；照旧基则新键集下 `shared/data-classification.md`'
    '无 blob 而 v4 禁跳过，复算必中断（本批自证 N2a），即照搬 R1 字面则 R1 与 R2／R4 不能同时成立；'
    '旧基读数 `413ab919…` 随 v3 文件留档**不改写**，仅自 v4 起不再作当前冻结读数。'
    '② **R3 的判据无机械取法，换实现而非换结论**——提案原文在档位归属上与本表一致（它已把 `change-governance.md`'
    '豁免为登记面），偏差不在归属，而在「是否被宿主技能加载器读入并影响输出」无可机算取法；唯一可算的代理量'
    '「被技能件引用」实测亦不成立（该件在 15 技能目录内命中 13 处，含 1 处 `#` 注释行与 4 处表格内流程指引行），'
    '故落地为两级判据＋逐件引用命中行原文落判＋基线表完备性双向互查。**落地时序凭据（本规程首个生效实例）**＝'
    '登记面写入前两枚逐字相等（差异 0 件、blob 缺失 0 件、键集差 0 件）；本行写入并三层带平后 H-1b 漂 1 件'
    '＝`shared/change-governance.md`，按规程第 3 步落**登记面**并归因本批、不触发重新冻结——'
    '「抓到被测对象已变」与「不把纯登记变化误当技术行为变化」两条验收关切在同一次实跑里同时成立。'
    '**§二 第 3 步复核**＝线内只读独立复算（自实现配方、不复用本批凭据脚本）六项全 PASS：两枚逐字命中登记值、'
    '自设六注入全被捕获、独立切六节 sha256 与本批读数全对、判 R3 订正为必要非扩面；其指出三处文字勘误'
    '（第 1 步「必属行为面」与第 4 步「不得默认任一档」冲突、「5 处表格内」逐行实为 4 处、本条未自报基线推进）'
    '已随批修入终稿。九项负向注入全 PASS。未改节全等性由分节 sha256 自证（§一／§三／§4.1—§4.2／§4.3 第 1—7 条／'
    '§4.4／§五 逐字全等，其中 §三／§4.1+§4.2／§4.4 三节值与 v3 §七 登记值一致）。复算凭据固化至 '
    '`程序文件/脚本/cg20260926_005_h1_recompute.py`（承上一批记录 §七「若获批须固化」要求），'
    '并把归类基线表改为**从 v4 现读**、不在脚本里手抄。'
    '§九 CG 行 148→**149**；台账 **82 行不变**、**PL-049 转已闭合**（待处置 20→19／已闭合 61→62）。'
    '历史快照保留如下，终态以本批执行记录为准。\n>\n'
)

CG_ROW = (
    f'| {HERE} | 2026-09-26 | '
    '**B 级**（定级依据＝§一 B 级「新增内容、不影响安全性」直接命中——写面为新建判据载体 v4 并恢复一枚恒真硬项的检测力，'
    '属影响行为比较口径的实质变更，**不采 C 级**（C 级定义＝不影响功能与准确性的排版类变更，本批改了取物与归类判据）；'
    '**不升 A**＝零改标准数值与限值、零改 `shared/` 契约与索引本体、零改 15 技能目录内容件、零改校验器与十二门禁判据。'
    '先例＝同件 v1／v2／v3 均定 B 级（CG-20260921-003／-004／-008），且上一批 CG-20260926-004 记录 §一 第 4 条已预判'
    '「基准件的实质修订属 B 级、须走 §二 四步并留前版」。授权字面＝发起人 2026-09-26「评估，并推进」，'
    '系对该批收尾句「允许按记录 §四 的 R1—R5 落地冻结基准 v4，B 级，走 §二 四步并保留 v3 前版」的当轮批复） | '
    '① 落地内容＝执行 CG-20260926-004 记录 §四 的 R1—R5：R1 H-1 拆 H-1a／H-1b（旧版留档不删）；R2 H-1b 键集与字节同源同时点；'
    'R3 差异按行为面／登记面归类并定触发口径；R4 脚本版本入取物基准；R5 机器本地件排除改结构判据。'
    '② **落地偏差两处（据实登记）**＝(a) R1 的「不动既有复算基」未照搬，H-1a 冻结基由 `08069b0` 推进到 `36dee02`——'
    '照旧基则新键集下 `shared/data-classification.md` 无 blob 而 v4 禁跳过、复算必中断，即 R1 字面与 R2／R4 不能同时成立；'
    '(b) R3 的判据「是否被宿主读入并影响输出」无可机算取法（提案在档位归属上与本表一致、已豁免 `change-governance.md` 为登记面），'
    '唯一可算代理「被技能件引用」实测不成立（该件命中 13 处含 1 注释行与 4 表格内指引行），故换实现不换结论。'
    '③ 新基线与件集＝冻结基 `36dee02`，键集 73 ∖ 结构判据命中 1 件＝72 件参与聚合（62 技能目录＋8 `shared/`＋2 根治理件），'
    '登记值 `751164809b54e4ab98de38cf6e0b316fcea4220b78eb918f2b76513c5410d5ac`；v3 的 `413ab919…` 随 v3 文件留档不改写、'
    '自 v4 起不得再引为当前冻结读数。④ 全等性自证＝§二 为唯一重写面（另 §4.3 第 8 条仅版本枚举扩写、§六 第 6 条加 v4 注），'
    '§一／§三／§4.1—§4.2／§4.3 第 1—7 条／§4.4／§五 六节两版逐字全等（§三 `9f9a4c7f347d575a…`、§4.1+§4.2 '
    '`27a8aa63235928bc…`、§4.4 `44cd4b710d3316f2…` 三节值与 v3 §七 登记值一致，构成切片口径正确与内容未变的双重证明）。'
    '⑤ 负向注入九项全 PASS（凭据脚本 `--selftest`）＝N1 错取脚本版本产他值 `62fb5e99…`；N2a 跨版本混取时如实中断、'
    'N2b 同参数改跳过即吞 1 件仍与 v3 登记值逐字相等（证跳过是漏检而非无害）；N3a H-1b 字节侧改回 blob 即与 H-1a 恒等、'
    'N3b 取运行时现字节报漂移 36 件＋新增 1 件；N4a 结构判据与文件名硬列**集等价**、N4b 排除面多吞一件即产他值 `3d4f3b29…`；'
    'N5 基线表删一行即报未列件；N6 命中 13 处仍落登记面。⑥ **§二 第 3 步复核**＝线内只读独立复算六项全 PASS'
    '（自实现两枚配方逐字命中、自设六注入全被捕获、独立切六节 sha256 与本批全对、判 R3 订正为必要非扩面），'
    '其指出三处文字勘误已随批修入终稿；§4.3 第 8 条枚举缺口由主代理在复核等待期自查发现、复核批未列出，据实登记。'
    '⑦ 复算凭据固化＝把上一批记录 §七 披露的「未固化为仓内脚本的 stdin 内联复算」落 `程序文件/脚本/`，'
    '并顺手把该记录未单独分出的「新增件」一态显式分出（其值 D 把 `shared/data-classification.md` 跳过，正是 v4 规程所禁） | '
    '影响范围＝`_专题_技能合集策划/行为与专业证据层冻结基准_v4.md`（新建）＋`程序文件/脚本/cg20260926_005_build_baseline_v4.py`'
    '（新建）＋`程序文件/脚本/cg20260926_005_h1_recompute.py`（新建）＋`程序文件/脚本/cg20260926_005_governance_patch.py`（新建）'
    '＋`记录/2026-09-26_CG-20260926-005_冻结基准v4落地执行记录.md`（新建）＋`CHANGELOG.md`'
    '＋`成果/2026-09-25_项目全面审视与下一阶段执行方案.md` §五 更新表「冻结机制必要修订」行（状态转已闭合，防下轮误读为未启动）'
    '＋`文档/专业整改任务总单_v1.md` §三 PL-049 条状态注（原文不改写）＋本文件登记面与 §11.2 台账 PL-049 一行；'
    '基准件与记录件均不在检查 10 扫描面（该面不含 `_专题_技能合集策划/` 与 `记录/`，本批现读清单内两者命中 0 单元），'
    '故新件不触发登记，仅治理镜像面因本文件指纹再漂须按列判 N 重登。'
    '零改面＝`行为与专业证据层冻结基准_v1/v2/v3.md`（前版冻结态）、15 技能目录全部内容件、契约／红线／索引／分类判据本体、'
    '校验器与十二门禁判据、§九 历史 CG 行、§11.2 台账除 PL-049 外全部 81 行、`素材/` | '
    '已发布（发起人当轮批复；B 级 §二 第 3 步复核＝线内只读独立复算批，读数见本批执行记录 §四）；'
    '§九 CG 行 148→**149**、台账 **82 行不变**、状态分布 待处置 20→**19**／已闭合 61→**62**／已裁定不做 1 不变；'
    '写面与验收读数以 记录/2026-09-26_CG-20260926-005_冻结基准v4落地执行记录.md 为准；'
    'commit 随本批（T1），push 不随批（T2，须发起人当轮明文整句） |\n'
)

PL_ID = 'PL-049'
PL_CLOSE = ('**CG-20260926-005 闭合**＝本行原述的「反向后果＝H-1 恒为同值、不再反映实跑时宿主真正加载的技能内容」'
            '由 CG-20260926-004 做成三值实测、由本批按 R1—R5 落地为基准 v4：H-1 拆 H-1a（冻结时点，基线推进到 `36dee02`）'
            '＋H-1b（实跑时点，键集与字节同源取运行时现读、不钉固定值），新立 §二 2A-补 五步差异归类规程，'
            '把「抓到被测对象已变」与「不把纯登记变化误当技术行为变化」两条同时闭合。'
            '闭合凭据＝登记面写入前两枚逐字相等（差异 0 件）、写入带平后 H-1b 漂 1 件且该件按规程落登记面并归因本批'
            '（规程首个生效实例）、九项负向注入全 PASS、线内只读独立复核六项全 PASS。'
            '本行事项列原述与来源登记按快照纪律**不改写**。')


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
        print(f'本批 §九 行列数 {len(vg.md_cells(body))} ≠ 表头 {ncol}，停')
        return 1
    lines.insert(idx[0] + 1, body)

    # ── §11.2 台账 PL-049 转已闭合 ──
    pl = [i for i, l in enumerate(lines) if l.startswith(f'| {PL_ID} | ')]
    if len(pl) != 1:
        print(f'台账 {PL_ID} 行命中 {len(pl)}，停')
        return 1
    row = lines[pl[0]]
    cells = vg.md_cells(row)
    if len(cells) != 7:
        print(f'台账 {PL_ID} 行列数 {len(cells)} ≠ 表头 7，停')
        return 1
    if cells[5].strip() != '待处置':
        print(f'台账 {PL_ID} 状态列现值「{cells[5].strip()}」非「待处置」，停（不覆盖他批改动）')
        return 1
    if row.count('| 待处置 |') != 1 or not row.rstrip().endswith('|'):
        print('台账状态列锚非唯一或行尾缺竖线，停')
        return 1
    new_row = row.replace('| 待处置 |', '| **已闭合** |', 1)
    new_row = new_row.rstrip()[:-1].rstrip() + ' ' + PL_CLOSE + ' |'
    if len(vg.md_cells(new_row)) != 7:
        print(f'改写后 {PL_ID} 行列数 {len(vg.md_cells(new_row))} ≠ 7，回退不写')
        return 1
    lines[pl[0]] = new_row
    out = '\n'.join(lines)

    CG.write_bytes(out.encode('utf-8'))
    check = CG.read_bytes().decode('utf-8')
    now = [l for l in check.split('\n') if l.startswith(f'| {HERE} | ')]
    pl2 = [l for l in check.split('\n') if l.startswith(f'| {PL_ID} | ')]
    from collections import Counter
    dist = Counter(vg.md_cells(l)[5].replace('*', '').strip()
                   for l in check.split('\n') if l.startswith('| PL-') and len(vg.md_cells(l)) == 7)
    print('写入完成：')
    print(f'  头部新行存在＝{f"> **最后更新**：2026-09-26，{HERE}（" in check}')
    print(f'  旧行已降级且唯一＝{check.count(DEMOTED_ANCHOR) == 1}')
    print(f'  §九 新行唯一＝{len(now) == 1}｜列数＝{len(vg.md_cells(now[0]))}（表头 {ncol}）'
          f'｜收尾竖线在位＝{now[0].rstrip().endswith("|")}')
    print(f'  台账 {PL_ID} 唯一＝{len(pl2) == 1}｜列数＝{len(vg.md_cells(pl2[0]))}（原 7）'
          f'｜状态列＝{vg.md_cells(pl2[0])[5].strip()}｜闭合凭据在位＝{"CG-20260926-005 闭合" in pl2[0]}')
    print(f'  台账行数＝{sum(1 for l in check.split(chr(10)) if l.startswith("| PL-"))}'
          f'｜状态分布＝{dict(dist)}')
    print(f'  §九 CG 行数＝{sum(1 for l in check.split(chr(10)) if l.startswith("| CG-"))}（预期 149）')
    print(f'  行数 {lf_before} → {check.count(chr(10))}（预期 +3＝头部两物理行＋§九 一行，台账行为原地改写）')
    print(f'  CR 计数 {cr_before} → {check.count(chr(13))}（预期不变 0）')
    print(f'  字节 {len(raw)} → {len(out.encode("utf-8"))}')
    return 0


sys.exit(main())
